from __future__ import annotations

from typing import Any
from uuid import UUID

from roadmap.infrastructure.roadmap_retrieval_types import (
    RoadmapListResult,
    RoadmapTree,
)


def get_roadmap(roadmap_id: UUID, *, reader: Any) -> RoadmapTree: ...


def list_roadmaps(*, reader: Any) -> RoadmapListResult: ...
