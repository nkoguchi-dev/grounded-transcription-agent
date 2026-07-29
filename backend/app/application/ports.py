from collections.abc import Callable
from types import TracebackType
from typing import Protocol, Self

from app.domain.jobs.model import Job


class JobRepository(Protocol):
    def create(self, job: Job) -> None: ...
    def get(self, job_id: str) -> Job | None: ...
    def update(self, job: Job) -> None: ...


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
