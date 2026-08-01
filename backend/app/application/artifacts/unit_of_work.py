from collections.abc import Callable
from types import TracebackType
from typing import Protocol, Self

from app.domain.artifacts.artifact_repository import ArtifactRepository


class ArtifactUnitOfWork(Protocol):
    @property
    def artifacts(self) -> ArtifactRepository: ...

    def __enter__(self) -> Self: ...

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None: ...

    def commit(self) -> None: ...


ArtifactUnitOfWorkFactory = Callable[[], ArtifactUnitOfWork]
