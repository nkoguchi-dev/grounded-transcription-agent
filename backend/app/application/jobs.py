from collections.abc import Callable
from dataclasses import dataclass

from app.application.job_publisher import JobPublisher
from app.application.unit_of_work import JobUnitOfWorkFactory
from app.domain.jobs.model import Job, JobStatus


@dataclass(frozen=True)
class CreateJobInput:
    duration_seconds: int
    should_fail: bool


class CreateJobUseCase:
    def __init__(
        self, uow_factory: JobUnitOfWorkFactory, job_publisher: JobPublisher
    ) -> None:
        self._uow_factory = uow_factory
        self._job_publisher = job_publisher

    def execute(self, input_data: CreateJobInput) -> Job:
        job = Job.create(input_data.duration_seconds, input_data.should_fail)
        with self._uow_factory() as uow:
            uow.jobs.create(job)
            uow.commit()
        return job

    def dispatch(self, job: Job) -> Job:
        task_id = self._job_publisher.publish(job.id)
        with self._uow_factory() as uow:
            uow.jobs.set_task_id(job.id, task_id)
            uow.commit()
        return job.with_task_id(task_id)


class GetJobUseCase:
    def __init__(self, uow_factory: JobUnitOfWorkFactory) -> None:
        self._uow_factory = uow_factory

    def execute(self, job_id: str) -> Job | None:
        with self._uow_factory() as uow:
            return uow.jobs.get(job_id)


class ExecuteDummyJobUseCase:
    def __init__(
        self, uow_factory: JobUnitOfWorkFactory, sleep: Callable[[float], None]
    ) -> None:
        self._uow_factory = uow_factory
        self._sleep = sleep

    def execute(self, job_id: str) -> None:
        job = self._start(job_id)
        if job is None:
            return
        try:
            self._sleep(job.duration_seconds)
            if job.should_fail:
                raise RuntimeError("Dummy job was configured to fail")
            self._succeed(job_id)
        except Exception as error:
            self._fail(job_id, str(error))
            raise

    def _start(self, job_id: str) -> Job | None:
        with self._uow_factory() as uow:
            job = uow.jobs.get(job_id)
            if job is None or job.status is not JobStatus.QUEUED:
                return None
            started_job = job.start()
            uow.jobs.update(started_job)
            uow.commit()
            return started_job

    def _succeed(self, job_id: str) -> None:
        with self._uow_factory() as uow:
            job = uow.jobs.get(job_id)
            if job is None or job.status is not JobStatus.RUNNING:
                return
            uow.jobs.update(job.succeed({"message": "Dummy job completed"}))
            uow.commit()

    def _fail(self, job_id: str, error_message: str) -> None:
        with self._uow_factory() as uow:
            job = uow.jobs.get(job_id)
            if job is None or job.status is not JobStatus.RUNNING:
                return
            uow.jobs.update(job.fail(error_message))
            uow.commit()
