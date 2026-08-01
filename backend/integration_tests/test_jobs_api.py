from collections.abc import Generator
from dataclasses import dataclass, field
from datetime import datetime

import pytest
from fastapi.testclient import TestClient

from app.application.jobs.create_job_use_case import CreateJobUseCase
from app.application.jobs.get_job_use_case import GetJobUseCase
from app.application.unit_of_work import JobUnitOfWorkFactory
from app.domain.jobs.model import Job
from app.presentation.api.app import create_api


@dataclass
class RecordingJobPublisher:
    task_id: str = "task-123"
    error: Exception | None = None
    published_job_ids: list[str] = field(default_factory=list)

    def publish(self, job_id: str) -> str:
        self.published_job_ids.append(job_id)
        if self.error is not None:
            raise self.error
        return self.task_id


@pytest.fixture
def publisher() -> RecordingJobPublisher:
    return RecordingJobPublisher()


@pytest.fixture
def client(
    uow_factory: JobUnitOfWorkFactory,
    publisher: RecordingJobPublisher,
) -> Generator[TestClient]:
    app = create_api(
        CreateJobUseCase(uow_factory, publisher),
        GetJobUseCase(uow_factory),
    )
    with TestClient(app) as test_client:
        yield test_client


def test_create_job_persists_and_publishes_once(
    client: TestClient,
    uow_factory: JobUnitOfWorkFactory,
    publisher: RecordingJobPublisher,
) -> None:
    response = client.post(
        "/api/jobs", json={"duration_seconds": 0, "should_fail": False}
    )

    assert response.status_code == 202
    body = response.json()
    assert body["status"] == "queued"
    assert body["duration_seconds"] == 0
    assert body["should_fail"] is False
    assert body["result"] is None
    assert body["error_message"] is None
    assert publisher.published_job_ids == [body["id"]]

    persisted = GetJobUseCase(uow_factory).execute(body["id"])
    assert persisted is not None
    assert persisted.id == body["id"]
    assert persisted.status.value == "queued"
    assert persisted.task_id == publisher.task_id


def test_create_job_keeps_committed_job_when_publisher_fails(
    client: TestClient,
    uow_factory: JobUnitOfWorkFactory,
    publisher: RecordingJobPublisher,
) -> None:
    publisher.error = RuntimeError("broker unavailable")

    response = client.post(
        "/api/jobs", json={"duration_seconds": 1, "should_fail": True}
    )

    assert response.status_code == 503
    assert response.json() == {"detail": "Job broker is unavailable"}
    assert len(publisher.published_job_ids) == 1

    persisted = GetJobUseCase(uow_factory).execute(publisher.published_job_ids[0])
    assert persisted is not None
    assert persisted.status.value == "queued"
    assert persisted.duration_seconds == 1
    assert persisted.should_fail is True
    assert persisted.task_id is None


def test_get_job_returns_state_persisted_in_postgresql(
    client: TestClient,
    uow_factory: JobUnitOfWorkFactory,
) -> None:
    job = Job.create(duration_seconds=3, should_fail=True).with_task_id("existing-task")
    with uow_factory() as uow:
        uow.jobs.create(job)
        uow.commit()

    response = client.get(f"/api/jobs/{job.id}")

    assert response.status_code == 200
    body = response.json()
    assert body["id"] == job.id
    assert body["status"] == job.status.value
    assert body["duration_seconds"] == job.duration_seconds
    assert body["should_fail"] == job.should_fail
    assert body["result"] == job.result
    assert body["error_message"] == job.error_message
    assert datetime.fromisoformat(body["created_at"]) == job.created_at
    assert body["started_at"] is None
    assert body["finished_at"] is None


def test_get_job_returns_404_for_missing_job(client: TestClient) -> None:
    response = client.get("/api/jobs/missing")

    assert response.status_code == 404
    assert response.json() == {"detail": "Job not found"}
