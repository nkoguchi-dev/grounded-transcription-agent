"""rename celery task ID column

Revision ID: 0002
Revises: 0001
Create Date: 2026-07-30
"""

import sqlalchemy as sa

from alembic import op

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column(
        "jobs",
        "celery_task_id",
        new_column_name="task_id",
        existing_type=sa.String(length=36),
        existing_nullable=True,
    )


def downgrade() -> None:
    op.alter_column(
        "jobs",
        "task_id",
        new_column_name="celery_task_id",
        existing_type=sa.String(length=36),
        existing_nullable=True,
    )
