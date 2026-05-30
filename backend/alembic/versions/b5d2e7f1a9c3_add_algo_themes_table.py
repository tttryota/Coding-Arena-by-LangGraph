"""add_algo_themes_table

Revision ID: b5d2e7f1a9c3
Revises: a3f1c9d8e7b2
Create Date: 2026-05-30 10:00:00.000000

"""

import json
from collections.abc import Sequence
from pathlib import Path

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "b5d2e7f1a9c3"
down_revision: str | Sequence[str] | None = "a3f1c9d8e7b2"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    algo_themes = op.create_table(
        "algo_themes",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("category", sa.String(), nullable=False),
        sa.Column("label", sa.String(), nullable=False),
        sa.Column("display_order", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    # Seed fixture data from JSON
    json_path = Path(__file__).resolve().parents[2] / "data" / "algo_themes.json"
    themes = json.loads(json_path.read_text(encoding="utf-8"))
    op.bulk_insert(
        algo_themes,
        [
            {
                "id": t["id"],
                "category": t["category"],
                "label": t["label"],
                "display_order": t["display_order"],
            }
            for t in themes
        ],
    )


def downgrade() -> None:
    op.drop_table("algo_themes")
