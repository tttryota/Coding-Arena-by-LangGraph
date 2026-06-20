"""add_sql_dojo_topic_columns

Revision ID: d4a6b8c9e012
Revises: f7d1b8c4a2e6
Create Date: 2026-06-20 22:45:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "d4a6b8c9e012"
down_revision: str | Sequence[str] | None = "f7d1b8c4a2e6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column("sql_dojo_sessions", sa.Column("topic_id", sa.String(), nullable=True))
    op.add_column(
        "sql_dojo_sessions",
        sa.Column("topic_title", sa.String(), nullable=True),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("sql_dojo_sessions", "topic_title")
    op.drop_column("sql_dojo_sessions", "topic_id")

