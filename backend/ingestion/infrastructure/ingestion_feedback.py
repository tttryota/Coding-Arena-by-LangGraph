from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

import structlog

from ingestion.domain.ingestion_feedback_types import (
    IngestionFeedbackChunkInput,
    IngestionFeedbackGenerateInput,
    IngestionFeedbackGenerateResult,
    IngestionFeedbackInputError,
    IngestionFeedbackLlmCallError,
    IngestionFeedbackLlmClient,
    IngestionFeedbackLlmRequest,
    IngestionFeedbackLlmResponse,
    IngestionFeedbackPersistenceError,
    IngestionFeedbackResponseFormatError,
    IngestionFeedbackRoadmapLookupError,
    IngestionFeedbackWriter,
    NewIngestionFeedbackRecord,
    RoadmapCandidate,
    RoadmapItemReader,
    StoredIngestionFeedback,
)

logger = structlog.get_logger(__name__)

EVENT_CREATED = "ingestion_feedback_created"
EVENT_SKIPPED = "ingestion_feedback_skipped"
EVENT_ROADMAP_LOOKUP_FAILED = "ingestion_feedback_roadmap_lookup_failed"
EVENT_LLM_FAILED = "ingestion_feedback_llm_failed"
EVENT_PERSIST_FAILED = "ingestion_feedback_persist_failed"
SKIP_REASON_NO_ANALYZABLE_CHUNKS = "no_analyzable_chunks"


@dataclass(frozen=True)
class _LogContext:
    source_path: str
    input_chunk_count: int
    used_chunk_count: int
    skipped_chunk_count: int
    roadmap_candidate_count: int


def generate_for_file(
    feedback_input: IngestionFeedbackGenerateInput,
    *,
    llm_client: IngestionFeedbackLlmClient,
    roadmap_reader: RoadmapItemReader,
    writer: IngestionFeedbackWriter,
) -> IngestionFeedbackGenerateResult:
    _validate_input(feedback_input)

    analyzable_chunks = _collect_analyzable_chunks(feedback_input)
    used_chunk_count = len(analyzable_chunks)
    skipped_chunk_count = len(feedback_input.chunks) - used_chunk_count
    log_context = _LogContext(
        source_path=feedback_input.source_path,
        input_chunk_count=len(feedback_input.chunks),
        used_chunk_count=used_chunk_count,
        skipped_chunk_count=skipped_chunk_count,
        roadmap_candidate_count=0,
    )

    if used_chunk_count == 0:
        logger.info(
            EVENT_SKIPPED,
            source_path=log_context.source_path,
            input_chunk_count=log_context.input_chunk_count,
            used_chunk_count=log_context.used_chunk_count,
            skipped_chunk_count=log_context.skipped_chunk_count,
            roadmap_candidate_count=log_context.roadmap_candidate_count,
        )
        return IngestionFeedbackGenerateResult(
            status="skipped",
            used_chunk_count=used_chunk_count,
            skipped_chunk_count=skipped_chunk_count,
            created_feedback=None,
            skip_reason="no_analyzable_chunks",
        )

    roadmap_candidates = _load_roadmap_candidates(
        roadmap_reader=roadmap_reader,
        log_context=log_context,
    )

    request = IngestionFeedbackLlmRequest(
        source_path=feedback_input.source_path,
        chunk_texts=[chunk.text for chunk in analyzable_chunks],
        roadmap_candidates=list(roadmap_candidates),
    )
    response = _analyze_feedback(
        request=request,
        llm_client=llm_client,
        log_context=_LogContext(
            source_path=log_context.source_path,
            input_chunk_count=log_context.input_chunk_count,
            used_chunk_count=log_context.used_chunk_count,
            skipped_chunk_count=log_context.skipped_chunk_count,
            roadmap_candidate_count=len(roadmap_candidates),
        ),
    )

    selected_candidate = _validate_llm_response(
        response=response,
        roadmap_candidates=roadmap_candidates,
        source_path=feedback_input.source_path,
    )
    record = NewIngestionFeedbackRecord(
        source_path=feedback_input.source_path,
        roadmap_item_id=None if selected_candidate is None else selected_candidate.id,
        title=f"{feedback_input.source_path} の取り込みフィードバック",
        body=_build_feedback_body(
            selected_candidate=selected_candidate,
            accuracy_check=response.accuracy_check,
            improvement_suggestions=response.improvement_suggestions,
        ),
        is_read=False,
        created_at=feedback_input.generated_at,
        read_at=None,
    )
    stored_feedback = _persist_feedback(
        record=record,
        writer=writer,
        log_context=_LogContext(
            source_path=log_context.source_path,
            input_chunk_count=log_context.input_chunk_count,
            used_chunk_count=log_context.used_chunk_count,
            skipped_chunk_count=log_context.skipped_chunk_count,
            roadmap_candidate_count=len(roadmap_candidates),
        ),
    )

    logger.info(
        EVENT_CREATED,
        source_path=log_context.source_path,
        input_chunk_count=log_context.input_chunk_count,
        used_chunk_count=log_context.used_chunk_count,
        skipped_chunk_count=log_context.skipped_chunk_count,
        roadmap_candidate_count=len(roadmap_candidates),
        feedback_id=stored_feedback.id,
    )
    return IngestionFeedbackGenerateResult(
        status="created",
        used_chunk_count=used_chunk_count,
        skipped_chunk_count=skipped_chunk_count,
        created_feedback=stored_feedback,
        skip_reason=None,
    )


