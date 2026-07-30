import pytest

from app.application.jobs.create_job_use_case import CreateJobInput, CreateJobUseCase
from app.application.jobs.execute_dummy_job_use_case import ExecuteDummyJobUseCase
from app.application.jobs.get_job_use_case import GetJobUseCase
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

    def set_task_id(self, job_id: str, task_id: str) -> None:
        job = self.get(job_id)
        if job is None:
            raise LookupError(job_id)
        self._jobs[job_id] = job.with_task_id(task_id)


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


class FakeJobPublisher:
    def __init__(self) -> None:
        self.published_job_ids: list[str] = []

    def publish(self, job_id: str) -> str:
        self.published_job_ids.append(job_id)
        return "task-123"


class CompletingJobPublisher(FakeJobPublisher):
    def __init__(self, jobs: dict[str, Job]) -> None:
        super().__init__()
        self._jobs = jobs

    def publish(self, job_id: str) -> str:
        task_id = super().publish(job_id)
        self._jobs[job_id] = self._jobs[job_id].start().succeed({"message": "done"})
        return task_id


def test_create_and_dispatch_job_use_independent_committed_transactions() -> None:
    uow_factory = InMemoryUnitOfWorkFactory()
    job_publisher = FakeJobPublisher()
    use_case = CreateJobUseCase(uow_factory, job_publisher)

    created = use_case.execute(CreateJobInput(duration_seconds=0, should_fail=False))
    dispatched = use_case.dispatch(created)

    assert dispatched.task_id == "task-123"
    assert job_publisher.published_job_ids == [created.id]
    assert [unit.commit_calls for unit in uow_factory.created_units] == [1, 1]


def test_dispatch_keeps_a_worker_state_transition_when_storing_task_id() -> None:
    uow_factory = InMemoryUnitOfWorkFactory()
    job_publisher = CompletingJobPublisher(uow_factory.jobs)
    use_case = CreateJobUseCase(uow_factory, job_publisher)
    created = use_case.execute(CreateJobInput(duration_seconds=0, should_fail=False))

    dispatched = use_case.dispatch(created)

    persisted = uow_factory.jobs[created.id]
    assert dispatched.task_id == "task-123"
    assert persisted.task_id == "task-123"
    assert persisted.status.value == "succeeded"


def test_dummy_worker_marks_failed_job_in_a_separate_transaction() -> None:
    uow_factory = InMemoryUnitOfWorkFactory()
    created = CreateJobUseCase(uow_factory, FakeJobPublisher()).execute(
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
