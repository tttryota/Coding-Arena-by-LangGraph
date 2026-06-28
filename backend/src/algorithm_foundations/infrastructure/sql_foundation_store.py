"""競プロうさぎセッションの SQLAlchemy concrete 実装。"""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from infrastructure.rdb.models import (
    AlgorithmFoundationAnswer,
    AlgorithmFoundationSession,
)

if TYPE_CHECKING:
    from sqlalchemy import Engine


@dataclass(frozen=True)
class AlgorithmFoundationSessionRecord:
    id: str
    unit_id: str
    group_id: str
    group_title: str
    unit_title: str
    target_skill: str
    unit_kind: str
    problem_id: str
    problem_title: str
    programming_language: str
    status: str


@dataclass(frozen=True)
class AlgorithmFoundationAnswerRecord:
    session_id: str
    answer_text: str
    score: int
    feedback: str
    time_complexity: str
    space_complexity: str
    improvement_suggestions: str
    rubric_scores_json: str


@dataclass(frozen=True)
class AlgorithmFoundationUnitHistoryRecord:
    unit_id: str
    attempt_count: int
    best_score: int | None
    last_attempted_at: str | None


@dataclass(frozen=True)
class AlgorithmFoundationProblemHistoryRecord:
    unit_id: str
    problem_id: str
    attempt_count: int
    best_score: int | None
    last_attempted_at: str | None


