from app.application.artifacts.errors import (
    ArtifactNotFoundError,
    ArtifactObjectNotFoundError,
)
from app.application.artifacts.object_storage import ObjectStorage
from app.application.artifacts.unit_of_work import ArtifactUnitOfWorkFactory
from app.domain.artifacts.model import Artifact, ArtifactStatus


class CompleteUploadUseCase:
    def __init__(self, uow_factory: ArtifactUnitOfWorkFactory, storage: ObjectStorage):
        self._uow_factory = uow_factory
        self._storage = storage

    def execute(self, artifact_id: str) -> Artifact:
        with self._uow_factory() as uow:
            artifact = uow.artifacts.get(artifact_id)
        if artifact is None:
            raise ArtifactNotFoundError(artifact_id)
        if artifact.status is ArtifactStatus.READY:
            return artifact

        # HEAD can block on an external service, so it must not hold a DB transaction.
        object_info = self._storage.get_object_info(artifact.object_key)
        if object_info is None:
            raise ArtifactObjectNotFoundError(artifact_id)

        completed = artifact.complete(object_info.size)
        with self._uow_factory() as uow:
            current = uow.artifacts.get(artifact_id)
            if current is None:
                raise ArtifactNotFoundError(artifact_id)
            if current.status is ArtifactStatus.READY:
                return current
            uow.artifacts.update(completed)
            uow.commit()
        return completed
