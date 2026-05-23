"""IngestionFeedbackWriter + FeedbackListingReader + FeedbackReadWriter の SQLAlchemy concrete 実装。"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Literal

from sqlalchemy import select
from sqlalchemy.orm import Session

from infrastructure.rdb.models import IngestionFeedback

if TYPE_CHECKING:
    from uuid import UUID

    from sqlalchemy import Engine

    from ingestion.domain.feedback_listing_types import FeedbackListItem
    from ingestion.domain.ingestion_feedback_types import (
        NewIngestionFeedbackRecord,
        StoredIngestionFeedback,
    )


def _parse_naive_dt(iso_str: str) -> datetime:
    """ISO 文字列を timezone-naive datetime に変換。SQLite 互換。"""
    dt = datetime.fromisoformat(iso_str)
    if dt.tzinfo is not None:
        dt = dt.astimezone(UTC).replace(tzinfo=None)
    return dt


class SqlIngestionFeedbackStore:
    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def create(
        self,
        record: NewIngestionFeedbackRecord,
    ) -> StoredIngestionFeedback:
        from ingestion.domain.ingestion_feedback_types import StoredIngestionFeedback

        feedback_id = uuid.uuid4()
        with Session(self._engine) as s, s.begin():
            row = IngestionFeedback(
                id=feedback_id,
                source_path=record.source_path,
                roadmap_item_id=record.roadmap_item_id,
                title=record.title,
                body=record.body,
                is_read=record.is_read,
                created_at=_parse_naive_dt(record.created_at),
                read_at=_parse_naive_dt(record.read_at) if record.read_at else None,
            )
            s.add(row)

        return StoredIngestionFeedback(
            id=feedback_id,
            source_path=record.source_path,
            roadmap_item_id=record.roadmap_item_id,
            title=record.title,
            body=record.body,
            is_read=record.is_read,
            created_at=record.created_at,
            read_at=record.read_at,
        )

    def find_feedbacks(
        self,
        *,
        date_from: str | None,
        date_to: str | None,
        read_status: Literal["all", "unread", "read"],
    ) -> list[FeedbackListItem]:
        stmt = select(IngestionFeedback)

        if date_from is not None:
            stmt = stmt.where(
                IngestionFeedback.created_at >= _parse_naive_dt(date_from),
            )
        if date_to is not None:
            stmt = stmt.where(
                IngestionFeedback.created_at <= _parse_naive_dt(date_to),
            )
        if read_status == "unread":
            stmt = stmt.where(IngestionFeedback.is_read == False)  # noqa: E712
        elif read_status == "read":
            stmt = stmt.where(IngestionFeedback.is_read == True)  # noqa: E712

        stmt = stmt.order_by(IngestionFeedback.created_at.desc())

        with Session(self._engine) as s:
            rows = s.execute(stmt).scalars().all()
            return [_to_feedback_list_item(row) for row in rows]

    def get_by_id(self, feedback_id: UUID) -> FeedbackListItem | None:
        with Session(self._engine) as s:
            row = s.get(IngestionFeedback, feedback_id)
            if row is None:
                return None
            return _to_feedback_list_item(row)

    def update_read_status(
        self,
        feedback_id: UUID,
        *,
        is_read: bool,
        read_at: str,  # Protocol 定義で非 Optional。mark-as-unread は現在未サポート
    ) -> FeedbackListItem:
        with Session(self._engine) as s, s.begin():
            row = s.get(IngestionFeedback, feedback_id)
            if row is None:
                msg = f"IngestionFeedback not found: {feedback_id}"
                raise ValueError(msg)
            row.is_read = is_read
            row.read_at = _parse_naive_dt(read_at)
            s.flush()
            return _to_feedback_list_item(row)


def _to_feedback_list_item(row: IngestionFeedback) -> FeedbackListItem:
    from datetime import UTC

    from ingestion.domain.feedback_listing_types import FeedbackListItem

    created_at = (
        row.created_at.replace(tzinfo=UTC)
        if row.created_at.tzinfo is None
        else row.created_at
    )
    read_at = None
    if row.read_at is not None:
        read_at_dt = (
            row.read_at.replace(tzinfo=UTC)
            if row.read_at.tzinfo is None
            else row.read_at
        )
        read_at = read_at_dt.isoformat()

    return FeedbackListItem(
        id=row.id,
        source_path=row.source_path,
        roadmap_item_id=row.roadmap_item_id,
        title=row.title,
        body=row.body,
        is_read=row.is_read,
        created_at=created_at.isoformat(),
        read_at=read_at,
    )


__all__ = ["SqlIngestionFeedbackStore"]
