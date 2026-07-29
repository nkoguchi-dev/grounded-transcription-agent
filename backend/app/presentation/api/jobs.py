from datetime import datetime
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field

from app.application.jobs import CreateJobInput, CreateJobUseCase, GetJobUseCase
from app.domain.jobs.model import Job

router = APIRouter(prefix="/api/jobs", tags=["jobs"])


class CreateJobRequest(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid")
    duration_seconds: int = Field(default=1, ge=0, le=60)
    should_fail: bool = False


class JobResponse(BaseModel):
    id: str
    status: str
    duration_seconds: int
    should_fail: bool
    result: dict[str, Any] | None
    error_message: str | None
    created_at: datetime
    started_at: datetime | None
    finished_at: datetime | None

    @classmethod
    def from_job(cls, job: Job) -> "JobResponse":
        return cls(
            id=job.id,
            status=job.status.value,
            duration_seconds=job.duration_seconds,
            should_fail=job.should_fail,
            result=job.result,
            error_message=job.error_message,
            created_at=job.created_at,
            started_at=job.started_at,
            finished_at=job.finished_at,
        )


def get_create_job_use_case() -> CreateJobUseCase:
    raise RuntimeError("CreateJobUseCase dependency is not configured")


def get_get_job_use_case() -> GetJobUseCase:
    raise RuntimeError("GetJobUseCase dependency is not configured")


@router.post("", response_model=JobResponse, status_code=status.HTTP_202_ACCEPTED)
def create_job(
    request: CreateJobRequest,
    use_case: Annotated[CreateJobUseCase, Depends(get_create_job_use_case)],
) -> JobResponse:
    job = use_case.execute(
        CreateJobInput(request.duration_seconds, request.should_fail)
    )
    try:
        job = use_case.dispatch(job)
    except Exception as error:
        raise HTTPException(
            status_code=503, detail="Job broker is unavailable"
        ) from error
    return JobResponse.from_job(job)


@router.get("/{job_id}", response_model=JobResponse)
def get_job(
    job_id: str,
    use_case: Annotated[GetJobUseCase, Depends(get_get_job_use_case)],
) -> JobResponse:
    job = use_case.execute(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    return JobResponse.from_job(job)
