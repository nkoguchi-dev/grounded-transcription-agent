from dataclasses import dataclass

from celery import Celery

from app.domain.jobs.model import Job
from app.domain.jobs.repository import JobRepository


@dataclass(frozen=True)
class CreateJobInput:
    duration_seconds: int
    should_fail: bool


class CreateJobUseCase:
    def __init__(self, repository: JobRepository, celery: Celery) -> None:
        self._repository = repository
        self._celery = celery

    def execute(self, input_data: CreateJobInput) -> Job:
        job = Job.create(input_data.duration_seconds, input_data.should_fail)
        self._repository.create(job)
        return job

    def dispatch(self, job: Job) -> Job:
        task = self._celery.send_task("app.worker.execute_dummy_job", args=[job.id])
        updated = job.with_task_id(task.id)
        self._repository.update(updated)
        return updated


class GetJobUseCase:
    def __init__(self, repository: JobRepository) -> None:
        self._repository = repository

    def execute(self, job_id: str) -> Job | None:
        return self._repository.get(job_id)
