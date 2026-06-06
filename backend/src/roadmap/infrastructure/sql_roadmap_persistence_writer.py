"""RoadmapPersistenceWriter Protocol の SQLAlchemy concrete 実装。"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy.orm import Session

from infrastructure.rdb.models import Roadmap, RoadmapItem

if TYPE_CHECKING:
    from uuid import UUID

    from sqlalchemy import Engine

    from roadmap.domain.roadmap_persistence_types import (
        FlatRoadmapItem,
        RoadmapItemInput,
        RoadmapSaveInput,
        RoadmapSaveResult,
    )


class SqlRoadmapPersistenceWriter:
    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def save_roadmap(self, roadmap_input: RoadmapSaveInput) -> RoadmapSaveResult:
        """RoadmapGenerationPersistencePort.save_roadmap の実装。"""
        from roadmap.domain.roadmap_persistence_types import (
            RoadmapPersistenceWriteError,
            RoadmapSaveResult,
        )

        roadmap_id = uuid.uuid4()
        flat_items: list[FlatRoadmapItem] = []
        self._flatten_items(
            roadmap_input.items,
            roadmap_id=roadmap_id,
            parent_id=None,
            flat_items=flat_items,
            created_at=roadmap_input.created_at,
        )
        try:
            self.save_items(roadmap_id, roadmap_input.topic, flat_items)
        except Exception as exc:
            msg = f"failed to save roadmap: {exc}"
            raise RoadmapPersistenceWriteError(msg) from exc
        return RoadmapSaveResult(
            roadmap_id=roadmap_id,
            saved_count=len(flat_items),
        )

    def _flatten_items(  # noqa: PLR0913
        self,
        items: list[RoadmapItemInput],
        *,
        roadmap_id: uuid.UUID,
        parent_id: uuid.UUID | None,
        flat_items: list[FlatRoadmapItem],
        created_at: str,
    ) -> None:
        from roadmap.domain.roadmap_persistence_types import FlatRoadmapItem

        for order, item in enumerate(items):
            item_id = uuid.uuid4()
            flat_items.append(
                FlatRoadmapItem(
                    id=item_id,
                    roadmap_id=roadmap_id,
                    parent_id=parent_id,
                    level=item.level,
                    title=item.title,
                    description=item.description,
                    order=order,
                    score=0,
                    created_at=created_at,
                    updated_at=created_at,
                ),
            )
            self._flatten_items(
                item.children,
                roadmap_id=roadmap_id,
                parent_id=item_id,
                flat_items=flat_items,
                created_at=created_at,
            )

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
                created_at=datetime.fromisoformat(items[0].created_at)
                if items
                else datetime.now(tz=UTC),
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
