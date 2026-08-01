from collections.abc import Callable

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.application.unit_of_work import JobUnitOfWorkFactory
from app.domain.jobs.job_repository import JobRepository
from app.infrastructure.jobs import SqlAlchemyJobRepository


class SqlAlchemyJobUnitOfWork:
    def __init__(self, session_factory: Callable[[], Session]) -> None:
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
            # commit is explicit at the use-case boundary. Always rolling back here
            # discards partial changes when a block exits through an exception.
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


def create_sqlalchemy_job_uow_factory(database_url: str) -> JobUnitOfWorkFactory:
    engine = create_engine(database_url, pool_pre_ping=True)
    sessions = sessionmaker(bind=engine, expire_on_commit=False)
    return lambda: SqlAlchemyJobUnitOfWork(sessions)
