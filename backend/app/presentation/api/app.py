from fastapi import FastAPI

from app.application.artifacts.complete_upload import CompleteUploadUseCase
from app.application.artifacts.create_download_url import CreateDownloadUrlUseCase
from app.application.artifacts.get_artifact import GetArtifactUseCase
from app.application.artifacts.start_upload import StartUploadUseCase
from app.application.jobs.create_job_use_case import CreateJobUseCase
from app.application.jobs.get_job_use_case import GetJobUseCase
from app.presentation.api.application_error_handlers import (
    register_application_error_handlers,
)
from app.presentation.api.artifacts import router as artifacts_router
from app.presentation.api.artifacts.complete_upload import get_complete_upload_use_case
from app.presentation.api.artifacts.create_download_url import (
    get_create_download_url_use_case,
)
from app.presentation.api.artifacts.get_artifact import get_get_artifact_use_case
from app.presentation.api.artifacts.start_upload import get_start_upload_use_case
from app.presentation.api.jobs import router as jobs_router
from app.presentation.api.jobs.create_job import get_create_job_use_case
from app.presentation.api.jobs.get_job import get_get_job_use_case


def create_api(
    create_job_use_case: CreateJobUseCase,
    get_job_use_case: GetJobUseCase,
    *,
    start_upload_use_case: StartUploadUseCase | None = None,
    complete_upload_use_case: CompleteUploadUseCase | None = None,
    get_artifact_use_case: GetArtifactUseCase | None = None,
    create_download_url_use_case: CreateDownloadUrlUseCase | None = None,
) -> FastAPI:
    app = FastAPI(title="Grounded Transcription Agent")
    app.dependency_overrides[get_create_job_use_case] = lambda: create_job_use_case
    app.dependency_overrides[get_get_job_use_case] = lambda: get_job_use_case
    register_application_error_handlers(app)
    app.include_router(jobs_router)
    artifact_use_cases = (
        start_upload_use_case,
        complete_upload_use_case,
        get_artifact_use_case,
        create_download_url_use_case,
    )
    if all(use_case is not None for use_case in artifact_use_cases):
        app.dependency_overrides[get_start_upload_use_case] = (
            lambda: start_upload_use_case
        )
        app.dependency_overrides[get_complete_upload_use_case] = (
            lambda: complete_upload_use_case
        )
        app.dependency_overrides[get_get_artifact_use_case] = (
            lambda: get_artifact_use_case
        )
        app.dependency_overrides[get_create_download_url_use_case] = (
            lambda: create_download_url_use_case
        )
        app.include_router(artifacts_router)

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    return app
