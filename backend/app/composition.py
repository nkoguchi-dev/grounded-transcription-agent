import time

from app.application.jobs import (
    CreateJobUseCase,
    ExecuteDummyJobUseCase,
    GetJobUseCase,
)
from app.celery_app import celery
from app.infrastructure.database import SqlAlchemyJobUnitOfWork


def build_create_job_use_case() -> CreateJobUseCase:
    return CreateJobUseCase(SqlAlchemyJobUnitOfWork, celery)


def build_get_job_use_case() -> GetJobUseCase:
    return GetJobUseCase(SqlAlchemyJobUnitOfWork)


def build_execute_dummy_job_use_case() -> ExecuteDummyJobUseCase:
    return ExecuteDummyJobUseCase(SqlAlchemyJobUnitOfWork, time.sleep)
