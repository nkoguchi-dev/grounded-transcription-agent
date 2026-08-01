from datetime import datetime
from typing import Annotated, Any

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel, ConfigDict, Field

from app.application.jobs.create_job_use_case import CreateJobInput, CreateJobUseCase
from app.domain.jobs.model import Job

router = APIRouter(prefix="/api/jobs", tags=["jobs"])


class CreateJobRequest(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid")

    duration_seconds: int = Field(default=1, ge=0, le=60)
    should_fail: bool = False


class CreateJobResponse(BaseModel):
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
    def from_job(cls, job: Job) -> "CreateJobResponse":
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


@router.post("", response_model=CreateJobResponse, status_code=status.HTTP_202_ACCEPTED)
def create_job(
    request: CreateJobRequest,
    use_case: Annotated[CreateJobUseCase, Depends(get_create_job_use_case)],
) -> CreateJobResponse:
    job = use_case.execute(
        CreateJobInput(request.duration_seconds, request.should_fail)
    )
    job = use_case.dispatch(job)
    return CreateJobResponse.from_job(job)
