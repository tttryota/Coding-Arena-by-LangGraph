from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import TYPE_CHECKING

import structlog

from roadmap.infrastructure.roadmap_persistence_types import (
    FlatRoadmapItem,
    RoadmapIdGenerator,
    RoadmapItemInput,
    RoadmapLevel,
    RoadmapPersistenceInputError,
    RoadmapPersistenceWriteError,
    RoadmapPersistenceWriter,
    RoadmapSaveInput,
    RoadmapSaveResult,
)

if TYPE_CHECKING:
    from uuid import UUID


logger = structlog.get_logger(__name__)
EVENT_PERSISTED = "roadmap_persisted"
EVENT_PERSIST_FAILED = "roadmap_persistence_failed"
MAJOR_LEVEL: RoadmapLevel = "major"
MIDDLE_LEVEL: RoadmapLevel = "middle"
DETAIL_LEVEL: RoadmapLevel = "detail"
ROOT_LEVEL: RoadmapLevel = MAJOR_LEVEL
INITIAL_SCORE = 0
_ALLOWED_CHILD_LEVELS: dict[RoadmapLevel, RoadmapLevel | None] = {
    MAJOR_LEVEL: MIDDLE_LEVEL,
    MIDDLE_LEVEL: DETAIL_LEVEL,
    DETAIL_LEVEL: None,
}


@dataclass(frozen=True)
class _FlattenContext:
    roadmap_id: UUID
    id_generator: RoadmapIdGenerator
    created_at: str


def save_roadmap(
    roadmap_input: RoadmapSaveInput,
    *,
    writer: RoadmapPersistenceWriter,
    id_generator: RoadmapIdGenerator,
) -> RoadmapSaveResult:
    _validate_input(roadmap_input)

    roadmap_id = id_generator.generate()
    flat_items = _flatten_items(
        roadmap_input.items,
        parent_id=None,
        context=_FlattenContext(
            roadmap_id=roadmap_id,
            id_generator=id_generator,
            created_at=roadmap_input.created_at,
        ),
    )

    try:
        writer.save_items(roadmap_id, roadmap_input.topic, flat_items)
    except Exception as exception:
        logger.exception(
            EVENT_PERSIST_FAILED,
            topic=roadmap_input.topic,
            error_type=type(exception).__name__,
        )
        message = (
            "roadmap persistence failed: "
            f"topic={roadmap_input.topic!r}, item_count={len(flat_items)}"
        )
        raise RoadmapPersistenceWriteError(message) from exception

    logger.info(
        EVENT_PERSISTED,
        roadmap_id=roadmap_id,
        topic=roadmap_input.topic,
        saved_count=len(flat_items),
    )
    return RoadmapSaveResult(roadmap_id=roadmap_id, saved_count=len(flat_items))


def _validate_input(roadmap_input: RoadmapSaveInput) -> None:
    if roadmap_input.topic.strip() == "":
        message = f"topic must be non-blank: got {roadmap_input.topic!r}"
        raise RoadmapPersistenceInputError(message)
    _validate_created_at(roadmap_input.created_at)
    for index, item in enumerate(roadmap_input.items):
        _validate_item(item, expected_level=ROOT_LEVEL, path=f"items[{index}]")


def _validate_created_at(created_at: str) -> None:
    try:
        parsed = datetime.fromisoformat(created_at)
    except ValueError as exception:
        message = (
            "created_at must be a valid ISO 8601 string with UTC offset: "
            f"got {created_at!r}"
        )
        raise RoadmapPersistenceInputError(message) from exception
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        message = f"created_at must include a UTC offset: got {created_at!r}"
        raise RoadmapPersistenceInputError(message)


def _validate_item(
    item: RoadmapItemInput,
    *,
    expected_level: RoadmapLevel,
    path: str,
) -> None:
    if item.title.strip() == "":
        message = f"title must be non-blank at {path}: got {item.title!r}"
        raise RoadmapPersistenceInputError(message)
    if item.level not in _ALLOWED_CHILD_LEVELS:
        message = f"level is unsupported at {path}: got {item.level!r}"
        raise RoadmapPersistenceInputError(message)
    if item.level != expected_level:
        message = (
            f"level relationship is invalid at {path}: "
            f"expected {expected_level!r}, got {item.level!r}"
        )
        raise RoadmapPersistenceInputError(message)
    if item.level == DETAIL_LEVEL:
        if item.children != []:
            message = (
                f"children must be empty for {DETAIL_LEVEL!r} items at {path}: "
                f"got {len(item.children)} child(ren)"
            )
            raise RoadmapPersistenceInputError(message)
        return
    next_level = _ALLOWED_CHILD_LEVELS[item.level]
    if next_level is None:
        message = f"next level must exist for non-detail level: {item.level!r}"
        raise AssertionError(message)
    for index, child in enumerate(item.children):
        _validate_item(
            child,
            expected_level=next_level,
            path=f"{path}.children[{index}]",
        )


def _flatten_items(
    items: list[RoadmapItemInput],
    parent_id: UUID | None,
    context: _FlattenContext,
) -> list[FlatRoadmapItem]:
    flat_items: list[FlatRoadmapItem] = []
    for order, item in enumerate(items):
        item_id = context.id_generator.generate()
        flat_items.append(
            FlatRoadmapItem(
                id=item_id,
                roadmap_id=context.roadmap_id,
                parent_id=parent_id,
                level=item.level,
                title=item.title,
                description=item.description,
                order=order,
                score=INITIAL_SCORE,
                created_at=context.created_at,
                updated_at=context.created_at,
            ),
        )
        flat_items.extend(
            _flatten_items(
                item.children,
                parent_id=item_id,
                context=context,
            ),
        )
    return flat_items


__all__ = ["save_roadmap"]
