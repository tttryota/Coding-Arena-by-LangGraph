"""競プロクイズセッションの SQLAlchemy concrete 実装。"""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy import select
from sqlalchemy.orm import Session

from infrastructure.rdb.models import CompetitiveAnswer, CompetitiveSession

if TYPE_CHECKING:
    from sqlalchemy import Engine

    from competitive.domain.competitive_types import (
        ProblemExample,
        RubricItem,
    )


@dataclass(frozen=True)
class CompetitiveSessionRecord:
    id: str
    theme_id: str
    theme_label: str
    theme_category: str
    programming_language: str
    status: str


@dataclass(frozen=True)
class CompetitiveAnswerRecord:
    id: str
    session_id: str
    answer_text: str
    score: int
    feedback: str
    time_complexity: str
    space_complexity: str
    improvement_suggestions: str
    rubric_scores_json: str


class SqlCompetitiveStore:
    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def create_session(  # noqa: PLR0913
        self,
        *,
        theme_id: str,
        theme_label: str,
        theme_category: str,
        programming_language: str,
        problem_statement: str,
        input_format: str,
        output_format: str,
        constraints: str,
        examples: list[ProblemExample],
        reference_solution: str,
        grading_rubric: list[RubricItem],
    ) -> CompetitiveSessionRecord:
        session_id = uuid.uuid4()
        with Session(self._engine) as s, s.begin():
            row = CompetitiveSession(
                id=session_id,
                theme_id=theme_id,
                theme_label=theme_label,
                theme_category=theme_category,
                programming_language=programming_language,
                problem_statement=problem_statement,
                input_format=input_format,
                output_format=output_format,
                constraints=constraints,
                examples_json=json.dumps(examples, ensure_ascii=False),
                reference_solution=reference_solution,
                grading_rubric_json=json.dumps(
                    grading_rubric, ensure_ascii=False,
                ),
                status="in_progress",
                created_at=datetime.now(tz=UTC),
                completed_at=None,
            )
            s.add(row)
        return CompetitiveSessionRecord(
            id=str(session_id),
            theme_id=theme_id,
            theme_label=theme_label,
            theme_category=theme_category,
            programming_language=programming_language,
            status="in_progress",
        )

    def find_session(self, session_id: str) -> CompetitiveSessionRecord:
        with Session(self._engine) as s:
            row = s.get(CompetitiveSession, uuid.UUID(session_id))
            if row is None:
                msg = f"CompetitiveSession not found: {session_id}"
                raise ValueError(msg)
            return CompetitiveSessionRecord(
                id=str(row.id),
                theme_id=row.theme_id,
                theme_label=row.theme_label,
                theme_category=row.theme_category,
                programming_language=row.programming_language,
                status=row.status,
            )

    def get_session_details(
        self, session_id: str,
    ) -> dict[str, object]:
        """セッションの全詳細を返す(内部用)。

        reference_solution / grading_rubric を含むため、
        外部公開 API にはそのまま流さないこと。
        公開用レスポンスの組み立ては API 層で行う。
        """
        with Session(self._engine) as s:
            row = s.get(CompetitiveSession, uuid.UUID(session_id))
            if row is None:
                msg = f"CompetitiveSession not found: {session_id}"
                raise ValueError(msg)
            return {
                "id": str(row.id),
                "theme_id": row.theme_id,
                "theme_label": row.theme_label,
                "theme_category": row.theme_category,
                "programming_language": row.programming_language,
                "problem_statement": row.problem_statement,
                "input_format": row.input_format,
                "output_format": row.output_format,
                "constraints": row.constraints,
                "examples": json.loads(row.examples_json),
                "reference_solution": row.reference_solution,
                "grading_rubric": json.loads(row.grading_rubric_json),
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
        time_complexity: str,
        space_complexity: str,
        improvement_suggestions: str,
        rubric_scores_json: str,
    ) -> CompetitiveAnswerRecord:
        """回答保存とセッション完了を原子的に行う。"""
        answer_id = uuid.uuid4()
        session_uuid = uuid.UUID(session_id)
        now = datetime.now(tz=UTC)
        with Session(self._engine) as s, s.begin():
            cs = s.get(CompetitiveSession, session_uuid)
            if cs is None:
                msg = f"CompetitiveSession not found: {session_id}"
                raise ValueError(msg)
            row = CompetitiveAnswer(
                id=answer_id,
                session_id=session_uuid,
                answer_text=answer_text,
                score=score,
                feedback=feedback,
                time_complexity=time_complexity,
                space_complexity=space_complexity,
                improvement_suggestions=improvement_suggestions,
                rubric_scores_json=rubric_scores_json,
                created_at=now,
            )
            s.add(row)
            cs.status = "completed"
            cs.completed_at = now
        return CompetitiveAnswerRecord(
            id=str(answer_id),
            session_id=session_id,
            answer_text=answer_text,
            score=score,
            feedback=feedback,
            time_complexity=time_complexity,
            space_complexity=space_complexity,
            improvement_suggestions=improvement_suggestions,
            rubric_scores_json=rubric_scores_json,
        )

    def find_answer_by_session(
        self, session_id: str,
    ) -> CompetitiveAnswerRecord | None:
        stmt = (
            select(CompetitiveAnswer)
            .where(CompetitiveAnswer.session_id == uuid.UUID(session_id))
            .order_by(CompetitiveAnswer.created_at.desc())
        )
        with Session(self._engine) as s:
            row = s.execute(stmt).scalars().first()
            if row is None:
                return None
            return CompetitiveAnswerRecord(
                id=str(row.id),
                session_id=str(row.session_id),
                answer_text=row.answer_text,
                score=row.score,
                feedback=row.feedback,
                time_complexity=row.time_complexity,
                space_complexity=row.space_complexity,
                improvement_suggestions=row.improvement_suggestions,
                rubric_scores_json=row.rubric_scores_json,
            )

    def list_recent_sessions(
        self, *, limit: int = 20,
    ) -> list[CompetitiveSessionRecord]:
        stmt = (
            select(CompetitiveSession)
            .order_by(CompetitiveSession.created_at.desc())
            .limit(limit)
        )
        with Session(self._engine) as s:
            rows = s.execute(stmt).scalars().all()
            return [
                CompetitiveSessionRecord(
                    id=str(row.id),
                    theme_id=row.theme_id,
                    theme_label=row.theme_label,
                    theme_category=row.theme_category,
                    programming_language=row.programming_language,
                    status=row.status,
                )
                for row in rows
            ]


__all__ = [
    "CompetitiveAnswerRecord",
    "CompetitiveSessionRecord",
    "SqlCompetitiveStore",
]
