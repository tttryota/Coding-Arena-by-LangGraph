"""SummaryTestStore + SummaryTestResultsStore Protocol の SQLAlchemy concrete 実装。"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy import select
from sqlalchemy.orm import Session

from infrastructure.rdb.models import QuizSession, SummaryTestResult
from quiz.application.summary_test_results_types import SummaryTestResultRecord

if TYPE_CHECKING:
    from sqlalchemy import Engine


class SqlSummaryTestResultStore:
    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def save_result(
        self,
        session_id: str,
        roadmap_item_id: str,  # noqa: ARG002 — session_id 経由で roadmap_item を参照
        score: int,
        analysis: str,
    ) -> None:
        with Session(self._engine) as s, s.begin():
            result = SummaryTestResult(
                id=uuid.uuid4(),
                session_id=uuid.UUID(session_id),
                score=score,
                analysis=analysis,
                created_at=datetime.now(tz=UTC),
            )
            s.add(result)

    def find_by_roadmap_item(
        self,
        roadmap_item_id: str,
    ) -> list[SummaryTestResultRecord]:
        stmt = (
            select(SummaryTestResult)
            .join(
                QuizSession,
                SummaryTestResult.session_id == QuizSession.id,
            )
            .where(
                QuizSession.roadmap_item_id == uuid.UUID(roadmap_item_id),
            )
            .order_by(SummaryTestResult.created_at)
        )
        with Session(self._engine) as s:
            rows = s.execute(stmt).scalars().all()
            return [
                SummaryTestResultRecord(
                    id=str(row.id),
                    session_id=str(row.session_id),
                    score=row.score,
                    analysis=row.analysis,
                    created_at=row.created_at.isoformat(),
                )
                for row in rows
            ]


__all__ = ["SqlSummaryTestResultStore"]

