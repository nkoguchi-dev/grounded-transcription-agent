from app.application.artifacts.errors import (
    ArtifactNotFoundError,
    ArtifactNotReadyError,
)
from app.application.artifacts.object_storage import ObjectStorage, PresignedUrl
from app.application.artifacts.unit_of_work import ArtifactUnitOfWorkFactory
from app.domain.artifacts.model import ArtifactStatus


class CreateDownloadUrlUseCase:
    def __init__(self, uow_factory: ArtifactUnitOfWorkFactory, storage: ObjectStorage):
        self._uow_factory = uow_factory
        self._storage = storage

    def execute(self, artifact_id: str) -> PresignedUrl:
        with self._uow_factory() as uow:
            artifact = uow.artifacts.get(artifact_id)
        if artifact is None:
            raise ArtifactNotFoundError(artifact_id)
        if artifact.status is not ArtifactStatus.READY:
            raise ArtifactNotReadyError(artifact_id)
        return self._storage.create_download_url(artifact.object_key)
