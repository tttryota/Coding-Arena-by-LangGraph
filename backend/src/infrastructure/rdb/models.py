import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from infrastructure.rdb.base import Base


class Roadmap(Base):
    __tablename__ = "roadmaps"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    topic: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    items: Mapped[list["RoadmapItem"]] = relationship(
        "RoadmapItem",
        back_populates="roadmap",
    )


class RoadmapItem(Base):
    __tablename__ = "roadmap_items"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    roadmap_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("roadmaps.id"),
        nullable=False,
    )
    parent_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid,
        ForeignKey("roadmap_items.id"),
        nullable=True,
    )
    level: Mapped[str] = mapped_column(String, nullable=False)
    title: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str] = mapped_column(String, nullable=False)
    order: Mapped[int] = mapped_column(Integer, nullable=False)
    score: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    last_quiz_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    roadmap: Mapped["Roadmap"] = relationship(
        "Roadmap",
        back_populates="items",
    )
    children: Mapped[list["RoadmapItem"]] = relationship(
        "RoadmapItem",
        back_populates="parent",
    )
    parent: Mapped["RoadmapItem | None"] = relationship(
        "RoadmapItem",
        back_populates="children",
        remote_side=[id],  # noqa: A003
    )
    quiz_sessions: Mapped[list["QuizSession"]] = relationship(
        "QuizSession",
        back_populates="roadmap_item",
    )
    quiz_answers: Mapped[list["QuizAnswer"]] = relationship(
        "QuizAnswer",
        back_populates="roadmap_item",
    )
    ingestion_feedbacks: Mapped[list["IngestionFeedback"]] = relationship(
        "IngestionFeedback",
        back_populates="roadmap_item",
    )


class QuizSession(Base):
    __tablename__ = "quiz_sessions"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    roadmap_item_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("roadmap_items.id"),
        nullable=False,
    )
    status: Mapped[str] = mapped_column(String, nullable=False)
    started_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    roadmap_item: Mapped["RoadmapItem"] = relationship(
        "RoadmapItem",
        back_populates="quiz_sessions",
    )
    answers: Mapped[list["QuizAnswer"]] = relationship(
        "QuizAnswer",
        back_populates="session",
    )
    summary_test_result: Mapped["SummaryTestResult | None"] = relationship(
        "SummaryTestResult",
        back_populates="session",
        uselist=False,
    )


class QuizAnswer(Base):
    __tablename__ = "quiz_answers"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    session_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("quiz_sessions.id"),
        nullable=False,
    )
    roadmap_item_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("roadmap_items.id"),
        nullable=False,
    )
    confirmation_point_id: Mapped[str] = mapped_column(String, nullable=False)
    question_number: Mapped[int] = mapped_column(Integer, nullable=False)
    question_text: Mapped[str] = mapped_column(Text, nullable=False)
    answer_type: Mapped[str] = mapped_column(String, nullable=False)
    answer_text: Mapped[str] = mapped_column(Text, nullable=False)
    score: Mapped[int] = mapped_column(Integer, nullable=False)
    feedback: Mapped[str] = mapped_column(Text, nullable=False)
    answered_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    session: Mapped["QuizSession"] = relationship(
        "QuizSession",
        back_populates="answers",
    )
    roadmap_item: Mapped["RoadmapItem"] = relationship(
        "RoadmapItem",
        back_populates="quiz_answers",
    )


class IngestionFeedback(Base):
    __tablename__ = "ingestion_feedbacks"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    source_path: Mapped[str] = mapped_column(String, nullable=False)
    roadmap_item_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid,
        ForeignKey("roadmap_items.id"),
        nullable=True,
    )
    title: Mapped[str] = mapped_column(String, nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    is_read: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    read_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    roadmap_item: Mapped["RoadmapItem | None"] = relationship(
        "RoadmapItem",
        back_populates="ingestion_feedbacks",
    )


class SummaryTestResult(Base):
    __tablename__ = "summary_test_results"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    session_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("quiz_sessions.id"),
        nullable=False,
    )
    score: Mapped[int] = mapped_column(Integer, nullable=False)
    analysis: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    session: Mapped["QuizSession"] = relationship(
        "QuizSession",
        back_populates="summary_test_result",
    )


