import os
from collections.abc import Generator
from pathlib import Path

import pytest
from sqlalchemy import Engine, create_engine, text
from sqlalchemy.orm import Session, sessionmaker
from testcontainers.postgres import PostgresContainer

from alembic import command
from alembic.config import Config
from app.application.unit_of_work import JobUnitOfWorkFactory


@pytest.fixture(scope="session")
def database_engine() -> Generator[Engine]:
    previous_database_url = os.environ.get("DATABASE_URL")
    with PostgresContainer("postgres:17", driver="psycopg") as postgres:
        database_url = postgres.get_connection_url()
        os.environ["DATABASE_URL"] = database_url

        config = Config(str(Path(__file__).parents[1] / "alembic.ini"))
        command.upgrade(config, "head")
        engine = create_engine(database_url, pool_pre_ping=True)
        try:
            yield engine
        finally:
            engine.dispose()
            if previous_database_url is None:
                os.environ.pop("DATABASE_URL", None)
            else:
                os.environ["DATABASE_URL"] = previous_database_url


@pytest.fixture(scope="session")
def database_session_factory(database_engine: Engine) -> sessionmaker[Session]:
    return sessionmaker(bind=database_engine, expire_on_commit=False)


@pytest.fixture(scope="session")
def uow_factory(
    database_session_factory: sessionmaker[Session],
) -> JobUnitOfWorkFactory:
    from app.infrastructure.database import SqlAlchemyJobUnitOfWork

    return lambda: SqlAlchemyJobUnitOfWork(database_session_factory)


@pytest.fixture(autouse=True)
def isolate_test_data(database_engine: Engine) -> Generator[None]:
    yield
    # Use database-level cleanup because application transactions have already
    # committed by the time an API request returns.
    with database_engine.begin() as connection:
        connection.execute(text("TRUNCATE TABLE jobs"))
