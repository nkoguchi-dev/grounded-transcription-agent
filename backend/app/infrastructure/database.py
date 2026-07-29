import os
from collections.abc import Callable

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.application.ports import JobRepository
from app.infrastructure.jobs import SqlAlchemyJobRepository

engine = create_engine(os.environ["DATABASE_URL"], pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)


class SqlAlchemyJobUnitOfWork:
    def __init__(self, session_factory: Callable[[], Session] = SessionLocal) -> None:
        self._session_factory = session_factory
        self._session: Session | None = None
        self._jobs: JobRepository | None = None

    @property
    def jobs(self) -> JobRepository:
        if self._jobs is None:
            raise RuntimeError("Unit of work has not been entered")
        return self._jobs

    def __enter__(self) -> "SqlAlchemyJobUnitOfWork":
        self._session = self._session_factory()
        self._jobs = SqlAlchemyJobRepository(self._session)
        return self

    def __exit__(self, *_: object) -> None:
        if self._session is not None:
            self._session.rollback()
            self._session.close()
        self._session = None
        self._jobs = None

    def commit(self) -> None:
        if self._session is None:
            raise RuntimeError("Unit of work has not been entered")
        self._session.commit()

    def rollback(self) -> None:
        if self._session is None:
            raise RuntimeError("Unit of work has not been entered")
        self._session.rollback()