class SqlAlgorithmFoundationStore:
    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def create_session(  # noqa: PLR0913
        self,
        *,
        session_id: str | None = None,
        unit_id: str,
        group_id: str,
        group_title: str,
        unit_title: str,
        target_skill: str,
        unit_kind: str,
        prerequisite_unit_ids: list[str],
        prerequisite_titles: list[str],
        allowed_knowledge: list[str],
        forbidden_knowledge: list[str],
        programming_language: str,
        problem_id: str,
        problem_title: str,
        problem_statement: str,
        input_format: str,
        output_format: str,
        constraints: str,
        examples: list[dict[str, str]],
        reference_solution: str,
        grading_rubric: list[dict[str, object]],
    ) -> AlgorithmFoundationSessionRecord:
        sid = uuid.UUID(session_id) if session_id else uuid.uuid4()
        with Session(self._engine) as s, s.begin():
            row = AlgorithmFoundationSession(
                id=sid,
                unit_id=unit_id,
                group_id=group_id,
                group_title=group_title,
                unit_title=unit_title,
                target_skill=target_skill,
                unit_kind=unit_kind,
                prerequisite_unit_ids_json=json.dumps(prerequisite_unit_ids, ensure_ascii=False),
                prerequisite_titles_json=json.dumps(prerequisite_titles, ensure_ascii=False),
                allowed_knowledge_json=json.dumps(allowed_knowledge, ensure_ascii=False),
                forbidden_knowledge_json=json.dumps(forbidden_knowledge, ensure_ascii=False),
                programming_language=programming_language,
                problem_id=problem_id,
                problem_title=problem_title,
                problem_statement=problem_statement,
                input_format=input_format,
                output_format=output_format,
                constraints=constraints,
                examples_json=json.dumps(examples, ensure_ascii=False),
                reference_solution=reference_solution,
                grading_rubric_json=json.dumps(grading_rubric, ensure_ascii=False),
                status="in_progress",
                created_at=datetime.now(tz=UTC),
                completed_at=None,
            )
            s.add(row)
        return AlgorithmFoundationSessionRecord(
            id=str(sid),
            unit_id=unit_id,
            group_id=group_id,
            group_title=group_title,
            unit_title=unit_title,
            target_skill=target_skill,
            unit_kind=unit_kind,
            problem_id=problem_id,
            problem_title=problem_title,
            programming_language=programming_language,
            status="in_progress",
        )

    def get_session_details(self, session_id: str) -> dict[str, object]:
        with Session(self._engine) as s:
            row = s.get(AlgorithmFoundationSession, uuid.UUID(session_id))
            if row is None:
                msg = f"AlgorithmFoundationSession not found: {session_id}"
                raise ValueError(msg)
            return {
                "session_id": str(row.id),
                "unit_id": row.unit_id,
                "group_id": row.group_id,
                "group_title": row.group_title,
                "unit_title": row.unit_title,
                "target_skill": row.target_skill,
                "unit_kind": row.unit_kind,
                "prerequisite_unit_ids": json.loads(row.prerequisite_unit_ids_json),
                "prerequisite_titles": json.loads(row.prerequisite_titles_json),
                "allowed_knowledge": json.loads(row.allowed_knowledge_json),
                "forbidden_knowledge": json.loads(row.forbidden_knowledge_json),
                "programming_language": row.programming_language,
                "problem_id": row.problem_id,
                "problem_title": row.problem_title,
                "problem_statement": row.problem_statement,
                "input_format": row.input_format,
                "output_format": row.output_format,
                "constraints": row.constraints,
                "examples": json.loads(row.examples_json),
                "reference_solution": row.reference_solution,
                "grading_rubric": json.loads(row.grading_rubric_json),
                "status": row.status,
                "created_at": row.created_at.isoformat(),
                "completed_at": row.completed_at.isoformat() if row.completed_at else None,
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
    ) -> AlgorithmFoundationAnswerRecord:
        session_uuid = uuid.UUID(session_id)
        now = datetime.now(tz=UTC)
        with Session(self._engine) as s, s.begin():
            session = s.get(AlgorithmFoundationSession, session_uuid)
            if session is None:
                msg = f"AlgorithmFoundationSession not found: {session_id}"
                raise ValueError(msg)
            answer = AlgorithmFoundationAnswer(
                id=uuid.uuid4(),
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
            s.add(answer)
            session.status = "completed"
            session.completed_at = now
        return AlgorithmFoundationAnswerRecord(
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
        self,
        session_id: str,
    ) -> AlgorithmFoundationAnswerRecord | None:
        stmt = (
            select(AlgorithmFoundationAnswer)
            .where(AlgorithmFoundationAnswer.session_id == uuid.UUID(session_id))
            .order_by(AlgorithmFoundationAnswer.created_at.desc())
        )
        with Session(self._engine) as s:
            row = s.execute(stmt).scalars().first()
            if row is None:
                return None
            return AlgorithmFoundationAnswerRecord(
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
        self,
        *,
        limit: int = 50,
    ) -> list[AlgorithmFoundationSessionRecord]:
        stmt = (
            select(AlgorithmFoundationSession)
            .join(
                AlgorithmFoundationAnswer,
                AlgorithmFoundationAnswer.session_id == AlgorithmFoundationSession.id,
            )
            .order_by(AlgorithmFoundationAnswer.created_at.desc())
            .limit(limit)
        )
        with Session(self._engine) as s:
            rows = s.execute(stmt).scalars().all()
            return [
                AlgorithmFoundationSessionRecord(
                    id=str(row.id),
                    unit_id=row.unit_id,
                    group_id=row.group_id,
                    group_title=row.group_title,
                    unit_title=row.unit_title,
                    target_skill=row.target_skill,
                    unit_kind=row.unit_kind,
                    problem_id=row.problem_id,
                    problem_title=row.problem_title,
                    programming_language=row.programming_language,
                    status=row.status,
                )
                for row in rows
            ]

    def list_unit_history(self) -> list[AlgorithmFoundationUnitHistoryRecord]:
        stmt = (
            select(
                AlgorithmFoundationSession.unit_id,
                func.count(AlgorithmFoundationAnswer.id).label("attempt_count"),
                func.max(AlgorithmFoundationAnswer.score).label("best_score"),
                func.max(AlgorithmFoundationAnswer.created_at).label("last_attempted_at"),
            )
            .join(
                AlgorithmFoundationAnswer,
                AlgorithmFoundationAnswer.session_id == AlgorithmFoundationSession.id,
            )
            .group_by(AlgorithmFoundationSession.unit_id)
        )
        with Session(self._engine) as s:
            rows = s.execute(stmt).all()
            return [
                AlgorithmFoundationUnitHistoryRecord(
                    unit_id=row.unit_id,
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

    def list_recent_problem_ids_for_unit(
        self,
        unit_id: str,
        *,
        limit: int = 5,
    ) -> list[str]:
        stmt = (
            select(AlgorithmFoundationSession.problem_id)
            .join(
                AlgorithmFoundationAnswer,
                AlgorithmFoundationAnswer.session_id == AlgorithmFoundationSession.id,
            )
            .where(AlgorithmFoundationSession.unit_id == unit_id)
            .order_by(AlgorithmFoundationAnswer.created_at.desc())
            .limit(limit)
        )
        with Session(self._engine) as s:
            rows = s.execute(stmt).scalars().all()
            return list(rows)

    def list_problem_history_for_unit(
        self,
        unit_id: str,
    ) -> list[AlgorithmFoundationProblemHistoryRecord]:
        return self._list_problem_history(unit_id=unit_id)

    def list_problem_history(self) -> list[AlgorithmFoundationProblemHistoryRecord]:
        return self._list_problem_history(unit_id=None)

    def _list_problem_history(
        self,
        *,
        unit_id: str | None,
    ) -> list[AlgorithmFoundationProblemHistoryRecord]:
        stmt = (
            select(
                AlgorithmFoundationSession.unit_id,
                AlgorithmFoundationSession.problem_id,
                func.count(AlgorithmFoundationAnswer.id).label("attempt_count"),
                func.max(AlgorithmFoundationAnswer.score).label("best_score"),
                func.max(AlgorithmFoundationAnswer.created_at).label("last_attempted_at"),
            )
            .join(
                AlgorithmFoundationAnswer,
                AlgorithmFoundationAnswer.session_id == AlgorithmFoundationSession.id,
            )
            .group_by(
                AlgorithmFoundationSession.unit_id,
                AlgorithmFoundationSession.problem_id,
            )
        )
        if unit_id is not None:
            stmt = stmt.where(AlgorithmFoundationSession.unit_id == unit_id)
        with Session(self._engine) as s:
            rows = s.execute(stmt).all()
            return [
                AlgorithmFoundationProblemHistoryRecord(
                    unit_id=row.unit_id,
                    problem_id=row.problem_id,
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


__all__ = [
    "AlgorithmFoundationAnswerRecord",
    "AlgorithmFoundationProblemHistoryRecord",
    "AlgorithmFoundationSessionRecord",
    "AlgorithmFoundationUnitHistoryRecord",
    "SqlAlgorithmFoundationStore",
]
