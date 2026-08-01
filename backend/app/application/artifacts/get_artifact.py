from app.application.artifacts.errors import ArtifactNotFoundError
from app.application.artifacts.unit_of_work import ArtifactUnitOfWorkFactory
from app.domain.artifacts.model import Artifact


class GetArtifactUseCase:
    def __init__(self, uow_factory: ArtifactUnitOfWorkFactory):
        self._uow_factory = uow_factory

    def execute(self, artifact_id: str) -> Artifact:
        with self._uow_factory() as uow:
            artifact = uow.artifacts.get(artifact_id)
        if artifact is None:
            raise ArtifactNotFoundError(artifact_id)
        return artifact
