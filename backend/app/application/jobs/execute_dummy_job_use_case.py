from collections.abc import Callable

from app.application.unit_of_work import JobUnitOfWorkFactory
from app.domain.jobs.model import Job, JobStatus


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
