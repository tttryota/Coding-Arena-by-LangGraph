from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Literal, Protocol

if TYPE_CHECKING:
    from uuid import UUID


RoadmapItemLevel = Literal["major", "middle", "detail"]


class RoadmapItemCrudError(Exception):
    pass


class RoadmapItemCrudInputError(RoadmapItemCrudError):
    pass


class RoadmapItemCrudNotFoundError(RoadmapItemCrudError):
    pass


class RoadmapItemCrudStoreError(RoadmapItemCrudError):
    pass


@dataclass(frozen=True)
class RoadmapItemAddInput:
    roadmap_id: UUID
    parent_id: UUID | None
    title: str
    description: str
    order: int | None


@dataclass(frozen=True)
class RoadmapItemMoveInput:
    roadmap_id: UUID
    item_id: UUID
    target_parent_id: UUID | None
    target_order: int


@dataclass(frozen=True)
class RoadmapItemDeleteInput:
    roadmap_id: UUID
    item_id: UUID


@dataclass(frozen=True)
class RoadmapItemCrudItem:
    id: UUID
    roadmap_id: UUID
    parent_id: UUID | None
    level: RoadmapItemLevel
    title: str
    description: str
    order: int
    score: int


@dataclass(frozen=True)
class RoadmapItemCrudRoadmapRecord:
    roadmap_id: UUID
    items: list[RoadmapItemCrudItem]


@dataclass(frozen=True)
class RoadmapItemAddResult:
    created_item: RoadmapItemCrudItem


@dataclass(frozen=True)
class RoadmapItemMoveResult:
    moved_item: RoadmapItemCrudItem


@dataclass(frozen=True)
class RoadmapItemDeleteResult:
    deleted_item_ids: tuple[UUID, ...]
    deleted_count: int


class RoadmapItemCrudStore(Protocol):
    def find_roadmap(self, roadmap_id: UUID) -> RoadmapItemCrudRoadmapRecord | None: ...

    def find_item(self, item_id: UUID) -> RoadmapItemCrudItem | None: ...

    def replace_items(
        self,
        roadmap_id: UUID,
        items: list[RoadmapItemCrudItem],
    ) -> None: ...


class RoadmapItemIdGenerator(Protocol):
    def generate(self) -> UUID: ...


__all__ = [
    "RoadmapItemAddInput",
    "RoadmapItemAddResult",
    "RoadmapItemCrudInputError",
    "RoadmapItemCrudItem",
    "RoadmapItemCrudNotFoundError",
    "RoadmapItemCrudRoadmapRecord",
    "RoadmapItemCrudStore",
    "RoadmapItemCrudStoreError",
    "RoadmapItemDeleteInput",
    "RoadmapItemDeleteResult",
    "RoadmapItemIdGenerator",
    "RoadmapItemLevel",
    "RoadmapItemMoveInput",
    "RoadmapItemMoveResult",
]
