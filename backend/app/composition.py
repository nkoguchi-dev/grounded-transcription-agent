import os
import time

from fastapi import FastAPI

from app.application.artifacts.complete_upload import CompleteUploadUseCase
from app.application.artifacts.create_download_url import CreateDownloadUrlUseCase
from app.application.artifacts.get_artifact import GetArtifactUseCase
from app.application.artifacts.object_storage import ObjectStorage
from app.application.artifacts.start_upload import StartUploadUseCase
from app.application.artifacts.unit_of_work import ArtifactUnitOfWorkFactory
from app.application.job_publisher import JobPublisher
from app.application.jobs.create_job_use_case import CreateJobUseCase
from app.application.jobs.execute_dummy_job_use_case import ExecuteDummyJobUseCase
from app.application.jobs.get_job_use_case import GetJobUseCase
from app.application.unit_of_work import JobUnitOfWorkFactory
from app.infrastructure.artifact_database import create_sqlalchemy_artifact_uow_factory
from app.infrastructure.database import create_sqlalchemy_job_uow_factory
from app.infrastructure.object_storage import S3ObjectStorage
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


def build_artifact_uow_factory() -> ArtifactUnitOfWorkFactory:
    return create_sqlalchemy_artifact_uow_factory(os.environ["DATABASE_URL"])


def build_object_storage() -> ObjectStorage:
    return S3ObjectStorage(
        internal_endpoint=os.environ["MINIO_INTERNAL_ENDPOINT"],
        public_endpoint=os.environ["MINIO_PUBLIC_ENDPOINT"],
        access_key=os.environ["MINIO_ACCESS_KEY"],
        secret_key=os.environ["MINIO_SECRET_KEY"],
        bucket=os.environ["MINIO_BUCKET"],
        region=os.environ.get("MINIO_REGION", "ap-northeast-1"),
        url_expiry_seconds=int(os.environ.get("PRESIGNED_URL_EXPIRY_SECONDS", "900")),
    )


def create_application(
    *,
    uow_factory: JobUnitOfWorkFactory | None = None,
    publisher: JobPublisher | None = None,
    artifact_uow_factory: ArtifactUnitOfWorkFactory | None = None,
    object_storage: ObjectStorage | None = None,
) -> FastAPI:
    resolved_uow_factory = (
        uow_factory if uow_factory is not None else build_job_uow_factory()
    )
    resolved_artifact_uow_factory = (
        artifact_uow_factory
        if artifact_uow_factory is not None
        else build_artifact_uow_factory()
    )
    resolved_storage = (
        object_storage if object_storage is not None else build_object_storage()
    )
    return create_api(
        build_create_job_use_case(resolved_uow_factory, publisher),
        build_get_job_use_case(resolved_uow_factory),
        start_upload_use_case=StartUploadUseCase(
            resolved_artifact_uow_factory, resolved_storage
        ),
        complete_upload_use_case=CompleteUploadUseCase(
            resolved_artifact_uow_factory, resolved_storage
        ),
        get_artifact_use_case=GetArtifactUseCase(resolved_artifact_uow_factory),
        create_download_url_use_case=CreateDownloadUrlUseCase(
            resolved_artifact_uow_factory, resolved_storage
        ),
    )


def build_execute_dummy_job_use_case() -> ExecuteDummyJobUseCase:
    return ExecuteDummyJobUseCase(build_job_uow_factory(), time.sleep)
