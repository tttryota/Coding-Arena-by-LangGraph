"""ProgressUpdateStore Protocol の SQLAlchemy concrete 実装。"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy.orm import Session

from infrastructure.rdb.models import QuizSession, RoadmapItem, SummaryTestResult

if TYPE_CHECKING:
    from sqlalchemy import Engine


class SqlProgressUpdateStore:
    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def update_roadmap_item_progress(
        self,
        item_id: str,
        score: int,
        last_quiz_at: datetime,
    ) -> None:
        with Session(self._engine) as s, s.begin():
            row = s.get(RoadmapItem, uuid.UUID(item_id))
            if row is None:
                msg = f"RoadmapItem not found: {item_id}"
                raise ValueError(msg)
            row.score = score
            row.last_quiz_at = last_quiz_at
            row.updated_at = datetime.now(tz=UTC)

    def save_summary_test_result(
        self,
        session_id: str,
        item_id: str,  # noqa: ARG002 — session_id 経由で roadmap_item を参照
        score: int,
        comment: str,
    ) -> None:
        """SummaryTestResult を保存する。SqlSummaryTestResultStore.save_result と
        別 Protocol・別ユースケースフロー(progress_update vs summary_test_record)
        のため、意図的に独立した実装を持つ。"""
        with Session(self._engine) as s, s.begin():
            result = SummaryTestResult(
                id=uuid.uuid4(),
                session_id=uuid.UUID(session_id),
                score=score,
                analysis=comment,
                created_at=datetime.now(tz=UTC),
            )
            s.add(result)

    def complete_session(self, session_id: str) -> None:
        with Session(self._engine) as s, s.begin():
            row = s.get(QuizSession, uuid.UUID(session_id))
            if row is None:
                msg = f"QuizSession not found: {session_id}"
                raise ValueError(msg)
            row.status = "completed"
            row.completed_at = datetime.now(tz=UTC)


__all__ = ["SqlProgressUpdateStore"]
