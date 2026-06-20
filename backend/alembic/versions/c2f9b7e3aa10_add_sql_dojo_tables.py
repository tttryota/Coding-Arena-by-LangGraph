"""add_sql_dojo_tables

Revision ID: c2f9b7e3aa10
Revises: a3f1c9d8e7b2
Create Date: 2026-06-19 12:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "c2f9b7e3aa10"
down_revision: str | Sequence[str] | None = "a3f1c9d8e7b2"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "sql_dojo_sessions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("theme_family", sa.String(), nullable=False),
        sa.Column("difficulty", sa.String(), nullable=False),
        sa.Column("dialect", sa.String(), nullable=False),
        sa.Column("theme_title", sa.String(), nullable=False),
        sa.Column("business_domain", sa.String(), nullable=False),
        sa.Column("target_skill", sa.String(), nullable=False),
        sa.Column("problem_statement", sa.Text(), nullable=False),
        sa.Column("schema_markdown", sa.Text(), nullable=False),
        sa.Column("sample_data_json", sa.Text(), nullable=False),
        sa.Column("expected_focus", sa.Text(), nullable=False),
        sa.Column("reference_sql", sa.Text(), nullable=False),
        sa.Column("grading_contract_json", sa.Text(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "sql_dojo_answers",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("session_id", sa.Uuid(), nullable=False),
        sa.Column("answer_text", sa.Text(), nullable=False),
        sa.Column("score", sa.Integer(), nullable=False),
        sa.Column("feedback", sa.Text(), nullable=False),
        sa.Column("rule_breakdown_json", sa.Text(), nullable=False),
        sa.Column("improvement_suggestions", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(
            ["session_id"],
            ["sql_dojo_sessions.id"],
            name="fk_sql_dojo_answers_session_id",
        ),
        sa.UniqueConstraint("session_id", name="uq_sql_dojo_answers_session_id"),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("sql_dojo_answers")
    op.drop_table("sql_dojo_sessions")
