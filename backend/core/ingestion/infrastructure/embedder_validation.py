from __future__ import annotations

import math
from numbers import Integral

from core.ingestion.infrastructure.embedder_types import (
    ChunkEmbeddingInput,
    EmbeddingBatchInputError,
    EmbeddingResponseCountMismatchError,
    EmbeddingVectorFormatError,
)

EMBEDDING_RESPONSE_FORMAT_MESSAGE = "embedding model must return list[list[float]]"
EMBEDDING_VECTOR_ELEMENT_FORMAT_MESSAGE = (
    "embedding vector elements must be finite floats"
)
BATCH_CHUNKS_TYPE_MESSAGE = "chunks must be a list[ChunkEmbeddingInput]"
CHUNK_INPUT_INVALID_PREFIX = "chunk input invalid at "
CHUNK_INPUT_TYPE_MESSAGE = "chunk must be a ChunkEmbeddingInput"
INPUT_POSITION_PREFIX = "input_position="
CHUNK_INDEX_PREFIX = ": chunk_index="
VECTOR_INDEX_PREFIX = ": vector_index="
GOT_TYPE_PREFIX = ", got_type="
GOT_VALUE_PREFIX = ", got_value="
MINIMUM_CHUNK_INDEX = 0
EMPTY_TEXT = ""
EMPTY_VECTOR_LENGTH = 0


def validate_chunks(
    chunks: object,
    *,
    source_path: str | None,
) -> list[ChunkEmbeddingInput]:
    validated_chunks = _validate_chunks_container(
        chunks,
        source_path=source_path,
    )
    normalized_chunks: list[ChunkEmbeddingInput] = []

    for input_position, chunk in enumerate(validated_chunks):
        validated_chunk = _validate_chunk_input_type(
            chunk,
            input_position=input_position,
        )
        normalized_chunks.append(validated_chunk)
        chunk_prefix = _build_chunk_input_prefix(input_position)
        if not _is_valid_chunk_index(validated_chunk.chunk_index):
            message = (
                f"{chunk_prefix}"
                f"{CHUNK_INDEX_PREFIX}{validated_chunk.chunk_index!r}; "
                "chunk_index must be a non-negative integer"
            )
            raise EmbeddingBatchInputError(message)
        if not isinstance(validated_chunk.text, str):
            message = (
                f"{chunk_prefix}"
                f"{CHUNK_INDEX_PREFIX}{validated_chunk.chunk_index}; "
                f"text must be a string, got {type(validated_chunk.text).__name__}"
            )
            raise EmbeddingBatchInputError(message)
        if validated_chunk.text.strip() == EMPTY_TEXT:
            message = (
                f"{chunk_prefix}"
                f"{CHUNK_INDEX_PREFIX}{validated_chunk.chunk_index}; "
                "text must not be blank"
            )
            raise EmbeddingBatchInputError(message)
    return normalized_chunks


def _validate_chunks_container(
    chunks: object,
    *,
    source_path: str | None,
) -> list[object]:
    if not isinstance(chunks, list):
        message = (
            f"{BATCH_CHUNKS_TYPE_MESSAGE}: "
            f"source_path={source_path!r}, "
            f"{_build_type_and_value_details(chunks)}"
        )
        raise EmbeddingBatchInputError(message)
    return chunks


def _validate_chunk_input_type(
    chunk: object,
    *,
    input_position: int,
) -> ChunkEmbeddingInput:
    if not isinstance(chunk, ChunkEmbeddingInput):
        message = (
            f"{_build_chunk_input_prefix(input_position)}; "
            f"{CHUNK_INPUT_TYPE_MESSAGE}"
            f"{GOT_TYPE_PREFIX}{type(chunk).__name__}"
            f"{GOT_VALUE_PREFIX}{chunk!r}"
        )
        raise EmbeddingBatchInputError(message)
    return chunk


def _is_valid_chunk_index(chunk_index: object) -> bool:
    return (
        isinstance(chunk_index, Integral)
        and not isinstance(chunk_index, bool)
        and int(chunk_index) >= MINIMUM_CHUNK_INDEX
    )


