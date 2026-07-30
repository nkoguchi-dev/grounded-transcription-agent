from pathlib import Path

import pytest
from sqlalchemy import create_engine, inspect, text

from alembic import command
from alembic.config import Config


def test_task_id_migration_preserves_existing_values(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    database_url = f"sqlite:///{tmp_path / 'jobs.db'}"
    monkeypatch.setenv("DATABASE_URL", database_url)
    config = Config(str(Path(__file__).parents[1] / "alembic.ini"))

    command.upgrade(config, "0001")
    engine = create_engine(database_url)
    with engine.begin() as connection:
        connection.execute(text("""
                INSERT INTO jobs (
                    id, status, duration_seconds, should_fail, result, error_message,
                    celery_task_id, created_at, started_at, finished_at
                ) VALUES (
                    'job-123', 'queued', 0, 0, NULL, NULL, 'task-123',
                    '2026-07-30 00:00:00', NULL, NULL
                )
                """))

    command.upgrade(config, "head")

    inspector = inspect(engine)
    assert "task_id" in {column["name"] for column in inspector.get_columns("jobs")}
    with engine.connect() as connection:
        assert (
            connection.execute(
                text("SELECT task_id FROM jobs WHERE id = 'job-123'")
            ).scalar_one()
            == "task-123"
        )
