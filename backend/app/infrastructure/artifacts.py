from datetime import datetime

from sqlalchemy import BigInteger, DateTime, String
from sqlalchemy.orm import Mapped, Session, mapped_column

from app.domain.artifacts.model import Artifact, ArtifactStatus
from app.infrastructure.jobs import Base


class ArtifactRecord(Base):
    __tablename__ = "artifacts"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    object_key: Mapped[str] = mapped_column(String(255), unique=True)
    status: Mapped[str] = mapped_column(String(16))
    content_type: Mapped[str] = mapped_column(String(255))
    expected_size: Mapped[int] = mapped_column(BigInteger)
    actual_size: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    def to_domain(self) -> Artifact:
        return Artifact(
            id=self.id,
            object_key=self.object_key,
            status=ArtifactStatus(self.status),
            content_type=self.content_type,
            expected_size=self.expected_size,
            actual_size=self.actual_size,
            created_at=self.created_at,
            completed_at=self.completed_at,
        )


class SqlAlchemyArtifactRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def create(self, artifact: Artifact) -> None:
        values = artifact.__dict__ | {"status": artifact.status.value}
        self._session.add(ArtifactRecord(**values))

    def get(self, artifact_id: str) -> Artifact | None:
        record = self._session.get(ArtifactRecord, artifact_id)
        return record.to_domain() if record else None

    def update(self, artifact: Artifact) -> None:
        record = self._session.get(ArtifactRecord, artifact.id)
        if record is None:
            raise LookupError(artifact.id)
        for field, value in artifact.__dict__.items():
            setattr(
                record,
                field,
                value.value if isinstance(value, ArtifactStatus) else value,
            )
