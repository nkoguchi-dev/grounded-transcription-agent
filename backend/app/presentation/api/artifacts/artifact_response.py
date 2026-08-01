from datetime import datetime

from pydantic import BaseModel

from app.domain.artifacts.model import Artifact


class ArtifactResponse(BaseModel):
    id: str
    status: str
    content_type: str
    expected_size: int
    actual_size: int | None
    created_at: datetime
    completed_at: datetime | None

    @classmethod
    def from_artifact(cls, artifact: Artifact) -> "ArtifactResponse":
        return cls(
            id=artifact.id,
            status=artifact.status.value,
            content_type=artifact.content_type,
            expected_size=artifact.expected_size,
            actual_size=artifact.actual_size,
            created_at=artifact.created_at,
            completed_at=artifact.completed_at,
        )
