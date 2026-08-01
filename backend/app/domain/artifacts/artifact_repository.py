from typing import Protocol

from app.domain.artifacts.model import Artifact


class ArtifactRepository(Protocol):
    def create(self, artifact: Artifact) -> None: ...

    def get(self, artifact_id: str) -> Artifact | None: ...

    def update(self, artifact: Artifact) -> None: ...
