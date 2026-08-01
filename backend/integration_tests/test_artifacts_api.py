from collections.abc import Generator
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session, sessionmaker

from app.application.artifacts.object_storage import PresignedUrl, StoredObject
from app.application.artifacts.unit_of_work import ArtifactUnitOfWorkFactory
from app.application.unit_of_work import JobUnitOfWorkFactory
from app.composition import create_application
from app.domain.artifacts.model import Artifact
from app.infrastructure.artifacts import ArtifactRecord


class UnusedJobPublisher:
    def publish(self, job_id: str) -> str:
        raise AssertionError("job publisher must not be used by artifact tests")


@dataclass
class FakeObjectStorage:
    objects: dict[str, StoredObject] = field(default_factory=dict)
    upload_keys: list[str] = field(default_factory=list)

    def create_upload_url(self, object_key: str, content_type: str) -> PresignedUrl:
        self.upload_keys.append(object_key)
        return PresignedUrl(
            f"http://localhost:9002/bucket/{object_key}?upload=1",
            datetime.now(timezone.utc) + timedelta(minutes=15),
        )

    def get_object_info(self, object_key: str) -> StoredObject | None:
        return self.objects.get(object_key)

    def create_download_url(self, object_key: str) -> PresignedUrl:
        return PresignedUrl(
            f"http://localhost:9002/bucket/{object_key}?download=1",
            datetime.now(timezone.utc) + timedelta(minutes=15),
        )


@pytest.fixture
def storage() -> FakeObjectStorage:
    return FakeObjectStorage()


@pytest.fixture
def client(
    uow_factory: JobUnitOfWorkFactory,
    artifact_uow_factory: ArtifactUnitOfWorkFactory,
    storage: FakeObjectStorage,
) -> Generator[TestClient]:
    app = create_application(
        uow_factory=uow_factory,
        publisher=UnusedJobPublisher(),
        artifact_uow_factory=artifact_uow_factory,
        object_storage=storage,
    )
    with TestClient(app) as test_client:
        yield test_client


def persist_artifact(
    database_session_factory: sessionmaker[Session], artifact: Artifact
) -> None:
    values = artifact.__dict__ | {"status": artifact.status.value}
    with database_session_factory() as session:
        session.add(ArtifactRecord(**values))
        session.commit()


def test_start_upload_persists_pending_artifact(
    client: TestClient,
    storage: FakeObjectStorage,
    database_session_factory: sessionmaker[Session],
) -> None:
    response = client.post(
        "/api/artifacts/uploads",
        json={"content_type": "text/plain", "expected_size": 5},
    )

    assert response.status_code == 201
    started = response.json()
    artifact_id = started["artifact_id"]
    assert started["status"] == "pending"
    assert started["upload_url"].startswith("http://localhost:9002/")
    assert len(storage.upload_keys) == 1

    with database_session_factory() as session:
        persisted = session.get(ArtifactRecord, artifact_id)
    assert persisted is not None
    assert persisted.status == "pending"
    assert persisted.object_key == storage.upload_keys[0]
    assert persisted.content_type == "text/plain"
    assert persisted.expected_size == 5


def test_complete_upload_persists_ready_metadata(
    client: TestClient,
    storage: FakeObjectStorage,
    database_session_factory: sessionmaker[Session],
) -> None:
    artifact = Artifact.create("text/plain", 5)
    persist_artifact(database_session_factory, artifact)
    storage.objects[artifact.object_key] = StoredObject(5, "text/plain")

    response = client.post(f"/api/artifacts/{artifact.id}/complete")

    assert response.status_code == 200
    assert response.json()["status"] == "ready"
    assert response.json()["actual_size"] == 5
    with database_session_factory() as session:
        persisted = session.get(ArtifactRecord, artifact.id)
    assert persisted is not None
    assert persisted.status == "ready"
    assert persisted.actual_size == 5
    assert persisted.completed_at is not None


def test_completing_ready_artifact_is_idempotent(
    client: TestClient,
    database_session_factory: sessionmaker[Session],
) -> None:
    artifact = Artifact.create("text/plain", 5).complete(5)
    persist_artifact(database_session_factory, artifact)

    response = client.post(f"/api/artifacts/{artifact.id}/complete")

    assert response.status_code == 200
    assert response.json()["status"] == "ready"
    assert response.json()["actual_size"] == 5
    assert (
        datetime.fromisoformat(response.json()["completed_at"]) == artifact.completed_at
    )


def test_get_artifact_returns_persisted_metadata(
    client: TestClient,
    database_session_factory: sessionmaker[Session],
) -> None:
    artifact = Artifact.create("text/plain", 5).complete(5)
    persist_artifact(database_session_factory, artifact)

    response = client.get(f"/api/artifacts/{artifact.id}")

    assert response.status_code == 200
    body = response.json()
    assert {
        key: body[key]
        for key in (
            "id",
            "status",
            "content_type",
            "expected_size",
            "actual_size",
        )
    } == {
        "id": artifact.id,
        "status": "ready",
        "content_type": "text/plain",
        "expected_size": 5,
        "actual_size": 5,
    }
    assert datetime.fromisoformat(body["created_at"]) == artifact.created_at
    assert datetime.fromisoformat(body["completed_at"]) == artifact.completed_at


def test_ready_artifact_returns_download_url(
    client: TestClient,
    database_session_factory: sessionmaker[Session],
) -> None:
    artifact = Artifact.create("text/plain", 5).complete(5)
    persist_artifact(database_session_factory, artifact)

    response = client.post(f"/api/artifacts/{artifact.id}/download-url")

    assert response.status_code == 200
    assert response.json()["download_url"].endswith("?download=1")


def test_missing_uploaded_object_keeps_artifact_pending(
    client: TestClient, database_session_factory: sessionmaker[Session]
) -> None:
    artifact = Artifact.create("application/octet-stream", 8)
    persist_artifact(database_session_factory, artifact)

    response = client.post(f"/api/artifacts/{artifact.id}/complete")

    assert response.status_code == 409
    assert response.json() == {"detail": "Uploaded object not found"}
    with database_session_factory() as session:
        persisted = session.get(ArtifactRecord, artifact.id)
    assert persisted is not None
    assert persisted.status == "pending"
    assert persisted.actual_size is None


def test_pending_artifact_download_is_rejected(
    client: TestClient,
    database_session_factory: sessionmaker[Session],
) -> None:
    artifact = Artifact.create("text/plain", 1)
    persist_artifact(database_session_factory, artifact)

    response = client.post(f"/api/artifacts/{artifact.id}/download-url")

    assert response.status_code == 409
    assert response.json() == {"detail": "Artifact is not ready"}
