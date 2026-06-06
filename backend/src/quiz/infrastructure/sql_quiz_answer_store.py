"""QuizAnswerStore Protocol の SQLAlchemy concrete 実装。"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy import select
from sqlalchemy.orm import Session

from infrastructure.rdb.models import QuizAnswer, QuizSession

if TYPE_CHECKING:
    from sqlalchemy import Engine

    from quiz.application.session_lifecycle_types import QuizAnswerRecordLike


@dataclass(frozen=True)
class StoredAnswerRecord:
    question_number: int
    question_text: str
    answer_text: str
    answer_type: str
    score: int
    feedback: str
    confirmation_point_id: str


class SqlQuizAnswerStore:
    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def save_answer(
        self,
        quiz_session_id: str,
        answer: QuizAnswerRecordLike,
    ) -> None:
        session_uuid = uuid.UUID(quiz_session_id)
        with Session(self._engine) as s, s.begin():
            qs = s.get(QuizSession, session_uuid)
            if qs is None:
                msg = f"QuizSession not found: {quiz_session_id}"
                raise ValueError(msg)
            row = QuizAnswer(
                id=uuid.uuid4(),
                session_id=session_uuid,
                roadmap_item_id=qs.roadmap_item_id,
                confirmation_point_id=answer.confirmation_point_id,
                question_number=answer.question_number,
                question_text=answer.question_text,
                answer_type=answer.answer_type,
                answer_text=answer.answer_text,
                score=answer.score,
                feedback=answer.feedback,
                answered_at=datetime.now(tz=UTC),
            )
            s.add(row)

    def find_by_session(
        self,
        session_id: str,
    ) -> list[StoredAnswerRecord]:
        stmt = (
            select(QuizAnswer)
            .where(QuizAnswer.session_id == uuid.UUID(session_id))
            .order_by(QuizAnswer.question_number)
        )
        with Session(self._engine) as s:
            rows = s.execute(stmt).scalars().all()
            return [
                StoredAnswerRecord(
                    question_number=row.question_number,
                    question_text=row.question_text,
                    answer_text=row.answer_text,
                    answer_type=row.answer_type,
                    score=row.score,
                    feedback=row.feedback,
                    confirmation_point_id=row.confirmation_point_id,
                )
                for row in rows
            ]


__all__ = ["SqlQuizAnswerStore", "StoredAnswerRecord"]