def _validate_input(feedback_input: IngestionFeedbackGenerateInput) -> None:
    if feedback_input.source_path == "":
        message = (
            f"source_path must be non-empty: source_path={feedback_input.source_path!r}"
        )
        raise IngestionFeedbackInputError(message)
    if feedback_input.minimum_chunk_characters < 1:
        message = (
            "minimum_chunk_characters must be at least 1: "
            f"source_path={feedback_input.source_path!r}, "
            f"minimum_chunk_characters={feedback_input.minimum_chunk_characters}"
        )
        raise IngestionFeedbackInputError(message)
    try:
        datetime.fromisoformat(feedback_input.generated_at)
    except ValueError as exception:
        message = (
            "generated_at must be a valid ISO 8601 string: "
            f"source_path={feedback_input.source_path!r}, "
            f"generated_at={feedback_input.generated_at!r}"
        )
        raise IngestionFeedbackInputError(message) from exception

    seen_indexes: set[int] = set()
    for chunk in feedback_input.chunks:
        if chunk.chunk_index < 0:
            message = (
                "chunk_index must be non-negative: "
                f"source_path={feedback_input.source_path!r}, "
                f"chunk_index={chunk.chunk_index}"
            )
            raise IngestionFeedbackInputError(message)
        if chunk.chunk_index in seen_indexes:
            message = (
                "chunk_index values must be unique: "
                f"source_path={feedback_input.source_path!r}, "
                f"chunk_index={chunk.chunk_index}"
            )
            raise IngestionFeedbackInputError(message)
        seen_indexes.add(chunk.chunk_index)


def _collect_analyzable_chunks(
    feedback_input: IngestionFeedbackGenerateInput,
) -> list[IngestionFeedbackChunkInput]:
    return [
        chunk
        for chunk in sorted(feedback_input.chunks, key=lambda chunk: chunk.chunk_index)
        if len(chunk.text.strip()) >= feedback_input.minimum_chunk_characters
    ]


def _load_roadmap_candidates(
    *,
    roadmap_reader: RoadmapItemReader,
    log_context: _LogContext,
) -> list[RoadmapCandidate]:
    try:
        return roadmap_reader.list_items()
    except Exception as exception:
        logger.exception(
            EVENT_ROADMAP_LOOKUP_FAILED,
            source_path=log_context.source_path,
            input_chunk_count=log_context.input_chunk_count,
            used_chunk_count=log_context.used_chunk_count,
            skipped_chunk_count=log_context.skipped_chunk_count,
            roadmap_candidate_count=0,
            error_type=type(exception).__name__,
        )
        message = (
            "roadmap candidate lookup failed: "
            f"source_path={log_context.source_path!r}, "
            f"input_chunk_count={log_context.input_chunk_count}"
        )
        raise IngestionFeedbackRoadmapLookupError(message) from exception


