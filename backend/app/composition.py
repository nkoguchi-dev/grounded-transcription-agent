import time

from app.application.jobs.create_job_use_case import CreateJobUseCase
from app.application.jobs.execute_dummy_job_use_case import ExecuteDummyJobUseCase
from app.application.jobs.get_job_use_case import GetJobUseCase
from app.infrastructure.database import SqlAlchemyJobUnitOfWork
from app.presentation.celery_app import celery
from app.presentation.celery_publisher import CeleryJobPublisher


def build_create_job_use_case() -> CreateJobUseCase:
    return CreateJobUseCase(SqlAlchemyJobUnitOfWork, CeleryJobPublisher(celery))


def build_get_job_use_case() -> GetJobUseCase:
    return GetJobUseCase(SqlAlchemyJobUnitOfWork)


def build_execute_dummy_job_use_case() -> ExecuteDummyJobUseCase:
    return ExecuteDummyJobUseCase(SqlAlchemyJobUnitOfWork, time.sleep)
