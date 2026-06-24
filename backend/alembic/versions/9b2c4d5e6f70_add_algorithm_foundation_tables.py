"""add algorithm foundation tables

Revision ID: 9b2c4d5e6f70
Revises: d4a6b8c9e012
Create Date: 2026-06-25 12:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "9b2c4d5e6f70"
down_revision: str | Sequence[str] | None = "d4a6b8c9e012"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "algorithm_foundation_sessions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("unit_id", sa.String(), nullable=False),
        sa.Column("group_id", sa.String(), nullable=False),
        sa.Column("group_title", sa.String(), nullable=False),
        sa.Column("unit_title", sa.String(), nullable=False),
        sa.Column("target_skill", sa.String(), nullable=False),
        sa.Column("unit_kind", sa.String(), nullable=False),
        sa.Column("prerequisite_unit_ids_json", sa.Text(), nullable=False),
        sa.Column("prerequisite_titles_json", sa.Text(), nullable=False),
        sa.Column("allowed_knowledge_json", sa.Text(), nullable=False),
        sa.Column("forbidden_knowledge_json", sa.Text(), nullable=False),
        sa.Column("programming_language", sa.String(), nullable=False),
        sa.Column("problem_id", sa.String(), nullable=False),
        sa.Column("problem_title", sa.String(), nullable=False),
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
        "algorithm_foundation_answers",
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
        sa.ForeignKeyConstraint(
            ["session_id"],
            ["algorithm_foundation_sessions.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("session_id"),
    )


def downgrade() -> None:
    op.drop_table("algorithm_foundation_answers")
    op.drop_table("algorithm_foundation_sessions")
