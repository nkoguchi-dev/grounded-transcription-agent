from datetime import datetime
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.application.jobs.get_job_use_case import GetJobUseCase
from app.domain.jobs.model import Job

router = APIRouter(prefix="/api/jobs", tags=["jobs"])


class GetJobResponse(BaseModel):
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
    def from_job(cls, job: Job) -> "GetJobResponse":
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


def get_get_job_use_case() -> GetJobUseCase:
    raise RuntimeError("GetJobUseCase dependency is not configured")


@router.get("/{job_id}", response_model=GetJobResponse)
def get_job(
    job_id: str,
    use_case: Annotated[GetJobUseCase, Depends(get_get_job_use_case)],
) -> GetJobResponse:
    job = use_case.execute(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    return GetJobResponse.from_job(job)
