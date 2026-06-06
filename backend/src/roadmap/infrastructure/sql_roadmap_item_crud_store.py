"""RoadmapItemCrudStore Protocol の SQLAlchemy concrete 実装。"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from infrastructure.rdb.models import Roadmap, RoadmapItem
from roadmap.domain.roadmap_item_crud_types import (
    RoadmapItemCrudItem,
    RoadmapItemCrudRoadmapRecord,
)

if TYPE_CHECKING:
    from uuid import UUID

    from sqlalchemy import Engine


class SqlRoadmapItemCrudStore:
    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def find_roadmap(
        self,
        roadmap_id: UUID,
    ) -> RoadmapItemCrudRoadmapRecord | None:
        with Session(self._engine) as s:
            roadmap = s.get(Roadmap, roadmap_id)
            if roadmap is None:
                return None
            rows = (
                s.execute(
                    select(RoadmapItem)
                    .where(RoadmapItem.roadmap_id == roadmap_id)
                    .order_by(RoadmapItem.order),
                )
                .scalars()
                .all()
            )
            return RoadmapItemCrudRoadmapRecord(
                roadmap_id=roadmap_id,
                items=[_to_crud_item(row) for row in rows],
            )

    def find_item(self, item_id: UUID) -> RoadmapItemCrudItem | None:
        with Session(self._engine) as s:
            row = s.get(RoadmapItem, item_id)
            if row is None:
                return None
            return _to_crud_item(row)

    def replace_items(
        self,
        roadmap_id: UUID,
        items: list[RoadmapItemCrudItem],
    ) -> None:
        """既存アイテムを全て削除して新しいアイテムで置き換える。

        注意: created_at は RoadmapItemCrudItem に含まれないため、
        全アイテムの created_at が現在時刻にリセットされる。
        """
        now = datetime.now(tz=UTC)
        with Session(self._engine) as s, s.begin():
            # FK 制約安全: 先に parent_id を NULL にしてから削除
            s.execute(
                update(RoadmapItem)
                .where(RoadmapItem.roadmap_id == roadmap_id)
                .values(parent_id=None),
            )
            existing = (
                s.execute(
                    select(RoadmapItem)
                    .where(RoadmapItem.roadmap_id == roadmap_id),
                )
                .scalars()
                .all()
            )
            for row in existing:
                s.delete(row)
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
                    created_at=now,
                    updated_at=now,
                )
                s.add(row)


def _to_crud_item(row: RoadmapItem) -> RoadmapItemCrudItem:
    return RoadmapItemCrudItem(
        id=row.id,
        roadmap_id=row.roadmap_id,
        parent_id=row.parent_id,
        level=row.level,  # type: ignore[arg-type]
        title=row.title,
        description=row.description,
        order=row.order,
        score=row.score,
    )


__all__ = ["SqlRoadmapItemCrudStore"]
