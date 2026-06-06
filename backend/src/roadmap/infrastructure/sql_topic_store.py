"""TopicStore Protocol の SQLAlchemy concrete 実装。"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from infrastructure.rdb.models import Topic
from roadmap.domain.topic_listing_types import StoredTopicRecord

if TYPE_CHECKING:
    from sqlalchemy import Engine


class SqlTopicStore:
    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def list_manual_topics(self) -> list[StoredTopicRecord]:
        stmt = (
            select(Topic)
            .where(Topic.source == "manual")
            .order_by(Topic.created_at)
        )
        with Session(self._engine) as s:
            rows = s.execute(stmt).scalars().all()
            return [_to_record(row) for row in rows]

    def find_topic_by_canonical_name(
        self,
        canonical_name: str,
    ) -> StoredTopicRecord | None:
        stmt = select(Topic).where(Topic.canonical_name == canonical_name)
        with Session(self._engine) as s:
            row = s.execute(stmt).scalars().first()
            if row is None:
                return None
            return _to_record(row)

    def create_manual_topic(
        self,
        name: str,
        canonical_name: str,
    ) -> StoredTopicRecord:
        try:
            with Session(self._engine) as s, s.begin():
                row = Topic(
                    id=uuid.uuid4(),
                    name=name,
                    canonical_name=canonical_name,
                    source="manual",
                    created_at=datetime.now(tz=UTC),
                )
                s.add(row)
        except IntegrityError:
            existing = self.find_topic_by_canonical_name(canonical_name)
            if existing is not None:
                return existing
            raise
        return StoredTopicRecord(
            name=name,
            canonical_name=canonical_name,
            source="manual",
        )


def _to_record(row: Topic) -> StoredTopicRecord:
    return StoredTopicRecord(
        name=row.name,
        canonical_name=row.canonical_name,
        source=row.source,  # type: ignore[arg-type]
    )


__all__ = ["SqlTopicStore"]
