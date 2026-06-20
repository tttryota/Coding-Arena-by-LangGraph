"""SQL道場セッションの SQLAlchemy concrete 実装。"""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import TYPE_CHECKING, cast

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from infrastructure.rdb.models import SqlDojoAnswer, SqlDojoSession

if TYPE_CHECKING:
    from sqlalchemy import Engine

    from sql_dojo.domain.sql_dojo_types import SqlDojoGradingContract


@dataclass(frozen=True)
class SqlDojoSessionRecord:
    id: str
    theme_family: str
    topic_id: str | None
    topic_title: str | None
    difficulty: str
    dialect: str
    theme_title: str
    status: str


@dataclass(frozen=True)
class SqlDojoAnswerRecord:
    session_id: str
    answer_text: str
    score: int
    feedback: str
    rule_breakdown_json: str
    improvement_suggestions: str


@dataclass(frozen=True)
class SqlDojoThemeHistoryRecord:
    theme_family: str
    attempt_count: int
    best_score: int | None
    last_attempted_at: str | None


@dataclass(frozen=True)
class SqlDojoTopicHistoryRecord:
    topic_id: str
    attempt_count: int
    best_score: int | None
    last_attempted_at: str | None


class SqlSqlDojoStore:
    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def create_session(  # noqa: PLR0913
        self,
        *,
        session_id: str | None = None,
        theme_family: str,
        topic_id: str | None = None,
        topic_title: str | None = None,
        difficulty: str,
        dialect: str,
        theme_title: str,
        business_domain: str,
        target_skill: str,
        problem_statement: str,
        schema_markdown: str,
        sample_data_json: str,
        expected_focus: str,
        reference_sql: str,
        grading_contract_json: str,
    ) -> SqlDojoSessionRecord:
        sid = uuid.UUID(session_id) if session_id else uuid.uuid4()
        with Session(self._engine) as s, s.begin():
            row = SqlDojoSession(
                id=sid,
                theme_family=theme_family,
                topic_id=topic_id,
                topic_title=topic_title,
                difficulty=difficulty,
                dialect=dialect,
                theme_title=theme_title,
                business_domain=business_domain,
                target_skill=target_skill,
                problem_statement=problem_statement,
                schema_markdown=schema_markdown,
                sample_data_json=sample_data_json,
                expected_focus=expected_focus,
                reference_sql=reference_sql,
                grading_contract_json=grading_contract_json,
                status="in_progress",
                created_at=datetime.now(tz=UTC),
                completed_at=None,
            )
            s.add(row)
        return SqlDojoSessionRecord(
            id=str(sid),
            theme_family=theme_family,
            topic_id=topic_id,
            topic_title=topic_title,
            difficulty=difficulty,
            dialect=dialect,
            theme_title=theme_title,
            status="in_progress",
        )

    def get_session_details(self, session_id: str) -> dict[str, object]:
        with Session(self._engine) as s:
            row = s.get(SqlDojoSession, uuid.UUID(session_id))
            if row is None:
                msg = f"SqlDojoSession not found: {session_id}"
                raise ValueError(msg)
            return {
                "session_id": str(row.id),
                "theme_family": row.theme_family,
                "topic_id": row.topic_id,
                "topic_title": row.topic_title,
                "difficulty": row.difficulty,
                "dialect": row.dialect,
                "theme_title": row.theme_title,
                "business_domain": row.business_domain,
                "target_skill": row.target_skill,
                "problem_statement": row.problem_statement,
                "schema_markdown": row.schema_markdown,
                "sample_data_json": row.sample_data_json,
                "expected_focus": row.expected_focus,
                "reference_sql": row.reference_sql,
                "grading_contract_json": row.grading_contract_json,
                "status": row.status,
                "created_at": row.created_at.isoformat(),
            }

    def save_answer_and_complete(  # noqa: PLR0913
        self,
        *,
        session_id: str,
        answer_text: str,
        score: int,
        feedback: str,
        rule_breakdown_json: str,
        improvement_suggestions: str,
    ) -> SqlDojoAnswerRecord:
        session_uuid = uuid.UUID(session_id)
        now = datetime.now(tz=UTC)
        with Session(self._engine) as s, s.begin():
            session = s.get(SqlDojoSession, session_uuid)
            if session is None:
                msg = f"SqlDojoSession not found: {session_id}"
                raise ValueError(msg)
            answer = SqlDojoAnswer(
                id=uuid.uuid4(),
                session_id=session_uuid,
                answer_text=answer_text,
                score=score,
                feedback=feedback,
                rule_breakdown_json=rule_breakdown_json,
                improvement_suggestions=improvement_suggestions,
                created_at=now,
            )
            s.add(answer)
            session.status = "completed"
            session.completed_at = now
        return SqlDojoAnswerRecord(
            session_id=session_id,
            answer_text=answer_text,
            score=score,
            feedback=feedback,
            rule_breakdown_json=rule_breakdown_json,
            improvement_suggestions=improvement_suggestions,
        )

    def find_answer_by_session(self, session_id: str) -> SqlDojoAnswerRecord | None:
        stmt = (
            select(SqlDojoAnswer)
            .where(SqlDojoAnswer.session_id == uuid.UUID(session_id))
            .order_by(SqlDojoAnswer.created_at.desc())
        )
        with Session(self._engine) as s:
            row = s.execute(stmt).scalars().first()
            if row is None:
                return None
            return SqlDojoAnswerRecord(
                session_id=str(row.session_id),
                answer_text=row.answer_text,
                score=row.score,
                feedback=row.feedback,
                rule_breakdown_json=row.rule_breakdown_json,
                improvement_suggestions=row.improvement_suggestions,
            )

    def list_recent_sessions(self, *, limit: int = 50) -> list[SqlDojoSessionRecord]:
        stmt = (
            select(SqlDojoSession)
            .order_by(SqlDojoSession.created_at.desc())
            .limit(limit)
        )
        with Session(self._engine) as s:
            rows = s.execute(stmt).scalars().all()
            return [
                SqlDojoSessionRecord(
                    id=str(row.id),
                    theme_family=row.theme_family,
                    topic_id=row.topic_id,
                    topic_title=row.topic_title,
                    difficulty=row.difficulty,
                    dialect=row.dialect,
                    theme_title=row.theme_title,
                    status=row.status,
                )
                for row in rows
            ]

    def list_topic_history(self) -> list[SqlDojoTopicHistoryRecord]:
        stmt = (
            select(
                SqlDojoSession.topic_id,
                func.count(SqlDojoSession.id).label("attempt_count"),
                func.max(SqlDojoAnswer.score).label("best_score"),
                func.max(SqlDojoSession.created_at).label("last_attempted_at"),
            )
            .outerjoin(
                SqlDojoAnswer,
                SqlDojoAnswer.session_id == SqlDojoSession.id,
            )
            .where(SqlDojoSession.topic_id.is_not(None))
            .group_by(SqlDojoSession.topic_id)
        )
        with Session(self._engine) as s:
            rows = s.execute(stmt).all()
            return [
                SqlDojoTopicHistoryRecord(
                    topic_id=row.topic_id,
                    attempt_count=row.attempt_count,
                    best_score=row.best_score,
                    last_attempted_at=(
                        row.last_attempted_at.isoformat()
                        if row.last_attempted_at
                        else None
                    ),
                )
                for row in rows
            ]

    def list_theme_history(self) -> list[SqlDojoThemeHistoryRecord]:
        stmt = (
            select(
                SqlDojoSession.theme_family,
                func.count(SqlDojoSession.id).label("attempt_count"),
                func.max(SqlDojoAnswer.score).label("best_score"),
                func.max(SqlDojoSession.created_at).label("last_attempted_at"),
            )
            .outerjoin(
                SqlDojoAnswer,
                SqlDojoAnswer.session_id == SqlDojoSession.id,
            )
            .group_by(SqlDojoSession.theme_family)
        )
        with Session(self._engine) as s:
            rows = s.execute(stmt).all()
            return [
                SqlDojoThemeHistoryRecord(
                    theme_family=row.theme_family,
                    attempt_count=row.attempt_count,
                    best_score=row.best_score,
                    last_attempted_at=(
                        row.last_attempted_at.isoformat()
                        if row.last_attempted_at
                        else None
                    ),
                )
                for row in rows
            ]

    @staticmethod
    def grading_contract_as_dict(details: dict[str, object]) -> SqlDojoGradingContract:
        return cast(
            "SqlDojoGradingContract",
            json.loads(str(details["grading_contract_json"])),
        )


__all__ = [
    "SqlDojoAnswerRecord",
    "SqlDojoSessionRecord",
    "SqlDojoThemeHistoryRecord",
    "SqlDojoTopicHistoryRecord",
    "SqlSqlDojoStore",
]
