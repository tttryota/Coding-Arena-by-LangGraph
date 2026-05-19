from __future__ import annotations

from dataclasses import dataclass

import structlog

from core.ingestion.infrastructure.embedder_types import (
    ChunkEmbeddingInput,
    ChunkEmbeddingResult,
    EmbeddingBatchInput,
    EmbeddingBatchInputError,
    EmbeddingModel,
    EmbeddingModelCallError,
    EmbeddingResponseCountMismatchError,
    EmbeddingVectorFormatError,
)
from core.ingestion.infrastructure.embedder_validation import (
    normalize_embeddings,
    validate_chunks,
    validate_embedding_count,
)

logger = structlog.get_logger(__name__)

EMPTY_BATCH_CHUNK_COUNT = 0
EMPTY_BATCH_EMBEDDED_COUNT = 0
EMPTY_INVALID_CHUNK_COUNT = 0
EMPTY_MODEL_FAILURE_COUNT = 0
FAILED_BATCH_EMBEDDED_COUNT = 0
FIRST_EMBEDDING_INDEX = 0
SINGLE_MODEL_FAILURE_COUNT = 1
BATCH_INPUT_TYPE_MESSAGE = "batch_input must be an EmbeddingBatchInput"

__all__ = [
    "ChunkEmbeddingInput",
    "ChunkEmbeddingResult",
    "EmbeddingBatchInput",
    "EmbeddingBatchInputError",
    "EmbeddingModel",
    "EmbeddingModelCallError",
    "EmbeddingResponseCountMismatchError",
    "EmbeddingVectorFormatError",
    "embed",
]


@dataclass(frozen=True)
class _ValidatedEmbeddingBatchInput:
    chunks: list[ChunkEmbeddingInput]
    embedding_model: EmbeddingModel
    source_path: str | None


def embed(batch_input: EmbeddingBatchInput) -> list[ChunkEmbeddingResult]:
    validated_input = _validate_batch_input(batch_input)

    if len(validated_input.chunks) == EMPTY_BATCH_CHUNK_COUNT:
        _log_batch_completed(
            source_path=validated_input.source_path,
            chunk_count=EMPTY_BATCH_CHUNK_COUNT,
            embedded_count=EMPTY_BATCH_EMBEDDED_COUNT,
            vector_dimension=None,
        )
        return []

    normalized_embeddings = _embed_chunks(validated_input)
    vector_dimension = _get_vector_dimension(normalized_embeddings)

    _log_batch_completed(
        source_path=validated_input.source_path,
        chunk_count=len(validated_input.chunks),
        embedded_count=len(normalized_embeddings),
        vector_dimension=vector_dimension,
    )

    return _build_chunk_embedding_results(
        validated_input.chunks,
        normalized_embeddings,
    )


def _validate_batch_input(batch_input: object) -> _ValidatedEmbeddingBatchInput:
    if not isinstance(batch_input, EmbeddingBatchInput):
        message = (
            f"{BATCH_INPUT_TYPE_MESSAGE}: "
            f"got_type={type(batch_input).__name__}, "
            f"got_value={batch_input!r}"
        )
        raise EmbeddingBatchInputError(message)

    _validate_embedding_model(
        batch_input.embedding_model,
        source_path=batch_input.source_path,
    )
    validated_chunks = validate_chunks(
        batch_input.chunks,
        source_path=batch_input.source_path,
    )
    return _ValidatedEmbeddingBatchInput(
        chunks=validated_chunks,
        embedding_model=batch_input.embedding_model,
        source_path=batch_input.source_path,
    )


def _embed_chunks(
    batch_input: _ValidatedEmbeddingBatchInput,
) -> list[list[float]]:
    raw_embeddings = _call_embedding_model(batch_input)
    validated_embeddings = validate_embedding_count(
        raw_embeddings,
        expected_count=len(batch_input.chunks),
    )
    return normalize_embeddings(validated_embeddings)


def _call_embedding_model(batch_input: _ValidatedEmbeddingBatchInput) -> object:
    texts = [chunk.text for chunk in batch_input.chunks]
    try:
        return batch_input.embedding_model.embed(texts)
    except Exception as exception:
        _log_model_call_failed(
            source_path=batch_input.source_path,
            chunk_count=len(batch_input.chunks),
        )
        message = (
            "embedding model call failed: "
            f"source_path={batch_input.source_path!r}, "
            f"chunk_count={len(batch_input.chunks)}, "
            f"exception_type={type(exception).__name__}, "
            f"exception_message={exception!s}"
        )
        raise EmbeddingModelCallError(message) from exception


def _get_vector_dimension(normalized_embeddings: list[list[float]]) -> int | None:
    if not normalized_embeddings:
        return None
    return len(normalized_embeddings[FIRST_EMBEDDING_INDEX])


def _build_chunk_embedding_results(
    chunks: list[ChunkEmbeddingInput],
    normalized_embeddings: list[list[float]],
) -> list[ChunkEmbeddingResult]:
    return [
        ChunkEmbeddingResult(
            chunk_index=int(chunk.chunk_index),
            embedding=embedding_values,
        )
        for chunk, embedding_values in zip(
            chunks,
            normalized_embeddings,
            strict=True,
        )
    ]


def _validate_embedding_model(
    embedding_model: EmbeddingModel,
    *,
    source_path: str | None,
) -> None:
    embed_method = getattr(embedding_model, "embed", None)
    if not callable(embed_method):
        message = (
            "embedding_model.embed must be callable: "
            f"source_path={source_path!r}, "
            f"embedding_model_type={type(embedding_model).__name__}, "
            f"embed_attribute_type={type(embed_method).__name__}"
        )
        raise EmbeddingBatchInputError(message)


def _log_batch_completed(
    source_path: str | None,
    chunk_count: int,
    embedded_count: int,
    vector_dimension: int | None,
) -> None:
    logger.info(
        "embedder_batch_completed",
        source_path=source_path,
        chunk_count=chunk_count,
        embedded_count=embedded_count,
        vector_dimension=vector_dimension,
        invalid_chunk_count=EMPTY_INVALID_CHUNK_COUNT,
        model_failure_count=EMPTY_MODEL_FAILURE_COUNT,
    )


def _log_model_call_failed(source_path: str | None, chunk_count: int) -> None:
    logger.exception(
        "embedder_model_call_failed",
        source_path=source_path,
        chunk_count=chunk_count,
        embedded_count=FAILED_BATCH_EMBEDDED_COUNT,
        vector_dimension=None,
        invalid_chunk_count=EMPTY_INVALID_CHUNK_COUNT,
        model_failure_count=SINGLE_MODEL_FAILURE_COUNT,
    )
