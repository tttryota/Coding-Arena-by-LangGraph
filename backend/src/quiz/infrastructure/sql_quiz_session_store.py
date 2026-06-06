"""QuizSessionStore Protocol の SQLAlchemy concrete 実装。"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy import select
from sqlalchemy.orm import Session

from infrastructure.rdb.models import QuizSession

if TYPE_CHECKING:
    from sqlalchemy import Engine


@dataclass(frozen=True)
class QuizSessionRecord:
    id: str
    roadmap_item_id: str


class SqlQuizSessionStore:
    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def create_session(self, roadmap_item_id: str) -> QuizSessionRecord:
        session_id = uuid.uuid4()
        with Session(self._engine) as s, s.begin():
            row = QuizSession(
                id=session_id,
                roadmap_item_id=uuid.UUID(roadmap_item_id),
                status="in_progress",
                started_at=datetime.now(tz=UTC),
                completed_at=None,
            )
            s.add(row)
        return QuizSessionRecord(
            id=str(session_id),
            roadmap_item_id=roadmap_item_id,
        )

    def find_in_progress_by_item(
        self,
        roadmap_item_id: str,
    ) -> QuizSessionRecord | None:
        stmt = (
            select(QuizSession)
            .where(
                QuizSession.roadmap_item_id == uuid.UUID(roadmap_item_id),
                QuizSession.status == "in_progress",
            )
            .order_by(QuizSession.started_at.desc())
        )
        with Session(self._engine) as s:
            row = s.execute(stmt).scalars().first()
            if row is None:
                return None
            return QuizSessionRecord(
                id=str(row.id),
                roadmap_item_id=str(row.roadmap_item_id),
            )

    def find_session(self, session_id: str) -> QuizSessionRecord:
        with Session(self._engine) as s:
            row = s.get(QuizSession, uuid.UUID(session_id))
            if row is None:
                msg = f"QuizSession not found: {session_id}"
                raise ValueError(msg)
            return QuizSessionRecord(
                id=str(row.id),
                roadmap_item_id=str(row.roadmap_item_id),
            )

    def complete_session(
        self,
        session_id: str,
        roadmap_item_id: str,  # noqa: ARG002 — score 保存は ProgressUpdateStore が担当
        score: int,  # noqa: ARG002 — score 保存は ProgressUpdateStore が担当
        completed_at: str,
    ) -> None:
        with Session(self._engine) as s, s.begin():
            row = s.get(QuizSession, uuid.UUID(session_id))
            if row is None:
                msg = f"QuizSession not found: {session_id}"
                raise ValueError(msg)
            row.status = "completed"
            row.completed_at = datetime.fromisoformat(completed_at)

    def discard_session(self, session_id: str) -> None:
        with Session(self._engine) as s, s.begin():
            row = s.get(QuizSession, uuid.UUID(session_id))
            if row is None:
                msg = f"QuizSession not found: {session_id}"
                raise ValueError(msg)
            row.status = "discarded"


__all__ = ["QuizSessionRecord", "SqlQuizSessionStore"]
