"""add_phase2_tables

Revision ID: e58995544a46
Revises: 1a2c78eddbeb
Create Date: 2026-05-23 11:04:13.308892

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "e58995544a46"
down_revision: str | Sequence[str] | None = "1a2c78eddbeb"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "roadmaps",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("topic", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "topics",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("canonical_name", sa.String(), nullable=False),
        sa.Column("source", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("canonical_name"),
    )
    op.create_table(
        "diff_snapshots",
        sa.Column("snapshot_key", sa.String(), nullable=False),
        sa.Column("files_json", sa.Text(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("snapshot_key"),
    )
    with op.batch_alter_table("quiz_answers", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column("confirmation_point_id", sa.String(), nullable=False),
        )

    with op.batch_alter_table("roadmap_items", schema=None) as batch_op:
        batch_op.create_foreign_key(
            "fk_roadmap_items_roadmap_id",
            "roadmaps",
            ["roadmap_id"],
            ["id"],
        )


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table("roadmap_items", schema=None) as batch_op:
        batch_op.drop_constraint("fk_roadmap_items_roadmap_id", type_="foreignkey")

    with op.batch_alter_table("quiz_answers", schema=None) as batch_op:
        batch_op.drop_column("confirmation_point_id")

    op.drop_table("diff_snapshots")
    op.drop_table("topics")
    op.drop_table("roadmaps")
