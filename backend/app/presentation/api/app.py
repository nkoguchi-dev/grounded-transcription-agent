from fastapi import FastAPI

from app.application.jobs.create_job_use_case import CreateJobUseCase
from app.application.jobs.get_job_use_case import GetJobUseCase
from app.presentation.api.jobs import router as jobs_router
from app.presentation.api.jobs.create_job import get_create_job_use_case
from app.presentation.api.jobs.get_job import get_get_job_use_case


def create_api(
    create_job_use_case: CreateJobUseCase, get_job_use_case: GetJobUseCase
) -> FastAPI:
    app = FastAPI(title="Grounded Transcription Agent")
    app.dependency_overrides[get_create_job_use_case] = lambda: create_job_use_case
    app.dependency_overrides[get_get_job_use_case] = lambda: get_job_use_case
    app.include_router(jobs_router)

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    return app
