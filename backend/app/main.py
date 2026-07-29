from fastapi import FastAPI

from app.composition import build_create_job_use_case, build_get_job_use_case
from app.presentation.api.jobs import (
    get_create_job_use_case,
    get_get_job_use_case,
)
from app.presentation.api.jobs import router as jobs_router

app = FastAPI(title="Grounded Transcription Agent")
app.dependency_overrides[get_create_job_use_case] = build_create_job_use_case
app.dependency_overrides[get_get_job_use_case] = build_get_job_use_case
app.include_router(jobs_router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
