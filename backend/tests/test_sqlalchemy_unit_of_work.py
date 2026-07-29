from collections.abc import Callable

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.domain.jobs.model import Job
from app.infrastructure.database import SqlAlchemyJobUnitOfWork
from app.infrastructure.jobs import Base


@pytest.fixture
def uow_factory() -> Callable[[], SqlAlchemyJobUnitOfWork]:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    sessions = sessionmaker(bind=engine, expire_on_commit=False)
    return lambda: SqlAlchemyJobUnitOfWork(sessions)


def test_unit_of_work_commits_changes(
    uow_factory: Callable[[], SqlAlchemyJobUnitOfWork],
) -> None:
    job = Job.create(0, False)

    with uow_factory() as uow:
        uow.jobs.create(job)
        uow.commit()

    with uow_factory() as uow:
        persisted_job = uow.jobs.get(job.id)

    assert persisted_job is not None
    assert persisted_job.id == job.id
    assert persisted_job.status == job.status
    assert persisted_job.duration_seconds == job.duration_seconds
    assert persisted_job.should_fail == job.should_fail


def test_unit_of_work_rolls_back_when_use_case_fails(
    uow_factory: Callable[[], SqlAlchemyJobUnitOfWork],
) -> None:
    job = Job.create(0, False)

    with pytest.raises(RuntimeError, match="persistence failed"):
        with uow_factory() as uow:
            uow.jobs.create(job)
            raise RuntimeError("persistence failed")

    with uow_factory() as uow:
        assert uow.jobs.get(job.id) is None
