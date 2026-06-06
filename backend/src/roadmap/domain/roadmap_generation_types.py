from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Literal, Protocol, TypedDict

if TYPE_CHECKING:
    from uuid import UUID

from roadmap.domain.roadmap_persistence_types import (
    RoadmapItemInput,
    RoadmapSaveInput,
    RoadmapSaveResult,
)

RoadmapGenerationFailureCode = Literal[
    "schedule_failed",
    "llm_request_failed",
    "llm_json_parse_failed",
    "llm_schema_validation_failed",
    "persistence_failed",
]


class RoadmapGenerationAccepted(TypedDict):
    job_id: UUID
    status: Literal["queued"]


class RoadmapGenerationQueuedStatus(TypedDict):
    status: Literal["queued"]


class RoadmapGenerationRunningStatus(TypedDict):
    status: Literal["running"]


class RoadmapGenerationCompletedStatus(TypedDict):
    status: Literal["completed"]
    roadmap_id: UUID


class RoadmapGenerationFailedStatus(TypedDict):
    status: Literal["failed"]
    error_code: RoadmapGenerationFailureCode
    error_message: str


RoadmapGenerationJobStatus = (
    RoadmapGenerationQueuedStatus
    | RoadmapGenerationRunningStatus
    | RoadmapGenerationCompletedStatus
    | RoadmapGenerationFailedStatus
)

RoadmapGenerationItemLevel = Literal["major", "middle", "detail"]


class RoadmapGenerationError(Exception):
    pass


class RoadmapGenerationInputError(RoadmapGenerationError):
    pass


class RoadmapGenerationScheduleError(RoadmapGenerationError):
    pass


class RoadmapGenerationLlmError(RoadmapGenerationError):
    pass


class RoadmapGenerationJobStoreError(RoadmapGenerationError):
    pass


class RoadmapGenerationJobNotFoundError(RoadmapGenerationError):
    pass


class RoadmapGenerationLlmResponseError(RoadmapGenerationError):
    pass


class RoadmapGenerationJsonParseError(RoadmapGenerationLlmResponseError):
    pass


class RoadmapGenerationSchemaValidationError(RoadmapGenerationLlmResponseError):
    pass


@dataclass(frozen=True)
class ValidatedRoadmapGeneration:
    topic: str
    items: list[ValidatedRoadmapGenerationItem]


@dataclass(frozen=True)
class ValidatedRoadmapGenerationItem:
    title: str
    description: str
    level: RoadmapGenerationItemLevel
    children: list[ValidatedRoadmapGenerationItem]


class RoadmapGenerationJobIdGenerator(Protocol):
    def generate(self) -> UUID: ...


class RoadmapGenerationJobScheduler(Protocol):
    def enqueue_roadmap_generation(self, job_id: UUID, topic: str) -> None: ...


class RoadmapGenerationJobStatusStore(Protocol):
    def create_queued_job(self, job_id: UUID, topic: str) -> None: ...

    def mark_running(self, job_id: UUID) -> None: ...

    def mark_completed(self, job_id: UUID, roadmap_id: UUID) -> None: ...

    def mark_failed(
        self,
        job_id: UUID,
        error_code: RoadmapGenerationFailureCode,
        error_message: str,
    ) -> None: ...

    def get_job(self, job_id: UUID) -> RoadmapGenerationJobStatus: ...


class RoadmapGenerationLlmClient(Protocol):
    def generate_roadmap_json(self, topic: str) -> str: ...


class RoadmapGenerationPersistencePort(Protocol):
    def save_roadmap(self, roadmap_input: RoadmapSaveInput) -> RoadmapSaveResult: ...


class RoadmapGenerationClock(Protocol):
    def now(self) -> str: ...


__all__ = [
    "RoadmapGenerationAccepted",
    "RoadmapGenerationClock",
    "RoadmapGenerationCompletedStatus",
    "RoadmapGenerationError",
    "RoadmapGenerationFailedStatus",
    "RoadmapGenerationFailureCode",
    "RoadmapGenerationInputError",
    "RoadmapGenerationItemLevel",
    "RoadmapGenerationJobIdGenerator",
    "RoadmapGenerationJobNotFoundError",
    "RoadmapGenerationJobScheduler",
    "RoadmapGenerationJobStatus",
    "RoadmapGenerationJobStatusStore",
    "RoadmapGenerationJobStoreError",
    "RoadmapGenerationJsonParseError",
    "RoadmapGenerationLlmClient",
    "RoadmapGenerationLlmError",
    "RoadmapGenerationLlmResponseError",
    "RoadmapGenerationPersistencePort",
    "RoadmapGenerationQueuedStatus",
    "RoadmapGenerationRunningStatus",
    "RoadmapGenerationScheduleError",
    "RoadmapGenerationSchemaValidationError",
    "RoadmapItemInput",
    "RoadmapSaveInput",
    "RoadmapSaveResult",
    "ValidatedRoadmapGeneration",
    "ValidatedRoadmapGenerationItem",
]
