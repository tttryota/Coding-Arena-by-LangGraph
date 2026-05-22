from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Literal, Protocol

if TYPE_CHECKING:
    from uuid import UUID

RoadmapLevel = Literal["major", "middle", "detail"]


class RoadmapRetrievalError(Exception):
    pass


class RoadmapRetrievalNotFoundError(RoadmapRetrievalError):
    pass


class RoadmapRetrievalStoreError(RoadmapRetrievalError):
    pass


@dataclass(frozen=True)
class RoadmapItemRecord:
    id: UUID
    parent_id: UUID | None
    level: RoadmapLevel
    title: str
    description: str
    order: int
    score: int
    last_quiz_at: str | None


@dataclass(frozen=True)
class RoadmapRecord:
    roadmap_id: UUID
    topic: str
    items: list[RoadmapItemRecord]


@dataclass(frozen=True)
class RoadmapTreeNode:
    id: UUID
    title: str
    description: str
    level: RoadmapLevel
    score: int
    order: int
    children: list[RoadmapTreeNode]
    last_quiz_at: str | None


@dataclass(frozen=True)
class RoadmapTree:
    roadmap_id: UUID
    topic: str
    overall_score: int
    items: list[RoadmapTreeNode]


@dataclass(frozen=True)
class RoadmapListItem:
    roadmap_id: UUID
    topic: str
    overall_score: int


@dataclass(frozen=True)
class RoadmapListResult:
    items: list[RoadmapListItem]
    total_count: int


class RoadmapRetrievalReader(Protocol):
    def find_roadmap(self, roadmap_id: UUID) -> RoadmapRecord | None: ...

    def find_all_roadmaps(self) -> list[RoadmapRecord]: ...


__all__ = [
    "RoadmapItemRecord",
    "RoadmapLevel",
    "RoadmapListItem",
    "RoadmapListResult",
    "RoadmapRecord",
    "RoadmapRetrievalError",
    "RoadmapRetrievalNotFoundError",
    "RoadmapRetrievalReader",
    "RoadmapRetrievalStoreError",
    "RoadmapTree",
    "RoadmapTreeNode",
]