def _analyze_feedback(
    *,
    request: IngestionFeedbackLlmRequest,
    llm_client: IngestionFeedbackLlmClient,
    log_context: _LogContext,
) -> IngestionFeedbackLlmResponse:
    try:
        return llm_client.analyze(request)
    except Exception as exception:
        logger.exception(
            EVENT_LLM_FAILED,
            source_path=log_context.source_path,
            input_chunk_count=log_context.input_chunk_count,
            used_chunk_count=log_context.used_chunk_count,
            skipped_chunk_count=log_context.skipped_chunk_count,
            roadmap_candidate_count=log_context.roadmap_candidate_count,
            error_type=type(exception).__name__,
        )
        message = (
            "ingestion feedback llm call failed: "
            f"source_path={log_context.source_path!r}, "
            f"used_chunk_count={log_context.used_chunk_count}"
        )
        raise IngestionFeedbackLlmCallError(message) from exception


def _persist_feedback(
    *,
    record: NewIngestionFeedbackRecord,
    writer: IngestionFeedbackWriter,
    log_context: _LogContext,
) -> StoredIngestionFeedback:
    try:
        return writer.create(record)
    except Exception as exception:
        logger.exception(
            EVENT_PERSIST_FAILED,
            source_path=log_context.source_path,
            input_chunk_count=log_context.input_chunk_count,
            used_chunk_count=log_context.used_chunk_count,
            skipped_chunk_count=log_context.skipped_chunk_count,
            roadmap_candidate_count=log_context.roadmap_candidate_count,
            error_type=type(exception).__name__,
        )
        message = (
            "ingestion feedback persistence failed: "
            f"source_path={log_context.source_path!r}"
        )
        raise IngestionFeedbackPersistenceError(message) from exception


def _validate_llm_response(
    *,
    response: object,
    roadmap_candidates: list[RoadmapCandidate],
    source_path: str,
) -> RoadmapCandidate | None:
    if not hasattr(response, "selected_roadmap_item_id"):
        message = (
            "selected_roadmap_item_id is missing from LLM response: "
            f"source_path={source_path!r}"
        )
        raise IngestionFeedbackResponseFormatError(message)
    selected_roadmap_item_id = response.selected_roadmap_item_id
    accuracy_check = getattr(response, "accuracy_check", None)
    improvement_suggestions = getattr(response, "improvement_suggestions", None)

    if not isinstance(accuracy_check, str) or accuracy_check.strip() == "":
        message = (
            f"accuracy_check must be a non-empty string: source_path={source_path!r}"
        )
        raise IngestionFeedbackResponseFormatError(message)
    if not isinstance(improvement_suggestions, list) or improvement_suggestions == []:
        message = (
            "improvement_suggestions must be a non-empty list: "
            f"source_path={source_path!r}"
        )
        raise IngestionFeedbackResponseFormatError(message)
    if any(
        not isinstance(suggestion, str) or suggestion.strip() == ""
        for suggestion in improvement_suggestions
    ):
        message = (
            "improvement_suggestions must contain non-empty strings: "
            f"source_path={source_path!r}"
        )
        raise IngestionFeedbackResponseFormatError(message)
    if selected_roadmap_item_id is None:
        return None

    for candidate in roadmap_candidates:
        if candidate.id == selected_roadmap_item_id:
            return candidate
    message = (
        "selected_roadmap_item_id must be one of the roadmap candidates: "
        f"source_path={source_path!r}"
    )
    raise IngestionFeedbackResponseFormatError(message)


def _build_feedback_body(
    *,
    selected_candidate: RoadmapCandidate | None,
    accuracy_check: str,
    improvement_suggestions: list[str],
) -> str:
    lines: list[str] = []
    if selected_candidate is not None:
        lines.extend(
            [
                f"反映先ロードマップ: {selected_candidate.display_path}",
                "",
            ],
        )
    lines.extend(
        [
            "正確性チェック:",
            accuracy_check,
            "",
            "改善提案:",
        ],
    )
    lines.extend(f"- {suggestion}" for suggestion in improvement_suggestions)
    return "\n".join(lines)


__all__ = ["generate_for_file"]
