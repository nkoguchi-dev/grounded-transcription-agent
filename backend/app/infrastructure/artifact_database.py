from collections.abc import Callable

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.application.artifacts.unit_of_work import ArtifactUnitOfWorkFactory
from app.domain.artifacts.artifact_repository import ArtifactRepository
from app.infrastructure.artifacts import SqlAlchemyArtifactRepository


class SqlAlchemyArtifactUnitOfWork:
    def __init__(self, session_factory: Callable[[], Session]) -> None:
        self._session_factory = session_factory
        self._session: Session | None = None
        self._artifacts: ArtifactRepository | None = None

    @property
    def artifacts(self) -> ArtifactRepository:
        if self._artifacts is None:
            raise RuntimeError("Unit of work has not been entered")
        return self._artifacts

    def __enter__(self) -> "SqlAlchemyArtifactUnitOfWork":
        self._session = self._session_factory()
        self._artifacts = SqlAlchemyArtifactRepository(self._session)
        return self

    def __exit__(self, *_: object) -> None:
        if self._session is not None:
            self._session.rollback()
            self._session.close()
        self._session = None
        self._artifacts = None

    def commit(self) -> None:
        if self._session is None:
            raise RuntimeError("Unit of work has not been entered")
        self._session.commit()


def create_sqlalchemy_artifact_uow_factory(
    database_url: str,
) -> ArtifactUnitOfWorkFactory:
    engine = create_engine(database_url, pool_pre_ping=True)
    sessions = sessionmaker(bind=engine, expire_on_commit=False)
    return lambda: SqlAlchemyArtifactUnitOfWork(sessions)
