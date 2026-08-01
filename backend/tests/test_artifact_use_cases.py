from datetime import datetime, timedelta, timezone

import pytest

from app.application.artifacts.complete_upload import CompleteUploadUseCase
from app.application.artifacts.create_download_url import CreateDownloadUrlUseCase
from app.application.artifacts.errors import (
    ArtifactNotReadyError,
    ArtifactObjectNotFoundError,
)
from app.application.artifacts.object_storage import PresignedUrl, StoredObject
from app.application.artifacts.start_upload import StartUploadInput, StartUploadUseCase
from app.domain.artifacts.model import Artifact, ArtifactStatus


class MemoryArtifactRepository:
    def __init__(self, records: dict[str, Artifact]) -> None:
        self._records = records

    def create(self, artifact: Artifact) -> None:
        self._records[artifact.id] = artifact

    def get(self, artifact_id: str) -> Artifact | None:
        return self._records.get(artifact_id)

    def update(self, artifact: Artifact) -> None:
        self._records[artifact.id] = artifact


class MemoryArtifactUnitOfWork:
    def __init__(self, records: dict[str, Artifact]) -> None:
        self.artifacts = MemoryArtifactRepository(records)

    def __enter__(self) -> "MemoryArtifactUnitOfWork":
        return self

    def __exit__(self, *_: object) -> None:
        pass

    def commit(self) -> None:
        pass


class FakeObjectStorage:
    def __init__(self) -> None:
        self.objects: dict[str, StoredObject] = {}
        self.upload_keys: list[str] = []

    def create_upload_url(self, object_key: str, content_type: str) -> PresignedUrl:
        self.upload_keys.append(object_key)
        return PresignedUrl(
            f"http://public/{object_key}",
            datetime.now(timezone.utc) + timedelta(minutes=15),
        )

    def get_object_info(self, object_key: str) -> StoredObject | None:
        return self.objects.get(object_key)

    def create_download_url(self, object_key: str) -> PresignedUrl:
        return PresignedUrl(
            f"http://public/{object_key}?download=1",
            datetime.now(timezone.utc) + timedelta(minutes=15),
        )


def test_start_complete_and_download_flow() -> None:
    records: dict[str, Artifact] = {}
    storage = FakeObjectStorage()

    def factory() -> MemoryArtifactUnitOfWork:
        return MemoryArtifactUnitOfWork(records)

    started = StartUploadUseCase(factory, storage).execute(
        StartUploadInput("text/plain", 5)
    )
    assert records[started.artifact.id].status is ArtifactStatus.PENDING
    assert storage.upload_keys == [started.artifact.object_key]

    storage.objects[started.artifact.object_key] = StoredObject(5, "text/plain")
    completed = CompleteUploadUseCase(factory, storage).execute(started.artifact.id)
    repeated = CompleteUploadUseCase(factory, storage).execute(started.artifact.id)
    download = CreateDownloadUrlUseCase(factory, storage).execute(started.artifact.id)

    assert completed.status is ArtifactStatus.READY
    assert completed.actual_size == 5
    assert repeated == completed
    assert download.url.endswith("?download=1")


def test_complete_does_not_change_pending_artifact_when_object_is_missing() -> None:
    artifact = Artifact.create("text/plain", 5)
    records = {artifact.id: artifact}
    storage = FakeObjectStorage()

    def factory() -> MemoryArtifactUnitOfWork:
        return MemoryArtifactUnitOfWork(records)

    with pytest.raises(ArtifactObjectNotFoundError):
        CompleteUploadUseCase(factory, storage).execute(artifact.id)

    assert records[artifact.id].status is ArtifactStatus.PENDING


def test_pending_artifact_has_no_download_url() -> None:
    artifact = Artifact.create("text/plain", 5)
    records = {artifact.id: artifact}

    with pytest.raises(ArtifactNotReadyError):
        CreateDownloadUrlUseCase(
            lambda: MemoryArtifactUnitOfWork(records), FakeObjectStorage()
        ).execute(artifact.id)
