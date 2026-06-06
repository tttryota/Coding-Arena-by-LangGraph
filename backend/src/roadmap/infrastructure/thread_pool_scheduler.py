"""RoadmapGenerationJobScheduler Protocol の ThreadPoolExecutor 実装。"""

from __future__ import annotations

from typing import TYPE_CHECKING

import structlog

from roadmap.domain.roadmap_generation_types import RoadmapGenerationScheduleError

if TYPE_CHECKING:
    from collections.abc import Callable
    from concurrent.futures import Future, ThreadPoolExecutor
    from uuid import UUID

logger = structlog.get_logger(__name__)


class ThreadPoolJobScheduler:
    def __init__(
        self,
        executor: ThreadPoolExecutor,
        job_runner: Callable[[UUID, str], None],
    ) -> None:
        self._executor = executor
        self._job_runner = job_runner

    def enqueue_roadmap_generation(self, job_id: UUID, topic: str) -> None:
        try:
            future = self._executor.submit(self._job_runner, job_id, topic)
        except Exception as exc:
            raise RoadmapGenerationScheduleError(str(exc)) from exc
        future.add_done_callback(self._on_job_done)

    @staticmethod
    def _on_job_done(future: Future[None]) -> None:
        if future.cancelled():
            logger.warning("roadmap_generation_job_cancelled")
            return
        exc = future.exception()
        if exc is not None:
            logger.error(
                "roadmap_generation_job_unhandled_error",
                error_type=type(exc).__name__,
                error_message=str(exc),
                exc_info=exc,
            )


__all__ = ["ThreadPoolJobScheduler"]
