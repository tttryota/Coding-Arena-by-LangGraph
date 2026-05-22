from __future__ import annotations

from typing import Literal
from uuid import UUID

RoadmapLevel = Literal["major", "middle", "detail"]


class RoadmapRetrievalError(Exception): ...


class RoadmapRetrievalNotFoundError(RoadmapRetrievalError): ...


class RoadmapRetrievalStoreError(RoadmapRetrievalError): ...


class RoadmapItemRecord:
    id: UUID
    parent_id: UUID | None
    level: RoadmapLevel
    title: str
    description: str
    order: int
    score: int
    last_quiz_at: str | None

    def __init__(
        self,
        *,
        id: UUID,
        parent_id: UUID | None,
        level: RoadmapLevel,
        title: str,
        description: str,
        order: int,
        score: int,
        last_quiz_at: str | None,
    ) -> None: ...


class RoadmapRecord:
    roadmap_id: UUID
    topic: str
    items: list[RoadmapItemRecord]

    def __init__(
        self,
        *,
        roadmap_id: UUID,
        topic: str,
        items: list[RoadmapItemRecord],
    ) -> None: ...


class RoadmapTreeNode:
    id: UUID
    title: str
    description: str
    level: RoadmapLevel
    score: int
    order: int
    children: list[RoadmapTreeNode]
    last_quiz_at: str | None

    def __init__(
        self,
        *,
        id: UUID,
        title: str,
        description: str,
        level: RoadmapLevel,
        score: int,
        order: int,
        children: list[RoadmapTreeNode],
        last_quiz_at: str | None,
    ) -> None: ...


class RoadmapTree:
    roadmap_id: UUID
    topic: str
    overall_score: int
    items: list[RoadmapTreeNode]

    def __init__(
        self,
        *,
        roadmap_id: UUID,
        topic: str,
        overall_score: int,
        items: list[RoadmapTreeNode],
    ) -> None: ...


class RoadmapListItem:
    roadmap_id: UUID
    topic: str
    overall_score: int

    def __init__(
        self,
        *,
        roadmap_id: UUID,
        topic: str,
        overall_score: int,
    ) -> None: ...


class RoadmapListResult:
    items: list[RoadmapListItem]
    total_count: int

    def __init__(self, *, items: list[RoadmapListItem], total_count: int) -> None: ...
