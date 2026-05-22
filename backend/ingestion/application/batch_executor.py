from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Final

import structlog

from ingestion.domain.batch_scheduler_types import (
    BatchRunStatus,
    BatchRunSummary,
    BatchSchedulerConfigError,
    BatchTrigger,
    ChunkSplitter,
    ChunkStore,
    ChunkStoreChunkInput,
    ChunkStoreUpsertInput,
    ChunkTagger,
    Embedder,
    FailedFileAction,
    FailedFileStep,
    FailedFileSummary,
    FileDiffDetector,
    VaultMarkdownLoader,
)

if TYPE_CHECKING:
    from collections.abc import Callable
    from types import TracebackType

    from ingestion.application.tagger import ChunkTaggingResult
    from ingestion.domain.chunk_splitter import ChunkSplitResult
    from ingestion.domain.embedder_types import ChunkEmbeddingResult
    from ingestion.infrastructure.file_diff_detector import FileDiffResult

logger = structlog.get_logger(__name__)

EMPTY_TIMESTAMP_PLACEHOLDER: Final = ""
EMPTY_SUMMARY_COUNT: Final = 0
NO_STORED_CHUNKS: Final = 0
NO_FAILED_FILES: Final = 0
NO_DIFF_COUNT: Final = 0
SUCCESS_COUNT_INCREMENT: Final = 1
DELETE_ACTION: Final = "delete"
INGEST_NEW_ACTION: Final = "ingest_new"
INGEST_UPDATED_ACTION: Final = "ingest_updated"
FAILED_STATUS: Final = "failed"
UPSERT_STEP: Final = "upsert"


@dataclass(frozen=True)
class _TaggedChunk:
    chunk_index: int
    text: str
    headers: str
    tags: list[str]


@dataclass(frozen=True)
class BatchExecutionConfig:
    target_path: str
    diff_detector: FileDiffDetector
    markdown_loader: VaultMarkdownLoader
    chunk_splitter: ChunkSplitter
    chunk_tagger: ChunkTagger
    embedder: Embedder
    chunk_store: ChunkStore


@dataclass
class _SummaryState:
    trigger: BatchTrigger
    new_count: int
    updated_count: int
    deleted_count: int
    deleted_success_count: int = 0
    ingested_success_count: int = 0
    stored_chunk_count: int = 0
    failed_files: list[FailedFileSummary] = field(default_factory=list)

    @property
    def ingest_target_count(self) -> int:
        return self.new_count + self.updated_count

    @property
    def failed_file_count(self) -> int:
        return len(self.failed_files)

    def build(self, *, status: BatchRunStatus) -> BatchRunSummary:
        return BatchRunSummary(
            status=status,
            trigger=self.trigger,
            new_count=self.new_count,
            updated_count=self.updated_count,
            deleted_count=self.deleted_count,
            deleted_success_count=self.deleted_success_count,
            ingest_target_count=self.ingest_target_count,
            ingested_success_count=self.ingested_success_count,
            failed_file_count=self.failed_file_count,
            failed_files=list(self.failed_files),
            stored_chunk_count=self.stored_chunk_count,
        )


@dataclass(frozen=True)
class _FailureContext:
    source_path: str
    action: FailedFileAction
    step: FailedFileStep


@dataclass
class _CapturedException:
    exception: Exception | None = None

    def __enter__(self) -> _CapturedException:
        return self

    def __exit__(
        self,
        exception_type: type[BaseException] | None,
        exception: BaseException | None,
        traceback: TracebackType | None,
    ) -> bool:
        del exception_type, traceback
        if isinstance(exception, Exception):
            self.exception = exception
            return True
        return False


def run_once(
    config: BatchExecutionConfig,
    *,
    trigger: BatchTrigger,
) -> BatchRunSummary:
    if not config.target_path:
        message = "target_path must not be empty"
        raise BatchSchedulerConfigError(message)
    return _run_batch(config, trigger=trigger)


