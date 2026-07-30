from dataclasses import dataclass

from app.application.job_publisher import JobPublisher
from app.application.unit_of_work import JobUnitOfWorkFactory
from app.domain.jobs.model import Job


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
