from dataclasses import dataclass

from app.application.artifacts.object_storage import ObjectStorage, PresignedUrl
from app.application.artifacts.unit_of_work import ArtifactUnitOfWorkFactory
from app.domain.artifacts.model import Artifact


@dataclass(frozen=True)
class StartUploadInput:
    content_type: str
    expected_size: int


@dataclass(frozen=True)
class StartUploadOutput:
    artifact: Artifact
    upload: PresignedUrl


class StartUploadUseCase:
    def __init__(self, uow_factory: ArtifactUnitOfWorkFactory, storage: ObjectStorage):
        self._uow_factory = uow_factory
        self._storage = storage

    def execute(self, input_data: StartUploadInput) -> StartUploadOutput:
        artifact = Artifact.create(input_data.content_type, input_data.expected_size)
        with self._uow_factory() as uow:
            uow.artifacts.create(artifact)
            uow.commit()
        # URL generation is intentionally outside the database transaction.
        upload = self._storage.create_upload_url(
            artifact.object_key, artifact.content_type
        )
        return StartUploadOutput(artifact, upload)
