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


def _load_themes() -> list[dict[str, object]]:
    """Fixture JSON を読み込む (Docker: /opt/fixtures, local: data/)。"""
    json_path = Path(__file__).resolve().parents[2] / "data" / "algo_themes.json"
    if not json_path.exists():
        json_path = Path("/opt/fixtures/algo_themes.json")
    return json.loads(json_path.read_text(encoding="utf-8"))  # type: ignore[no-any-return]


def upgrade() -> None:
    conn = op.get_bind()
    # べき等: テーブルが既に存在する場合はスキップ
    inspector = sa.inspect(conn)
    if "algo_themes" not in inspector.get_table_names():
        op.create_table(
            "algo_themes",
            sa.Column("id", sa.String(), nullable=False),
            sa.Column("category", sa.String(), nullable=False),
            sa.Column("label", sa.String(), nullable=False),
            sa.Column("display_order", sa.Integer(), nullable=False),
            sa.PrimaryKeyConstraint("id"),
        )

    # データが空なら INSERT
    algo_themes = sa.table(
        "algo_themes",
        sa.column("id", sa.String),
        sa.column("category", sa.String),
        sa.column("label", sa.String),
        sa.column("display_order", sa.Integer),
    )
    count = conn.execute(sa.select(sa.func.count()).select_from(algo_themes)).scalar()
    if count == 0:
        themes = _load_themes()
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
