"""RoadmapPersistenceWriter Protocol の SQLAlchemy concrete 実装。"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy.orm import Session

from infrastructure.rdb.models import Roadmap, RoadmapItem

if TYPE_CHECKING:
    from uuid import UUID

    from sqlalchemy import Engine

    from roadmap.domain.roadmap_persistence_types import FlatRoadmapItem


class SqlRoadmapPersistenceWriter:
    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def save_items(
        self,
        roadmap_id: UUID,
        topic: str,
        items: list[FlatRoadmapItem],
    ) -> None:
        with Session(self._engine) as s, s.begin():
            roadmap = Roadmap(
                id=roadmap_id,
                topic=topic,
                created_at=datetime.fromisoformat(items[0].created_at) if items else datetime.now(tz=UTC),
            )
            s.add(roadmap)
            s.flush()

            for item in items:
                row = RoadmapItem(
                    id=item.id,
                    roadmap_id=item.roadmap_id,
                    parent_id=item.parent_id,
                    level=item.level,
                    title=item.title,
                    description=item.description,
                    order=item.order,
                    score=item.score,
                    created_at=datetime.fromisoformat(item.created_at),
                    updated_at=datetime.fromisoformat(item.updated_at),
                )
                s.add(row)


__all__ = ["SqlRoadmapPersistenceWriter"]
