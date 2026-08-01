import os
import time

from fastapi import FastAPI

from app.application.job_publisher import JobPublisher
from app.application.jobs.create_job_use_case import CreateJobUseCase
from app.application.jobs.execute_dummy_job_use_case import ExecuteDummyJobUseCase
from app.application.jobs.get_job_use_case import GetJobUseCase
from app.application.unit_of_work import JobUnitOfWorkFactory
from app.infrastructure.database import create_sqlalchemy_job_uow_factory
from app.presentation.api.app import create_api


def build_create_job_use_case(
    uow_factory: JobUnitOfWorkFactory | None = None,
    publisher: JobPublisher | None = None,
) -> CreateJobUseCase:
    # Concrete infrastructure is wired only here so application use cases remain
    # independent from SQLAlchemy and Celery.
    resolved_publisher = publisher
    if resolved_publisher is None:
        # Keep Celery configuration lazy so alternate publisher boundaries do not
        # require a broker merely to import or compose the application.
        from app.presentation.celery_app import celery
        from app.presentation.celery_publisher import CeleryJobPublisher

        resolved_publisher = CeleryJobPublisher(celery)
    return CreateJobUseCase(
        uow_factory if uow_factory is not None else build_job_uow_factory(),
        resolved_publisher,
    )


def build_get_job_use_case(
    uow_factory: JobUnitOfWorkFactory | None = None,
) -> GetJobUseCase:
    return GetJobUseCase(
        uow_factory if uow_factory is not None else build_job_uow_factory()
    )


def build_job_uow_factory() -> JobUnitOfWorkFactory:
    return create_sqlalchemy_job_uow_factory(os.environ["DATABASE_URL"])


def create_application(
    *,
    uow_factory: JobUnitOfWorkFactory | None = None,
    publisher: JobPublisher | None = None,
) -> FastAPI:
    resolved_uow_factory = (
        uow_factory if uow_factory is not None else build_job_uow_factory()
    )
    return create_api(
        build_create_job_use_case(resolved_uow_factory, publisher),
        build_get_job_use_case(resolved_uow_factory),
    )


def build_execute_dummy_job_use_case() -> ExecuteDummyJobUseCase:
    return ExecuteDummyJobUseCase(build_job_uow_factory(), time.sleep)
