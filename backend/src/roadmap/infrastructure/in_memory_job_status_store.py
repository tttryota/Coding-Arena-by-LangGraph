"""RoadmapGenerationJobStatusStore Protocol の in-memory 実装。"""

from __future__ import annotations

import threading
from typing import TYPE_CHECKING

from roadmap.domain.roadmap_generation_types import (
    RoadmapGenerationCompletedStatus,
    RoadmapGenerationFailedStatus,
    RoadmapGenerationJobNotFoundError,
    RoadmapGenerationQueuedStatus,
    RoadmapGenerationRunningStatus,
)

if TYPE_CHECKING:
    from uuid import UUID

    from roadmap.domain.roadmap_generation_types import (
        RoadmapGenerationFailureCode,
        RoadmapGenerationJobStatus,
    )


class InMemoryJobStatusStore:
    def __init__(self) -> None:
        self._jobs: dict[UUID, RoadmapGenerationJobStatus] = {}
        self._topics: dict[UUID, str] = {}
        self._lock = threading.Lock()

    def create_queued_job(self, job_id: UUID, topic: str) -> None:
        with self._lock:
            self._jobs[job_id] = RoadmapGenerationQueuedStatus(status="queued")
            self._topics[job_id] = topic

    def mark_running(self, job_id: UUID) -> None:
        with self._lock:
            self._jobs[job_id] = RoadmapGenerationRunningStatus(status="running")

    def mark_completed(self, job_id: UUID, roadmap_id: UUID) -> None:
        with self._lock:
            self._jobs[job_id] = RoadmapGenerationCompletedStatus(
                status="completed",
                roadmap_id=roadmap_id,
            )

    def mark_failed(
        self,
        job_id: UUID,
        error_code: RoadmapGenerationFailureCode,
        error_message: str,
    ) -> None:
        with self._lock:
            self._jobs[job_id] = RoadmapGenerationFailedStatus(
                status="failed",
                error_code=error_code,
                error_message=error_message,
            )

    def get_job(self, job_id: UUID) -> RoadmapGenerationJobStatus:
        with self._lock:
            if job_id not in self._jobs:
                msg = f"Job not found: {job_id}"
                raise RoadmapGenerationJobNotFoundError(msg)
            return self._jobs[job_id]


__all__ = ["InMemoryJobStatusStore"]
