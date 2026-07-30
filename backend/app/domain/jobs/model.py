from dataclasses import dataclass, replace
from datetime import datetime, timezone
from enum import StrEnum
from typing import Any
from uuid import uuid4


class JobStatus(StrEnum):
    QUEUED = "queued"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"


@dataclass(frozen=True)
class Job:
    id: str
    status: JobStatus
    duration_seconds: int
    should_fail: bool
    result: dict[str, Any] | None
    error_message: str | None
    task_id: str | None
    created_at: datetime
    started_at: datetime | None
    finished_at: datetime | None

    @classmethod
    def create(cls, duration_seconds: int, should_fail: bool) -> "Job":
        if not 0 <= duration_seconds <= 60:
            raise ValueError("duration_seconds must be between 0 and 60")
        return cls(
            id=str(uuid4()),
            status=JobStatus.QUEUED,
            duration_seconds=duration_seconds,
            should_fail=should_fail,
            result=None,
            error_message=None,
            task_id=None,
            created_at=datetime.now(timezone.utc),
            started_at=None,
            finished_at=None,
        )

    def with_task_id(self, task_id: str) -> "Job":
        return replace(self, task_id=task_id)

    def start(self) -> "Job":
        if self.status is not JobStatus.QUEUED:
            raise ValueError("only queued jobs can start")
        return replace(
            self, status=JobStatus.RUNNING, started_at=datetime.now(timezone.utc)
        )

    def succeed(self, result: dict[str, Any]) -> "Job":
        if self.status is not JobStatus.RUNNING:
            raise ValueError("only running jobs can succeed")
        return replace(
            self,
            status=JobStatus.SUCCEEDED,
            result=result,
            finished_at=datetime.now(timezone.utc),
        )

    def fail(self, error_message: str) -> "Job":
        if self.status is not JobStatus.RUNNING:
            raise ValueError("only running jobs can fail")
        return replace(
            self,
            status=JobStatus.FAILED,
            error_message=error_message,
            finished_at=datetime.now(timezone.utc),
        )
