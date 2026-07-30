from app.application.unit_of_work import JobUnitOfWorkFactory
from app.domain.jobs.model import Job


class GetJobUseCase:
    def __init__(self, uow_factory: JobUnitOfWorkFactory) -> None:
        self._uow_factory = uow_factory

    def execute(self, job_id: str) -> Job | None:
        with self._uow_factory() as uow:
            return uow.jobs.get(job_id)