class Topic(Base):
    __tablename__ = "topics"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String, nullable=False)
    canonical_name: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    source: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)


class CompetitiveSession(Base):
    __tablename__ = "competitive_sessions"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    theme_id: Mapped[str] = mapped_column(String, nullable=False)
    theme_label: Mapped[str] = mapped_column(String, nullable=False)
    theme_category: Mapped[str] = mapped_column(String, nullable=False)
    programming_language: Mapped[str] = mapped_column(String, nullable=False)
    problem_statement: Mapped[str] = mapped_column(Text, nullable=False)
    input_format: Mapped[str] = mapped_column(Text, nullable=False)
    output_format: Mapped[str] = mapped_column(Text, nullable=False)
    constraints: Mapped[str] = mapped_column(Text, nullable=False)
    examples_json: Mapped[str] = mapped_column(Text, nullable=False)
    reference_solution: Mapped[str] = mapped_column(Text, nullable=False)
    grading_rubric_json: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    answer: Mapped["CompetitiveAnswer | None"] = relationship(
        "CompetitiveAnswer",
        back_populates="session",
        uselist=False,
    )


class CompetitiveAnswer(Base):
    __tablename__ = "competitive_answers"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    session_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("competitive_sessions.id"),
        nullable=False,
        unique=True,
    )
    answer_text: Mapped[str] = mapped_column(Text, nullable=False)
    score: Mapped[int] = mapped_column(Integer, nullable=False)
    feedback: Mapped[str] = mapped_column(Text, nullable=False)
    time_complexity: Mapped[str] = mapped_column(String, nullable=False)
    space_complexity: Mapped[str] = mapped_column(String, nullable=False)
    improvement_suggestions: Mapped[str] = mapped_column(Text, nullable=False)
    rubric_scores_json: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    session: Mapped["CompetitiveSession"] = relationship(
        "CompetitiveSession",
        back_populates="answer",
    )


class SqlDojoSession(Base):
    __tablename__ = "sql_dojo_sessions"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    theme_family: Mapped[str] = mapped_column(String, nullable=False)
    difficulty: Mapped[str] = mapped_column(String, nullable=False)
    dialect: Mapped[str] = mapped_column(String, nullable=False)
    theme_title: Mapped[str] = mapped_column(String, nullable=False)
    business_domain: Mapped[str] = mapped_column(String, nullable=False)
    target_skill: Mapped[str] = mapped_column(String, nullable=False)
    problem_statement: Mapped[str] = mapped_column(Text, nullable=False)
    schema_markdown: Mapped[str] = mapped_column(Text, nullable=False)
    sample_data_json: Mapped[str] = mapped_column(Text, nullable=False)
    expected_focus: Mapped[str] = mapped_column(Text, nullable=False)
    reference_sql: Mapped[str] = mapped_column(Text, nullable=False)
    grading_contract_json: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    answer: Mapped["SqlDojoAnswer | None"] = relationship(
        "SqlDojoAnswer",
        back_populates="session",
        uselist=False,
    )


class SqlDojoAnswer(Base):
    __tablename__ = "sql_dojo_answers"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    session_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("sql_dojo_sessions.id"),
        nullable=False,
        unique=True,
    )
    answer_text: Mapped[str] = mapped_column(Text, nullable=False)
    score: Mapped[int] = mapped_column(Integer, nullable=False)
    feedback: Mapped[str] = mapped_column(Text, nullable=False)
    rule_breakdown_json: Mapped[str] = mapped_column(Text, nullable=False)
    improvement_suggestions: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    session: Mapped["SqlDojoSession"] = relationship(
        "SqlDojoSession",
        back_populates="answer",
    )


class AlgoThemeModel(Base):
    __tablename__ = "algo_themes"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    category: Mapped[str] = mapped_column(String, nullable=False)
    label: Mapped[str] = mapped_column(String, nullable=False)
    display_order: Mapped[int] = mapped_column(Integer, nullable=False)


class DiffSnapshot(Base):
    __tablename__ = "diff_snapshots"

    snapshot_key: Mapped[str] = mapped_column(String, primary_key=True)
    files_json: Mapped[str] = mapped_column(Text, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
