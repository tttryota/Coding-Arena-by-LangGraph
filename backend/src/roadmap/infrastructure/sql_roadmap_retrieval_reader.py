"""RoadmapRetrievalReader Protocol の SQLAlchemy concrete 実装。"""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import select
from sqlalchemy.orm import Session

from infrastructure.rdb.models import Roadmap, RoadmapItem
from roadmap.domain.roadmap_retrieval_types import RoadmapItemRecord, RoadmapRecord

if TYPE_CHECKING:
    from uuid import UUID

    from sqlalchemy import Engine


class SqlRoadmapRetrievalReader:
    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def find_roadmap(self, roadmap_id: UUID) -> RoadmapRecord | None:
        with Session(self._engine) as s:
            roadmap = s.get(Roadmap, roadmap_id)
            if roadmap is None:
                return None
            items = (
                s.execute(
                    select(RoadmapItem)
                    .where(RoadmapItem.roadmap_id == roadmap_id)
                    .order_by(RoadmapItem.order),
                )
                .scalars()
                .all()
            )
            return RoadmapRecord(
                roadmap_id=roadmap.id,
                topic=roadmap.topic,
                items=[_to_item_record(row) for row in items],
            )

    def find_all_roadmaps(self) -> list[RoadmapRecord]:
        # N+1 クエリだが、個人ツールでロードマップ数は少量のため許容
        with Session(self._engine) as s:
            roadmaps = s.execute(select(Roadmap)).scalars().all()
            results = []
            for roadmap in roadmaps:
                items = (
                    s.execute(
                        select(RoadmapItem)
                        .where(RoadmapItem.roadmap_id == roadmap.id)
                        .order_by(RoadmapItem.order),
                    )
                    .scalars()
                    .all()
                )
                results.append(
                    RoadmapRecord(
                        roadmap_id=roadmap.id,
                        topic=roadmap.topic,
                        items=[_to_item_record(row) for row in items],
                    ),
                )
            return results


def _to_item_record(row: RoadmapItem) -> RoadmapItemRecord:
    return RoadmapItemRecord(
        id=row.id,
        parent_id=row.parent_id,
        level=row.level,  # type: ignore[arg-type]
        title=row.title,
        description=row.description,
        order=row.order,
        score=row.score,
        last_quiz_at=row.last_quiz_at.isoformat() if row.last_quiz_at else None,
    )


__all__ = ["SqlRoadmapRetrievalReader"]
