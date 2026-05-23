"""RoadmapItemReader + RoadmapItemExistenceChecker Protocol の SQLAlchemy concrete 実装。"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import TYPE_CHECKING

from sqlalchemy import select
from sqlalchemy.orm import Session

from infrastructure.rdb.models import RoadmapItem

if TYPE_CHECKING:
    from sqlalchemy import Engine


@dataclass(frozen=True)
class RoadmapItemRecord:
    id: str
    level: str
    title: str
    description: str


class SqlRoadmapItemReadStore:
    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def find_item(self, item_id: str) -> RoadmapItemRecord | None:
        with Session(self._engine) as s:
            row = s.get(RoadmapItem, uuid.UUID(item_id))
            if row is None:
                return None
            return RoadmapItemRecord(
                id=str(row.id),
                level=row.level,
                title=row.title,
                description=row.description,
            )

    def item_exists(self, item_id: str) -> bool:
        stmt = select(RoadmapItem.id).where(
            RoadmapItem.id == uuid.UUID(item_id),
        )
        with Session(self._engine) as s:
            return s.execute(stmt).first() is not None


__all__ = ["RoadmapItemRecord", "SqlRoadmapItemReadStore"]
