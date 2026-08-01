from dataclasses import dataclass, replace
from datetime import datetime, timezone
from enum import StrEnum
from uuid import uuid4


class ArtifactStatus(StrEnum):
    PENDING = "pending"
    READY = "ready"


@dataclass(frozen=True)
class Artifact:
    id: str
    object_key: str
    status: ArtifactStatus
    content_type: str
    expected_size: int
    actual_size: int | None
    created_at: datetime
    completed_at: datetime | None

    @classmethod
    def create(cls, content_type: str, expected_size: int) -> "Artifact":
        if not content_type.strip():
            raise ValueError("content_type must not be empty")
        if expected_size < 0:
            raise ValueError("expected_size must not be negative")
        artifact_id = str(uuid4())
        return cls(
            id=artifact_id,
            object_key=f"artifacts/{artifact_id}/{uuid4().hex}",
            status=ArtifactStatus.PENDING,
            content_type=content_type,
            expected_size=expected_size,
            actual_size=None,
            created_at=datetime.now(timezone.utc),
            completed_at=None,
        )

    def complete(self, actual_size: int) -> "Artifact":
        # A repeated completion notification must preserve the first observed result.
        if self.status is ArtifactStatus.READY:
            return self
        return replace(
            self,
            status=ArtifactStatus.READY,
            actual_size=actual_size,
            completed_at=datetime.now(timezone.utc),
        )