def _run_batch(
    config: BatchExecutionConfig,
    *,
    trigger: BatchTrigger,
) -> BatchRunSummary:
    try:
        return _run_batch_inner(config, trigger=trigger)
    except Exception:
        logger.exception(
            "ingestion_batch_unexpected_error",
            trigger=trigger,
            target_path=config.target_path,
        )
        summary = _build_failed_summary(trigger)
        _log_batch_completed(summary)
        return summary


def _run_batch_inner(
    config: BatchExecutionConfig,
    *,
    trigger: BatchTrigger,
) -> BatchRunSummary:
    logger.info(
        "ingestion_batch_started",
        trigger=trigger,
        target_path=config.target_path,
    )
    diff_result = _detect_diff(config)
    if diff_result is None:
        summary = _build_failed_summary(trigger)
        _log_batch_completed(summary)
        return summary

    if _has_no_diff(diff_result):
        summary = _build_empty_summary("skipped_no_diff", trigger=trigger)
        logger.info(
            "ingestion_batch_skipped_no_diff",
            trigger=trigger,
            target_path=config.target_path,
            new_count=summary.new_count,
            updated_count=summary.updated_count,
            deleted_count=summary.deleted_count,
        )
        _log_batch_completed(summary)
        return summary

    summary_state = _SummaryState(
        trigger=trigger,
        new_count=diff_result.new_count,
        updated_count=diff_result.updated_count,
        deleted_count=diff_result.deleted_count,
    )

    for source_path in sorted(diff_result.deleted_files):
        _delete_removed_file(config, summary_state, source_path)

    for source_path in sorted(diff_result.new_files):
        _ingest_new_file(config, summary_state, source_path)

    for source_path in sorted(diff_result.updated_files):
        _ingest_updated_file(config, summary_state, source_path)

    status: BatchRunStatus = (
        "completed"
        if summary_state.failed_file_count == NO_FAILED_FILES
        else "completed_with_errors"
    )
    summary = summary_state.build(status=status)
    _log_batch_completed(summary)
    return summary


def _delete_removed_file(
    config: BatchExecutionConfig,
    summary_state: _SummaryState,
    source_path: str,
) -> None:
    if (
        _run_step(
            lambda: config.chunk_store.delete_by_source_path(source_path),
            summary_state=summary_state,
            failure=_FailureContext(
                source_path=source_path,
                action=DELETE_ACTION,
                step="delete_removed_file",
            ),
        )
        is None
    ):
        return

    summary_state.deleted_success_count += SUCCESS_COUNT_INCREMENT
    _log_file_completed(
        source_path=source_path,
        action=DELETE_ACTION,
        stored_chunk_count=NO_STORED_CHUNKS,
    )


def _ingest_new_file(
    config: BatchExecutionConfig,
    summary_state: _SummaryState,
    source_path: str,
) -> None:
    prepared_chunks = _prepare_chunks(
        config,
        summary_state,
        source_path=source_path,
        action=INGEST_NEW_ACTION,
    )
    if prepared_chunks is None:
        return
    if not prepared_chunks:
        summary_state.ingested_success_count += SUCCESS_COUNT_INCREMENT
        _log_file_completed(
            source_path=source_path,
            action=INGEST_NEW_ACTION,
            stored_chunk_count=NO_STORED_CHUNKS,
        )
        return

    upsert_result = _run_step(
        lambda: config.chunk_store.upsert_chunks(
            ChunkStoreUpsertInput(
                source_path=source_path,
                chunks=[
                    ChunkStoreChunkInput(
                        chunk_index=chunk.chunk_index,
                        text=chunk.text,
                        embedding=embedding,
                        headers=chunk.headers,
                        tags=chunk.tags,
                        created_at=EMPTY_TIMESTAMP_PLACEHOLDER,
                        updated_at=EMPTY_TIMESTAMP_PLACEHOLDER,
                    )
                    for chunk, embedding in prepared_chunks
                ],
            ),
        ),
        summary_state=summary_state,
        failure=_FailureContext(
            source_path=source_path,
            action=INGEST_NEW_ACTION,
            step=UPSERT_STEP,
        ),
    )
    if upsert_result is None:
        return

    summary_state.ingested_success_count += SUCCESS_COUNT_INCREMENT
    summary_state.stored_chunk_count += upsert_result.stored_count
    _log_file_completed(
        source_path=source_path,
        action=INGEST_NEW_ACTION,
        stored_chunk_count=upsert_result.stored_count,
    )


