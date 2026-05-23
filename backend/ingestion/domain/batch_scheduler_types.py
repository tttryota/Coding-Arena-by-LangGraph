from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Literal, Protocol

if TYPE_CHECKING:
    from pathlib import Path

    from ingestion.application.tagger import ChunkTaggingResult
    from ingestion.domain.chunk_splitter import ChunkSplitResult
    from ingestion.domain.embedder_types import ChunkEmbeddingResult
    from ingestion.infrastructure.file_diff_detector import FileDiffResult

BatchTrigger = Literal["startup", "interval"]
BatchRunStatus = Literal[
    "completed",
    "completed_with_errors",
    "skipped_no_diff",
    "failed",
]
FailedFileAction = Literal["delete", "ingest_new", "ingest_updated"]
FailedFileStep = Literal[
    "load",
    "split",
    "tag",
    "embed",
    "delete_old_chunks",
    "delete_removed_file",
    "upsert",
]


class BatchSchedulerConfigError(Exception):
    pass


@dataclass(frozen=True)
class ChunkStoreChunkInput:
    chunk_index: int
    text: str
    embedding: list[float]
    headers: str
    tags: list[str]
    created_at: str
    updated_at: str


@dataclass(frozen=True)
class ChunkStoreUpsertInput:
    source_path: str
    chunks: list[ChunkStoreChunkInput]


@dataclass(frozen=True)
class ChunkStoreUpsertResult:
    source_path: str
    stored_count: int
    stored_ids: list[str]


@dataclass(frozen=True)
class ChunkStoreDeleteResult:
    source_path: str
    deleted_count: int


@dataclass(frozen=True)
class FailedFileSummary:
    source_path: str
    action: FailedFileAction
    step: FailedFileStep
    error_type: str


@dataclass(frozen=True)
class BatchRunSummary:
    status: BatchRunStatus
    trigger: BatchTrigger
    new_count: int
    updated_count: int
    deleted_count: int
    deleted_success_count: int
    ingest_target_count: int
    ingested_success_count: int
    failed_file_count: int
    failed_files: list[FailedFileSummary]
    stored_chunk_count: int


class FileDiffDetector(Protocol):
    def detect(self, target_path: str | Path) -> FileDiffResult: ...


class VaultMarkdownLoader(Protocol):
    def load(self, source_path: str | Path) -> str: ...


class ChunkSplitter(Protocol):
    def split(
        self,
        markdown_text: str,
        *,
        source_path: str | None = None,
    ) -> list[ChunkSplitResult]: ...


class ChunkTagger(Protocol):
    def tag(
        self,
        chunks: list[ChunkSplitResult],
        *,
        source_path: str,
    ) -> list[ChunkTaggingResult]: ...


class Embedder(Protocol):
    def embed(
        self,
        chunks: list[ChunkSplitResult],
        *,
        source_path: str,
    ) -> list[ChunkEmbeddingResult]: ...


class ChunkStore(Protocol):
    def delete_by_source_path(
        self,
        source_path: str,
    ) -> ChunkStoreDeleteResult: ...

    def upsert_chunks(
        self,
        upsert_input: ChunkStoreUpsertInput,
    ) -> ChunkStoreUpsertResult: ...


class PostIngestionHook(Protocol):
    def on_file_ingested(
        self,
        source_path: str,
        chunk_data: list[tuple[int, str]],
    ) -> None: ...
