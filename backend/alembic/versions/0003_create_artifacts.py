"""create artifacts table

Revision ID: 0003
Revises: 0002
Create Date: 2026-08-01
"""

import sqlalchemy as sa

from alembic import op

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "artifacts",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("object_key", sa.String(255), nullable=False, unique=True),
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column("content_type", sa.String(255), nullable=False),
        sa.Column("expected_size", sa.BigInteger(), nullable=False),
        sa.Column("actual_size", sa.BigInteger(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_table("artifacts")