def _build_chunk_input_prefix(input_position: int) -> str:
    return f"{CHUNK_INPUT_INVALID_PREFIX}{INPUT_POSITION_PREFIX}{input_position}"


def validate_embedding_count(
    raw_embeddings: object,
    *,
    expected_count: int,
) -> list[object]:
    if not isinstance(raw_embeddings, list):
        message = (
            f"{EMBEDDING_RESPONSE_FORMAT_MESSAGE}: got {type(raw_embeddings).__name__}"
        )
        raise EmbeddingVectorFormatError(message)

    actual_count = len(raw_embeddings)
    if actual_count != expected_count:
        message = (
            f"embedding response count mismatch: expected {expected_count}, "
            f"got {actual_count}"
        )
        raise EmbeddingResponseCountMismatchError(message)
    return raw_embeddings


def normalize_embeddings(raw_embeddings: list[object]) -> list[list[float]]:
    normalized_embeddings: list[list[float]] = []
    expected_dimension: int | None = None

    for vector_index, raw_vector in enumerate(raw_embeddings):
        normalized_vector = _normalize_vector(raw_vector, vector_index=vector_index)
        if expected_dimension is None:
            expected_dimension = len(normalized_vector)
        elif len(normalized_vector) != expected_dimension:
            message = (
                "embedding vector dimensions must match within a batch: "
                f"{_build_vector_index_detail(vector_index)}"
                f"expected_dimension={expected_dimension}, "
                f"actual_dimension={len(normalized_vector)}"
            )
            raise EmbeddingVectorFormatError(message)
        normalized_embeddings.append(normalized_vector)

    return normalized_embeddings


def _normalize_vector(raw_vector: object, *, vector_index: int) -> list[float]:
    if not isinstance(raw_vector, list):
        message = (
            f"{EMBEDDING_RESPONSE_FORMAT_MESSAGE}"
            f"{VECTOR_INDEX_PREFIX}{vector_index}"
            f"{GOT_TYPE_PREFIX}{type(raw_vector).__name__}"
            f"{GOT_VALUE_PREFIX}{raw_vector!r}"
        )
        raise EmbeddingVectorFormatError(message)
    if len(raw_vector) == EMPTY_VECTOR_LENGTH:
        message = (
            f"embedding vector must not be empty{VECTOR_INDEX_PREFIX}{vector_index}"
        )
        raise EmbeddingVectorFormatError(message)

    normalized_vector: list[float] = []
    for element_index, raw_value in enumerate(raw_vector):
        normalized_vector.append(
            _normalize_vector_value(
                raw_value,
                vector_index=vector_index,
                element_index=element_index,
            ),
        )
    return normalized_vector


def _normalize_vector_value(
    raw_value: object,
    *,
    vector_index: int,
    element_index: int,
) -> float:
    if not isinstance(raw_value, (int, float)) or isinstance(raw_value, bool):
        message = _build_invalid_vector_value_message(
            raw_value,
            vector_index=vector_index,
            element_index=element_index,
        )
        raise EmbeddingVectorFormatError(message)

    normalized_value = float(raw_value)
    if not math.isfinite(normalized_value):
        message = _build_invalid_vector_value_message(
            raw_value,
            vector_index=vector_index,
            element_index=element_index,
        )
        raise EmbeddingVectorFormatError(message)
    return normalized_value


def _build_invalid_vector_value_message(
    raw_value: object,
    *,
    vector_index: int,
    element_index: int,
) -> str:
    return (
        f"{EMBEDDING_VECTOR_ELEMENT_FORMAT_MESSAGE}: "
        f"{_build_vector_index_detail(vector_index)}"
        f"element_index={element_index}, "
        f"{_build_type_and_value_details(raw_value)}"
    )


def _build_vector_index_detail(vector_index: int) -> str:
    return f"vector_index={vector_index}, "


def _build_type_and_value_details(raw_value: object) -> str:
    return (
        f"{GOT_TYPE_PREFIX.removeprefix(', ')}{type(raw_value).__name__}"
        f"{GOT_VALUE_PREFIX}{raw_value!r}"
    )
