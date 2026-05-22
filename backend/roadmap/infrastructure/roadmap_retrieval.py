from __future__ import annotations

from typing import TYPE_CHECKING

import structlog

from roadmap.domain.roadmap_retrieval_types import (
    RoadmapItemRecord,
    RoadmapListItem,
    RoadmapListResult,
    RoadmapRecord,
    RoadmapRetrievalNotFoundError,
    RoadmapRetrievalReader,
    RoadmapRetrievalStoreError,
    RoadmapTree,
    RoadmapTreeNode,
)

if TYPE_CHECKING:
    from uuid import UUID

logger = structlog.get_logger(__name__)
EVENT_STORE_FAILED = "roadmap_retrieval_store_failed"
EVENT_NOT_FOUND = "roadmap_not_found"
EVENT_RETRIEVED = "roadmap_retrieved"
EVENT_LIST_RETRIEVED = "roadmap_list_retrieved"
__all__ = ["get_roadmap", "list_roadmaps"]


def _floor_average(scores: list[int]) -> int:
    if not scores:
        return 0
    return sum(scores) // len(scores)


def _group_children_by_parent(
    record: RoadmapRecord,
) -> dict[UUID | None, list[RoadmapItemRecord]]:
    grouped_children: dict[UUID | None, list[RoadmapItemRecord]] = {}
    for item in record.items:
        grouped_children.setdefault(item.parent_id, []).append(item)

    for siblings in grouped_children.values():
        siblings.sort(key=lambda item: item.order)

    return grouped_children


def _build_node(
    item: RoadmapItemRecord,
    grouped_children: dict[UUID | None, list[RoadmapItemRecord]],
) -> RoadmapTreeNode:
    child_records = grouped_children.get(item.id, [])
    children = [_build_node(child, grouped_children) for child in child_records]

    if item.level == "detail":
        score = item.score
        last_quiz_at = item.last_quiz_at
    else:
        score = _floor_average([child.score for child in children])
        last_quiz_at = None

    return RoadmapTreeNode(
        id=item.id,
        title=item.title,
        description=item.description,
        level=item.level,
        score=score,
        order=item.order,
        children=children,
        last_quiz_at=last_quiz_at,
    )


def _build_tree(record: RoadmapRecord) -> RoadmapTree:
    grouped_children = _group_children_by_parent(record)
    major_items = grouped_children.get(None, [])
    nodes = [_build_node(item, grouped_children) for item in major_items]
    overall_score = _floor_average([node.score for node in nodes])
    return RoadmapTree(
        roadmap_id=record.roadmap_id,
        topic=record.topic,
        overall_score=overall_score,
        items=nodes,
    )


def get_roadmap(
    roadmap_id: UUID,
    *,
    reader: RoadmapRetrievalReader,
) -> RoadmapTree:
    try:
        record = reader.find_roadmap(roadmap_id)
    except Exception as exception:
        logger.exception(
            EVENT_STORE_FAILED,
            roadmap_id=str(roadmap_id),
            error_type=type(exception).__name__,
        )
        if isinstance(exception, RoadmapRetrievalStoreError):
            raise
        message = f"reader.find_roadmap failed: {exception}"
        raise RoadmapRetrievalStoreError(message) from exception

    if record is None:
        logger.warning(EVENT_NOT_FOUND, roadmap_id=str(roadmap_id))
        message = f"roadmap not found: {roadmap_id}"
        raise RoadmapRetrievalNotFoundError(message)

    result = _build_tree(record)
    logger.info(
        EVENT_RETRIEVED,
        roadmap_id=str(result.roadmap_id),
        topic=result.topic,
        overall_score=result.overall_score,
        item_count=len(record.items),
    )
    return result


def list_roadmaps(*, reader: RoadmapRetrievalReader) -> RoadmapListResult:
    try:
        records = reader.find_all_roadmaps()
    except Exception as exception:
        logger.exception(
            EVENT_STORE_FAILED,
            error_type=type(exception).__name__,
        )
        if isinstance(exception, RoadmapRetrievalStoreError):
            raise
        message = f"reader.find_all_roadmaps failed: {exception}"
        raise RoadmapRetrievalStoreError(message) from exception

    items = [
        RoadmapListItem(
            roadmap_id=record.roadmap_id,
            topic=record.topic,
            overall_score=_build_tree(record).overall_score,
        )
        for record in records
    ]
    result = RoadmapListResult(items=items, total_count=len(items))
    logger.info(EVENT_LIST_RETRIEVED, total_count=result.total_count)
    return result