def _ingest_updated_file(
    config: BatchExecutionConfig,
    summary_state: _SummaryState,
    source_path: str,
) -> None:
    prepared_chunks = _prepare_chunks(
        config,
        summary_state,
        source_path=source_path,
        action=INGEST_UPDATED_ACTION,
    )
    if prepared_chunks is None:
        return

    if (
        _run_step(
            lambda: config.chunk_store.delete_by_source_path(source_path),
            summary_state=summary_state,
            failure=_FailureContext(
                source_path=source_path,
                action=INGEST_UPDATED_ACTION,
                step="delete_old_chunks",
            ),
        )
        is None
    ):
        return

    if not prepared_chunks:
        summary_state.ingested_success_count += SUCCESS_COUNT_INCREMENT
        _log_file_completed(
            source_path=source_path,
            action=INGEST_UPDATED_ACTION,
            stored_chunk_count=NO_STORED_CHUNKS,
        )
        return

    upsert_result = _run_step(
        lambda: config.chunk_store.upsert_chunks(
            ChunkStoreUpsertInput(
                source_path=source_path,
                chunks=[
                    ChunkStoreChunkInput(
                        chunk_index=chunk.chunk_index,
                        text=chunk.text,
                        embedding=embedding,
                        headers=chunk.headers,
                        tags=chunk.tags,
                        created_at=EMPTY_TIMESTAMP_PLACEHOLDER,
                        updated_at=EMPTY_TIMESTAMP_PLACEHOLDER,
                    )
                    for chunk, embedding in prepared_chunks
                ],
            ),
        ),
        summary_state=summary_state,
        failure=_FailureContext(
            source_path=source_path,
            action=INGEST_UPDATED_ACTION,
            step=UPSERT_STEP,
        ),
    )
    if upsert_result is None:
        return

    summary_state.ingested_success_count += SUCCESS_COUNT_INCREMENT
    summary_state.stored_chunk_count += upsert_result.stored_count
    _log_file_completed(
        source_path=source_path,
        action=INGEST_UPDATED_ACTION,
        stored_chunk_count=upsert_result.stored_count,
    )


def _prepare_chunks(
    config: BatchExecutionConfig,
    summary_state: _SummaryState,
    *,
    source_path: str,
    action: FailedFileAction,
) -> list[tuple[_TaggedChunk, list[float]]] | None:
    markdown_text = _run_step(
        lambda: config.markdown_loader.load(source_path),
        summary_state=summary_state,
        failure=_FailureContext(
            source_path=source_path,
            action=action,
            step="load",
        ),
    )
    if markdown_text is None:
        return None

    split_results = _run_step(
        lambda: config.chunk_splitter.split(
            markdown_text,
            source_path=source_path,
        ),
        summary_state=summary_state,
        failure=_FailureContext(
            source_path=source_path,
            action=action,
            step="split",
        ),
    )
    if split_results is None:
        return None

    if not split_results:
        return []

    tagging_results = _run_step(
        lambda: config.chunk_tagger.tag(
            split_results,
            source_path=source_path,
        ),
        summary_state=summary_state,
        failure=_FailureContext(
            source_path=source_path,
            action=action,
            step="tag",
        ),
    )
    if tagging_results is None:
        return None

    embedding_results = _run_step(
        lambda: config.embedder.embed(
            split_results,
            source_path=source_path,
        ),
        summary_state=summary_state,
        failure=_FailureContext(
            source_path=source_path,
            action=action,
            step="embed",
        ),
    )
    if embedding_results is None:
        return None

    return _build_prepared_chunks(
        split_results,
        tagging_results=tagging_results,
        embedding_results=embedding_results,
    )


