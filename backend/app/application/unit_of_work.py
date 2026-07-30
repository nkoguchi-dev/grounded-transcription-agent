from collections.abc import Callable
from types import TracebackType
from typing import Protocol, Self

from app.domain.jobs.job_repository import JobRepository


class JobUnitOfWork(Protocol):
    @property
    def jobs(self) -> JobRepository: ...

    def __enter__(self) -> Self: ...

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None: ...

    def commit(self) -> None: ...
    def rollback(self) -> None: ...


JobUnitOfWorkFactory = Callable[[], JobUnitOfWork]
