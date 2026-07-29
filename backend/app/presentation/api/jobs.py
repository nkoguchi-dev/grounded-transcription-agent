from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.orm import Session

from app.application.jobs import CreateJobInput, CreateJobUseCase, GetJobUseCase
from app.celery_app import celery
from app.domain.jobs.model import Job
from app.infrastructure.database import get_session
from app.infrastructure.jobs import SqlAlchemyJobRepository

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


@router.post("", response_model=JobResponse, status_code=status.HTTP_202_ACCEPTED)
def create_job(
    request: CreateJobRequest, session: Session = Depends(get_session)
) -> JobResponse:
    repository = SqlAlchemyJobRepository(session)
    use_case = CreateJobUseCase(repository, celery)
    job = use_case.execute(
        CreateJobInput(request.duration_seconds, request.should_fail)
    )
    session.commit()
    try:
        job = use_case.dispatch(job)
        session.commit()
    except Exception as error:
        session.rollback()
        raise HTTPException(
            status_code=503, detail="Job broker is unavailable"
        ) from error
    return JobResponse.from_job(job)


@router.get("/{job_id}", response_model=JobResponse)
def get_job(job_id: str, session: Session = Depends(get_session)) -> JobResponse:
    job = GetJobUseCase(SqlAlchemyJobRepository(session)).execute(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    return JobResponse.from_job(job)
