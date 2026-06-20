"""merge_algo_themes_and_sql_dojo_heads

Revision ID: f7d1b8c4a2e6
Revises: b5d2e7f1a9c3, c2f9b7e3aa10
Create Date: 2026-06-20 00:35:00.000000

"""

from collections.abc import Sequence

revision: str = "f7d1b8c4a2e6"
down_revision: str | Sequence[str] | None = ("b5d2e7f1a9c3", "c2f9b7e3aa10")
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""


def downgrade() -> None:
    """Downgrade schema."""
