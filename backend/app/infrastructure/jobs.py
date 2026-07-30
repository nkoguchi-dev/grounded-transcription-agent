from datetime import datetime
from typing import Any

from sqlalchemy import JSON, Boolean, DateTime, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column

from app.domain.jobs.model import Job, JobStatus


class Base(DeclarativeBase):
    pass


class JobRecord(Base):
    __tablename__ = "jobs"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    status: Mapped[str] = mapped_column(String(16))
    duration_seconds: Mapped[int] = mapped_column(Integer)
    should_fail: Mapped[bool] = mapped_column(Boolean)
    result: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    task_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    finished_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    def to_domain(self) -> Job:
        return Job(
            self.id,
            JobStatus(self.status),
            self.duration_seconds,
            self.should_fail,
            self.result,
            self.error_message,
            self.task_id,
            self.created_at,
            self.started_at,
            self.finished_at,
        )


class SqlAlchemyJobRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def create(self, job: Job) -> None:
        self._session.add(JobRecord(**job.__dict__))

    def get(self, job_id: str) -> Job | None:
        record = self._session.get(JobRecord, job_id)
        return record.to_domain() if record else None

    def update(self, job: Job) -> None:
        record = self._session.get(JobRecord, job.id)
        if record is None:
            raise LookupError(job.id)
        for field, value in job.__dict__.items():
            setattr(
                record, field, value.value if isinstance(value, JobStatus) else value
            )

    def set_task_id(self, job_id: str, task_id: str) -> None:
        record = self._session.get(JobRecord, job_id)
        if record is None:
            raise LookupError(job_id)
        record.task_id = task_id