def _build_prepared_chunks(
    split_results: list[ChunkSplitResult],
    *,
    tagging_results: list[ChunkTaggingResult],
    embedding_results: list[ChunkEmbeddingResult],
) -> list[tuple[_TaggedChunk, list[float]]]:
    tags_by_index = {
        result.chunk_index: list(result.tags) for result in tagging_results
    }
    embeddings_by_index = {
        result.chunk_index: list(result.embedding) for result in embedding_results
    }
    return [
        (
            _TaggedChunk(
                chunk_index=index,
                text=chunk.content,
                headers=" / ".join(chunk.heading_path),
                tags=tags_by_index.get(index, []),
            ),
            embeddings_by_index.get(index, []),
        )
        for index, chunk in enumerate(split_results)
    ]


def _detect_diff(config: BatchExecutionConfig) -> FileDiffResult | None:
    with _CapturedException() as captured:
        result = config.diff_detector.detect(config.target_path)
    if captured.exception is not None:
        logger.error(
            "ingestion_batch_diff_detection_failed",
            target_path=config.target_path,
            error_type=type(captured.exception).__name__,
            exc_info=captured.exception,
        )
        return None
    return result


def _run_step[TResult](
    operation: Callable[[], TResult],
    *,
    summary_state: _SummaryState | None,
    failure: _FailureContext | None,
) -> TResult | None:
    with _CapturedException() as captured_exception:
        result = operation()
    if captured_exception.exception is not None:
        if summary_state is not None and failure is not None:
            _record_failure(
                summary_state,
                failure=failure,
                exception=captured_exception.exception,
            )
        return None
    return result


def _record_failure(
    summary_state: _SummaryState,
    *,
    failure: _FailureContext,
    exception: Exception,
) -> None:
    summary_state.failed_files.append(
        FailedFileSummary(
            source_path=failure.source_path,
            action=failure.action,
            step=failure.step,
            error_type=type(exception).__name__,
        ),
    )
    logger.error(
        "ingestion_batch_file_failed",
        source_path=failure.source_path,
        action=failure.action,
        step=failure.step,
        error_type=type(exception).__name__,
    )


def _log_file_completed(
    *,
    source_path: str,
    action: FailedFileAction,
    stored_chunk_count: int,
) -> None:
    logger.info(
        "ingestion_batch_file_completed",
        source_path=source_path,
        action=action,
        stored_chunk_count=stored_chunk_count,
    )


def _has_no_diff(diff_result: FileDiffResult) -> bool:
    return (
        diff_result.new_count == NO_DIFF_COUNT
        and diff_result.updated_count == NO_DIFF_COUNT
        and diff_result.deleted_count == NO_DIFF_COUNT
    )


def _build_empty_summary(
    status: BatchRunStatus,
    *,
    trigger: BatchTrigger,
) -> BatchRunSummary:
    return BatchRunSummary(
        status=status,
        trigger=trigger,
        new_count=EMPTY_SUMMARY_COUNT,
        updated_count=EMPTY_SUMMARY_COUNT,
        deleted_count=EMPTY_SUMMARY_COUNT,
        deleted_success_count=EMPTY_SUMMARY_COUNT,
        ingest_target_count=EMPTY_SUMMARY_COUNT,
        ingested_success_count=EMPTY_SUMMARY_COUNT,
        failed_file_count=EMPTY_SUMMARY_COUNT,
        failed_files=[],
        stored_chunk_count=EMPTY_SUMMARY_COUNT,
    )


def _build_failed_summary(trigger: BatchTrigger) -> BatchRunSummary:
    return _build_empty_summary(FAILED_STATUS, trigger=trigger)


def _log_batch_completed(summary: BatchRunSummary) -> None:
    logger.info(
        "ingestion_batch_completed",
        status=summary.status,
        trigger=summary.trigger,
        new_count=summary.new_count,
        updated_count=summary.updated_count,
        deleted_count=summary.deleted_count,
        deleted_success_count=summary.deleted_success_count,
        ingested_success_count=summary.ingested_success_count,
        failed_file_count=summary.failed_file_count,
        stored_chunk_count=summary.stored_chunk_count,
    )
