from dataclasses import dataclass
from typing import cast

import pytest
from celery import Celery

from app.application.jobs import (
    CreateJobInput,
    CreateJobUseCase,
    ExecuteDummyJobUseCase,
    GetJobUseCase,
)
from app.domain.jobs.model import Job


class InMemoryJobRepository:
    def __init__(self, jobs: dict[str, Job]) -> None:
        self._jobs = jobs

    def create(self, job: Job) -> None:
        self._jobs[job.id] = job

    def get(self, job_id: str) -> Job | None:
        return self._jobs.get(job_id)

    def update(self, job: Job) -> None:
        if job.id not in self._jobs:
            raise LookupError(job.id)
        self._jobs[job.id] = job


class InMemoryUnitOfWork:
    def __init__(self, jobs: dict[str, Job]) -> None:
        self.jobs = InMemoryJobRepository(jobs)
        self.commit_calls = 0
        self.rollback_calls = 0

    def __enter__(self) -> "InMemoryUnitOfWork":
        return self

    def __exit__(self, exc_type: object, *_: object) -> None:
        if exc_type is not None:
            self.rollback()

    def commit(self) -> None:
        self.commit_calls += 1

    def rollback(self) -> None:
        self.rollback_calls += 1


class InMemoryUnitOfWorkFactory:
    def __init__(self) -> None:
        self.jobs: dict[str, Job] = {}
        self.created_units: list[InMemoryUnitOfWork] = []

    def __call__(self) -> InMemoryUnitOfWork:
        unit = InMemoryUnitOfWork(self.jobs)
        self.created_units.append(unit)
        return unit


@dataclass
class FakeTask:
    id: str


class FakeCelery:
    def send_task(self, *_: object, **__: object) -> FakeTask:
        return FakeTask(id="task-123")


def test_create_and_dispatch_job_use_independent_committed_transactions() -> None:
    uow_factory = InMemoryUnitOfWorkFactory()
    use_case = CreateJobUseCase(uow_factory, cast(Celery, FakeCelery()))

    created = use_case.execute(CreateJobInput(duration_seconds=0, should_fail=False))
    dispatched = use_case.dispatch(created)

    assert dispatched.celery_task_id == "task-123"
    assert [unit.commit_calls for unit in uow_factory.created_units] == [1, 1]


def test_dummy_worker_marks_failed_job_in_a_separate_transaction() -> None:
    uow_factory = InMemoryUnitOfWorkFactory()
    created = CreateJobUseCase(uow_factory, cast(Celery, FakeCelery())).execute(
        CreateJobInput(duration_seconds=0, should_fail=True)
    )
    worker_use_case = ExecuteDummyJobUseCase(uow_factory, lambda _: None)

    with pytest.raises(RuntimeError, match="configured to fail"):
        worker_use_case.execute(created.id)

    job = GetJobUseCase(uow_factory).execute(created.id)
    assert job is not None
    assert job.status.value == "failed"
    assert job.error_message == "Dummy job was configured to fail"
    assert [unit.commit_calls for unit in uow_factory.created_units] == [1, 1, 1, 0]
