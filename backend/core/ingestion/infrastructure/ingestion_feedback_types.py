from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Literal, Protocol

if TYPE_CHECKING:
    from uuid import UUID


class IngestionFeedbackInputError(Exception):
    pass


class IngestionFeedbackRoadmapLookupError(Exception):
    pass


class IngestionFeedbackLlmCallError(Exception):
    pass


class IngestionFeedbackResponseFormatError(Exception):
    pass


class IngestionFeedbackPersistenceError(Exception):
    pass


@dataclass(frozen=True)
class IngestionFeedbackChunkInput:
    chunk_index: int
    text: str


@dataclass(frozen=True)
class IngestionFeedbackGenerateInput:
    source_path: str
    chunks: list[IngestionFeedbackChunkInput]
    minimum_chunk_characters: int
    generated_at: str


@dataclass(frozen=True)
class RoadmapCandidate:
    id: UUID
    display_path: str


@dataclass(frozen=True)
class IngestionFeedbackLlmRequest:
    source_path: str
    chunk_texts: list[str]
    roadmap_candidates: list[RoadmapCandidate]


@dataclass(frozen=True)
class IngestionFeedbackLlmResponse:
    selected_roadmap_item_id: UUID | None
    accuracy_check: str
    improvement_suggestions: list[str]


@dataclass(frozen=True)
class NewIngestionFeedbackRecord:
    source_path: str
    roadmap_item_id: UUID | None
    title: str
    body: str
    is_read: bool
    created_at: str
    read_at: str | None


@dataclass(frozen=True)
class StoredIngestionFeedback:
    id: UUID
    source_path: str
    roadmap_item_id: UUID | None
    title: str
    body: str
    is_read: bool
    created_at: str
    read_at: str | None


IngestionFeedbackStatus = Literal["created", "skipped"]
IngestionFeedbackSkipReason = Literal["no_analyzable_chunks"]


@dataclass(frozen=True)
class IngestionFeedbackGenerateResult:
    status: IngestionFeedbackStatus
    used_chunk_count: int
    skipped_chunk_count: int
    created_feedback: StoredIngestionFeedback | None
    skip_reason: IngestionFeedbackSkipReason | None


class IngestionFeedbackLlmClient(Protocol):
    def analyze(
        self,
        request: IngestionFeedbackLlmRequest,
    ) -> IngestionFeedbackLlmResponse: ...


class RoadmapItemReader(Protocol):
    def list_items(self) -> list[RoadmapCandidate]: ...


class IngestionFeedbackWriter(Protocol):
    def create(
        self,
        record: NewIngestionFeedbackRecord,
    ) -> StoredIngestionFeedback: ...


__all__ = [
    "IngestionFeedbackChunkInput",
    "IngestionFeedbackGenerateInput",
    "IngestionFeedbackGenerateResult",
    "IngestionFeedbackInputError",
    "IngestionFeedbackLlmCallError",
    "IngestionFeedbackLlmClient",
    "IngestionFeedbackLlmRequest",
    "IngestionFeedbackLlmResponse",
    "IngestionFeedbackPersistenceError",
    "IngestionFeedbackResponseFormatError",
    "IngestionFeedbackRoadmapLookupError",
    "IngestionFeedbackWriter",
    "NewIngestionFeedbackRecord",
    "RoadmapCandidate",
    "RoadmapItemReader",
    "StoredIngestionFeedback",
]
