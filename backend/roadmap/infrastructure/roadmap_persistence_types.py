from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Literal, Protocol

if TYPE_CHECKING:
    from uuid import UUID


RoadmapLevel = Literal["major", "middle", "detail"]


class RoadmapPersistenceError(Exception):
    pass


class RoadmapPersistenceInputError(RoadmapPersistenceError):
    pass


class RoadmapPersistenceWriteError(RoadmapPersistenceError):
    pass


@dataclass(frozen=True)
class RoadmapItemInput:
    title: str
    description: str
    level: RoadmapLevel
    children: list[RoadmapItemInput]


@dataclass(frozen=True)
class RoadmapSaveInput:
    topic: str
    items: list[RoadmapItemInput]
    created_at: str


@dataclass(frozen=True)
class FlatRoadmapItem:
    id: UUID
    roadmap_id: UUID
    parent_id: UUID | None
    level: RoadmapLevel
    title: str
    description: str
    order: int
    score: int
    created_at: str
    updated_at: str


@dataclass(frozen=True)
class RoadmapSaveResult:
    roadmap_id: UUID
    saved_count: int


class RoadmapPersistenceWriter(Protocol):
    def save_items(
        self,
        roadmap_id: UUID,
        topic: str,
        items: list[FlatRoadmapItem],
    ) -> None: ...


class RoadmapIdGenerator(Protocol):
    def generate(self) -> UUID: ...


__all__ = [
    "FlatRoadmapItem",
    "RoadmapIdGenerator",
    "RoadmapItemInput",
    "RoadmapLevel",
    "RoadmapPersistenceError",
    "RoadmapPersistenceInputError",
    "RoadmapPersistenceWriteError",
    "RoadmapPersistenceWriter",
    "RoadmapSaveInput",
    "RoadmapSaveResult",
]
