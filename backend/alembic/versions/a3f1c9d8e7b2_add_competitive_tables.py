"""add_competitive_tables

Revision ID: a3f1c9d8e7b2
Revises: e58995544a46
Create Date: 2026-05-29 10:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a3f1c9d8e7b2"
down_revision: str | Sequence[str] | None = "e58995544a46"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "competitive_sessions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("theme_id", sa.String(), nullable=False),
        sa.Column("theme_label", sa.String(), nullable=False),
        sa.Column("theme_category", sa.String(), nullable=False),
        sa.Column("programming_language", sa.String(), nullable=False),
        sa.Column("problem_statement", sa.Text(), nullable=False),
        sa.Column("input_format", sa.Text(), nullable=False),
        sa.Column("output_format", sa.Text(), nullable=False),
        sa.Column("constraints", sa.Text(), nullable=False),
        sa.Column("examples_json", sa.Text(), nullable=False),
        sa.Column("reference_solution", sa.Text(), nullable=False),
        sa.Column("grading_rubric_json", sa.Text(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "competitive_answers",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("session_id", sa.Uuid(), nullable=False),
        sa.Column("answer_text", sa.Text(), nullable=False),
        sa.Column("score", sa.Integer(), nullable=False),
        sa.Column("feedback", sa.Text(), nullable=False),
        sa.Column("time_complexity", sa.String(), nullable=False),
        sa.Column("space_complexity", sa.String(), nullable=False),
        sa.Column("improvement_suggestions", sa.Text(), nullable=False),
        sa.Column("rubric_scores_json", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(
            ["session_id"],
            ["competitive_sessions.id"],
            name="fk_competitive_answers_session_id",
        ),
        sa.UniqueConstraint("session_id", name="uq_competitive_answers_session_id"),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("competitive_answers")
    op.drop_table("competitive_sessions")
