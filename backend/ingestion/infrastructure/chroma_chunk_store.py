from __future__ import annotations

import math
from dataclasses import dataclass
from numbers import Real
from typing import Final, Literal, Protocol, TypedDict, cast

import structlog

from ingestion.domain.batch_scheduler_types import (
    ChunkStoreChunkInput,
    ChunkStoreDeleteResult,
    ChunkStoreUpsertInput,
    ChunkStoreUpsertResult,
)

logger = structlog.get_logger(__name__)

SOURCE_PATH_KEY: Final = "source_path"
CHUNK_INDEX_KEY: Final = "chunk_index"
HEADERS_KEY: Final = "headers"
TAGS_KEY: Final = "tags"
CREATED_AT_KEY: Final = "created_at"
UPDATED_AT_KEY: Final = "updated_at"
IDS_KEY: Final = "ids"
DOCUMENTS_KEY: Final = "documents"
EMBEDDINGS_KEY: Final = "embeddings"
METADATAS_KEY: Final = "metadatas"
OPERATION_UPSERT: Final = "upsert"
OPERATION_GET: Final = "get"
OPERATION_DELETE: Final = "delete"
EVENT_CHUNK_STORE_UPSERT_COMPLETED: Final = "chunk_store_upsert_completed"
EVENT_CHUNK_STORE_UPSERT_FAILED: Final = "chunk_store_upsert_failed"
EVENT_CHUNK_STORE_GET_COMPLETED: Final = "chunk_store_get_completed"
EVENT_CHUNK_STORE_GET_FAILED: Final = "chunk_store_get_failed"
EVENT_CHUNK_STORE_DELETE_COMPLETED: Final = "chunk_store_delete_completed"
EVENT_CHUNK_STORE_DELETE_FAILED: Final = "chunk_store_delete_failed"
REASON_MUST_BE_NON_EMPTY_STRING: Final = "must be a non-empty string"
REASON_MUST_BE_FINITE_NUMBER: Final = "must be a finite number"
REASON_STORED_EMBEDDING_VALUES_MUST_BE_FINITE_NUMBERS: Final = (
    "stored embedding values must be finite numbers"
)
REASON_STORED_SOURCE_PATH_MISMATCH: Final = (
    "stored metadata source_path does not match requested source_path"
)
RECORD_FORMAT_ERROR_PREFIX: Final = "chunk store record format error"
REASON_RAW_RESULT_LIST_LENGTH_MISMATCH: Final = (
    "raw backend result lists must have the same length"
)
ZERO_COUNT: Final = 0
FIRST_ITEM_INDEX: Final = 0
SINGLE_ITEM_COUNT: Final = 1
MINIMUM_CHUNK_INDEX: Final = 0
_MISSING = object()


class ChunkStoreInputError(Exception):
    pass


class ChunkStoreDuplicateChunkIndexError(Exception):
    pass


class ChunkStoreBackendError(Exception):
    pass


class ChunkStoreRecordFormatError(Exception):
    pass


@dataclass(frozen=True)
class StoredChunkMetadata:
    source_path: str
    chunk_index: int
    headers: str
    tags: list[str]
    created_at: str
    updated_at: str


@dataclass(frozen=True)
class StoredChunk:
    id: str
    text: str
    embedding: list[float]
    metadata: StoredChunkMetadata


class _ChunkStoreMetadataPayload(TypedDict):
    source_path: str
    chunk_index: int
    headers: str
    tags: list[str]
    created_at: str
    updated_at: str


class _ChunkStoreSourcePathWhere(TypedDict):
    source_path: str


class _ChunkStoreRawResult(TypedDict):
    ids: object
    documents: object
    embeddings: object
    metadatas: object


class _ChunkStoreRawMetadata(TypedDict):
    source_path: object
    chunk_index: object
    headers: object
    tags: object
    created_at: object
    updated_at: object


_RawResultListKey = Literal["ids", "documents", "embeddings", "metadatas"]


class ChunkCollection(Protocol):
    def upsert(
        self,
        ids: list[str],
        documents: list[str],
        embeddings: list[list[float]],
        metadatas: list[_ChunkStoreMetadataPayload],
    ) -> None: ...

    def get(self, where: _ChunkStoreSourcePathWhere) -> _ChunkStoreRawResult: ...

    def delete(self, where: _ChunkStoreSourcePathWhere) -> None: ...


@dataclass(frozen=True)
class _ValidatedChunk:
    chunk_index: int
    text: str
    embedding: list[float]
    headers: str
    tags: list[str]
    created_at: str
    updated_at: str


@dataclass(frozen=True)
class _InputValidationContext:
    operation: str
    source_path: str | None = None
    chunk_index: int | None = None


@dataclass(frozen=True)
class _RecordValidationContext:
    operation: str
    source_path: str
    record_index: int | None = None
    metadata_source_path: str | None = None
    chunk_index: int | None = None


@dataclass(frozen=True)
class _RawStoredChunk:
    chunk_id: object
    document: object
    embedding: object
    metadata: object


class ChromaChunkStore:
    def __init__(self, collection: ChunkCollection) -> None:
        self._collection = collection

    def upsert_chunks(
        self,
        upsert_input: ChunkStoreUpsertInput,
    ) -> ChunkStoreUpsertResult:
        source_path = _validate_source_path(
            upsert_input.source_path,
            operation=OPERATION_UPSERT,
        )
        validated_chunks = _validate_upsert_chunks(
            upsert_input.chunks,
            context=_InputValidationContext(
                operation=OPERATION_UPSERT,
                source_path=source_path,
            ),
        )
        if not validated_chunks:
            logger.info(
                EVENT_CHUNK_STORE_UPSERT_COMPLETED,
                source_path=source_path,
                chunk_count=ZERO_COUNT,
                stored_count=ZERO_COUNT,
                vector_dimension=None,
            )
            return ChunkStoreUpsertResult(
                source_path=source_path,
                stored_count=ZERO_COUNT,
                stored_ids=[],
            )

        _ensure_unique_chunk_indexes(
            validated_chunks,
            source_path=source_path,
        )

        stored_ids = [
            _build_chunk_id(source_path, chunk.chunk_index)
            for chunk in validated_chunks
        ]
        documents = [chunk.text for chunk in validated_chunks]
        embeddings = [list(chunk.embedding) for chunk in validated_chunks]
        metadata_payloads = [
            _build_metadata_payload(source_path=source_path, chunk=chunk)
            for chunk in validated_chunks
        ]

        try:
            self._collection.upsert(
                ids=stored_ids,
                documents=documents,
                embeddings=embeddings,
                metadatas=metadata_payloads,
            )
        except Exception as exception:
            logger.exception(
                EVENT_CHUNK_STORE_UPSERT_FAILED,
                source_path=source_path,
                chunk_count=len(validated_chunks),
                stored_count=ZERO_COUNT,
                vector_dimension=len(validated_chunks[FIRST_ITEM_INDEX].embedding),
                error_type=type(exception).__name__,
            )
            message = _build_backend_error_message(
                operation=OPERATION_UPSERT,
                source_path=source_path,
                chunk_count=len(validated_chunks),
            )
            raise ChunkStoreBackendError(message) from exception

        logger.info(
            EVENT_CHUNK_STORE_UPSERT_COMPLETED,
            source_path=source_path,
            chunk_count=len(validated_chunks),
            stored_count=len(validated_chunks),
            vector_dimension=len(validated_chunks[FIRST_ITEM_INDEX].embedding),
        )
        return ChunkStoreUpsertResult(
            source_path=source_path,
            stored_count=len(validated_chunks),
            stored_ids=stored_ids,
        )

    def get_by_source_path(self, source_path: str) -> list[StoredChunk]:
        validated_source_path = _validate_source_path(
            source_path,
            operation=OPERATION_GET,
        )
        where = _build_source_path_where(validated_source_path)
        try:
            raw_result = self._collection.get(where=where)
        except Exception as exception:
            logger.exception(
                EVENT_CHUNK_STORE_GET_FAILED,
                source_path=validated_source_path,
                returned_count=ZERO_COUNT,
                vector_dimension=None,
                error_type=type(exception).__name__,
            )
            message = _build_backend_error_message(
                operation=OPERATION_GET,
                source_path=validated_source_path,
            )
            raise ChunkStoreBackendError(message) from exception

        stored_chunks = _normalize_raw_result(
            raw_result,
            operation=OPERATION_GET,
            source_path=validated_source_path,
        )
        stored_chunks.sort(key=lambda chunk: chunk.metadata.chunk_index)
        logger.info(
            EVENT_CHUNK_STORE_GET_COMPLETED,
            source_path=validated_source_path,
            returned_count=len(stored_chunks),
            vector_dimension=_get_vector_dimension(stored_chunks),
        )
        return stored_chunks

    def delete_by_source_path(self, source_path: str) -> ChunkStoreDeleteResult:
        validated_source_path = _validate_source_path(
            source_path,
            operation=OPERATION_DELETE,
        )
        where = _build_source_path_where(validated_source_path)

        try:
            raw_result = self._collection.get(where=where)
        except Exception as exception:
            logger.exception(
                EVENT_CHUNK_STORE_DELETE_FAILED,
                source_path=validated_source_path,
                deleted_count=ZERO_COUNT,
                error_type=type(exception).__name__,
            )
            message = _build_backend_error_message(
                operation=OPERATION_DELETE,
                source_path=validated_source_path,
            )
            raise ChunkStoreBackendError(message) from exception

        deleted_count = _extract_deleted_count(
            raw_result,
            source_path=validated_source_path,
        )

        try:
            self._collection.delete(where=where)
        except Exception as exception:
            logger.exception(
                EVENT_CHUNK_STORE_DELETE_FAILED,
                source_path=validated_source_path,
                deleted_count=ZERO_COUNT,
                error_type=type(exception).__name__,
            )
            message = _build_backend_error_message(
                operation=OPERATION_DELETE,
                source_path=validated_source_path,
            )
            raise ChunkStoreBackendError(message) from exception

        logger.info(
            EVENT_CHUNK_STORE_DELETE_COMPLETED,
            source_path=validated_source_path,
            deleted_count=deleted_count,
        )
        return ChunkStoreDeleteResult(
            source_path=validated_source_path,
            deleted_count=deleted_count,
        )


def _extract_deleted_count(
    raw_result: object,
    *,
    source_path: str,
) -> int:
    is_valid_result = isinstance(raw_result, dict) and isinstance(
        raw_result.get(IDS_KEY),
        list,
    )
    if not is_valid_result:
        logger.error(
            EVENT_CHUNK_STORE_DELETE_FAILED,
            source_path=source_path,
            deleted_count=ZERO_COUNT,
            error_type="BackendResponseError",
        )
        message = _build_backend_error_message(
            operation=OPERATION_DELETE,
            source_path=source_path,
        )
        raise ChunkStoreBackendError(message)
    return len(cast("list[object]", cast("dict[str, object]", raw_result)[IDS_KEY]))


def _validate_source_path(source_path: object, *, operation: str) -> str:
    if not isinstance(source_path, str) or source_path == "":
        message = _build_input_validation_error_message(
            field_name=SOURCE_PATH_KEY,
            reason=REASON_MUST_BE_NON_EMPTY_STRING,
            value=source_path,
            context=_InputValidationContext(operation=operation),
        )
        raise ChunkStoreInputError(message)
    return source_path


def _validate_upsert_chunks(
    chunks: object,
    *,
    context: _InputValidationContext,
) -> list[_ValidatedChunk]:
    if not isinstance(chunks, list):
        message = _build_input_validation_error_message(
            field_name="chunks",
            reason="must be a list",
            value=chunks,
            context=context,
        )
        raise ChunkStoreInputError(message)

    validated_chunks = [_validate_chunk(chunk, context=context) for chunk in chunks]
    _ensure_embedding_dimensions_match(validated_chunks, context=context)
    return validated_chunks


def _validate_chunk(
    chunk: object,
    *,
    context: _InputValidationContext,
) -> _ValidatedChunk:
    if not isinstance(chunk, ChunkStoreChunkInput):
        message = _build_input_validation_error_message(
            field_name="chunk",
            reason="must be a ChunkStoreChunkInput",
            value=chunk,
            context=context,
        )
        raise ChunkStoreInputError(message)

    chunk_index = _validate_chunk_index(chunk.chunk_index, context=context)
    chunk_context = _with_input_chunk_index(context, chunk_index)
    text = _validate_chunk_text(
        chunk.text,
        context=chunk_context,
    )
    embedding = _validate_embedding(
        chunk.embedding,
        context=chunk_context,
    )
    headers = _validate_string_field(
        chunk.headers,
        field_name=HEADERS_KEY,
        context=chunk_context,
    )
    tags = _validate_tags(
        chunk.tags,
        context=chunk_context,
    )
    created_at = _validate_string_field(
        chunk.created_at,
        field_name=CREATED_AT_KEY,
        context=chunk_context,
    )
    updated_at = _validate_string_field(
        chunk.updated_at,
        field_name=UPDATED_AT_KEY,
        context=chunk_context,
    )

    return _ValidatedChunk(
        chunk_index=chunk_index,
        text=text,
        embedding=embedding,
        headers=headers,
        tags=tags,
        created_at=created_at,
        updated_at=updated_at,
    )


def _validate_chunk_index(
    chunk_index: object,
    *,
    context: _InputValidationContext,
) -> int:
    if (
        not isinstance(chunk_index, int)
        or isinstance(chunk_index, bool)
        or chunk_index < MINIMUM_CHUNK_INDEX
    ):
        message = _build_input_validation_error_message(
            field_name=CHUNK_INDEX_KEY,
            reason="must be a non-negative integer",
            value=chunk_index,
            context=context,
        )
        raise ChunkStoreInputError(message)
    return chunk_index


def _validate_chunk_text(text: object, *, context: _InputValidationContext) -> str:
    if not isinstance(text, str) or text.strip() == "":
        message = _build_input_validation_error_message(
            field_name="text",
            reason=REASON_MUST_BE_NON_EMPTY_STRING,
            value=text,
            context=context,
        )
        raise ChunkStoreInputError(message)
    return text


def _validate_embedding(
    embedding: object,
    *,
    context: _InputValidationContext,
) -> list[float]:
    if not isinstance(embedding, list) or not embedding:
        message = _build_input_validation_error_message(
            field_name=EMBEDDINGS_KEY,
            reason="must be a non-empty list",
            value=embedding,
            context=context,
        )
        raise ChunkStoreInputError(message)

    normalized: list[float] = []
    for index, value in enumerate(embedding):
        if not isinstance(value, Real) or isinstance(value, bool):
            raise ChunkStoreInputError(
                _build_input_validation_error_message(
                    field_name=f"{EMBEDDINGS_KEY}[{index}]",
                    reason=REASON_MUST_BE_FINITE_NUMBER,
                    value=value,
                    context=context,
                ),
            )
        numeric_value = float(value)
        if not math.isfinite(numeric_value):
            raise ChunkStoreInputError(
                _build_input_validation_error_message(
                    field_name=f"{EMBEDDINGS_KEY}[{index}]",
                    reason=REASON_MUST_BE_FINITE_NUMBER,
                    value=value,
                    context=context,
                ),
            )
        normalized.append(numeric_value)
    return normalized


def _validate_string_field(
    value: object,
    *,
    field_name: str,
    context: _InputValidationContext,
) -> str:
    if not isinstance(value, str):
        message = _build_input_validation_error_message(
            field_name=field_name,
            reason="must be a string",
            value=value,
            context=context,
        )
        raise ChunkStoreInputError(message)
    return value


def _validate_tags(
    tags: object,
    *,
    context: _InputValidationContext,
) -> list[str]:
    if not isinstance(tags, list):
        message = _build_input_validation_error_message(
            field_name=TAGS_KEY,
            reason="must be a list[str]",
            value=tags,
            context=context,
        )
        raise ChunkStoreInputError(message)
    for index, tag in enumerate(tags):
        if not isinstance(tag, str):
            message = _build_input_validation_error_message(
                field_name=f"{TAGS_KEY}[{index}]",
                reason="must be a string inside list[str]",
                value=tag,
                context=context,
            )
            raise ChunkStoreInputError(message)
    return list(tags)


def _ensure_embedding_dimensions_match(
    chunks: list[_ValidatedChunk],
    *,
    context: _InputValidationContext,
) -> None:
    if len(chunks) <= SINGLE_ITEM_COUNT:
        return
    expected_dimension = len(chunks[FIRST_ITEM_INDEX].embedding)
    for chunk in chunks[SINGLE_ITEM_COUNT:]:
        if len(chunk.embedding) != expected_dimension:
            message = (
                f"{OPERATION_UPSERT} validation failed: "
                "embedding dimensions must match within "
                f"the batch (source_path={context.source_path!r}, expected_dimension="
                f"{expected_dimension}, chunk_index={chunk.chunk_index}, actual_dimension="
                f"{len(chunk.embedding)})"
            )
            raise ChunkStoreInputError(message)


def _ensure_unique_chunk_indexes(
    chunks: list[_ValidatedChunk],
    *,
    source_path: str,
) -> None:
    seen_chunk_indexes: set[int] = set()
    for chunk in chunks:
        if chunk.chunk_index in seen_chunk_indexes:
            message = (
                f"duplicate {CHUNK_INDEX_KEY} in {OPERATION_UPSERT} batch "
                f"({SOURCE_PATH_KEY}={source_path!r}, "
                f"{CHUNK_INDEX_KEY}={chunk.chunk_index})"
            )
            raise ChunkStoreDuplicateChunkIndexError(
                message,
            )
        seen_chunk_indexes.add(chunk.chunk_index)


def _build_chunk_id(source_path: str, chunk_index: int) -> str:
    return f"{source_path}_{chunk_index}"


def _build_metadata_payload(
    *,
    source_path: str,
    chunk: _ValidatedChunk,
) -> _ChunkStoreMetadataPayload:
    return cast(
        "_ChunkStoreMetadataPayload",
        {
            SOURCE_PATH_KEY: source_path,
            CHUNK_INDEX_KEY: chunk.chunk_index,
            HEADERS_KEY: chunk.headers,
            TAGS_KEY: list(chunk.tags),
            CREATED_AT_KEY: chunk.created_at,
            UPDATED_AT_KEY: chunk.updated_at,
        },
    )


def _build_source_path_where(source_path: str) -> _ChunkStoreSourcePathWhere:
    return cast("_ChunkStoreSourcePathWhere", {SOURCE_PATH_KEY: source_path})


def _build_backend_error_message(
    *,
    operation: str,
    source_path: str,
    chunk_count: int | None = None,
) -> str:
    detail_parts = [f"{SOURCE_PATH_KEY}={source_path!r}"]
    if chunk_count is not None:
        detail_parts.append(f"chunk_count={chunk_count}")
    return f"chunk store {operation} failed for {', '.join(detail_parts)}"


def _normalize_raw_result(
    raw_result: object,
    *,
    operation: str,
    source_path: str,
) -> list[StoredChunk]:
    validated_raw_result = _validate_raw_result(
        raw_result,
        operation=operation,
        source_path=source_path,
    )

    ids = _extract_result_list(
        validated_raw_result,
        IDS_KEY,
        operation=operation,
        source_path=source_path,
    )
    documents = _extract_result_list(
        validated_raw_result,
        DOCUMENTS_KEY,
        operation=operation,
        source_path=source_path,
    )
    embeddings = _extract_result_list(
        validated_raw_result,
        EMBEDDINGS_KEY,
        operation=operation,
        source_path=source_path,
    )
    metadata_list = _extract_result_list(
        validated_raw_result,
        METADATAS_KEY,
        operation=operation,
        source_path=source_path,
    )

    if not (len(ids) == len(documents) == len(embeddings) == len(metadata_list)):
        message = (
            f"{RECORD_FORMAT_ERROR_PREFIX}: "
            f"{REASON_RAW_RESULT_LIST_LENGTH_MISMATCH} "
            f"(operation={operation!r}, source_path={source_path!r}, "
            f"{IDS_KEY}_count={len(ids)}, {DOCUMENTS_KEY}_count={len(documents)}, "
            f"{EMBEDDINGS_KEY}_count={len(embeddings)}, "
            f"{METADATAS_KEY}_count={len(metadata_list)})"
        )
        raise ChunkStoreRecordFormatError(
            message,
        )

    normalized_chunks: list[StoredChunk] = []
    for record_index, (chunk_id, document, embedding, metadata) in enumerate(
        zip(
            ids,
            documents,
            embeddings,
            metadata_list,
            strict=True,
        ),
    ):
        normalized_chunks.append(
            _normalize_stored_chunk(
                _RawStoredChunk(
                    chunk_id=chunk_id,
                    document=document,
                    embedding=embedding,
                    metadata=metadata,
                ),
                context=_RecordValidationContext(
                    operation=operation,
                    source_path=source_path,
                    record_index=record_index,
                ),
            ),
        )
    return normalized_chunks


def _validate_raw_result(
    raw_result: object,
    *,
    operation: str,
    source_path: str,
) -> _ChunkStoreRawResult:
    if not isinstance(raw_result, dict):
        message = _build_record_format_error_message(
            reason="raw backend result must be a dict",
            value=raw_result,
            context=_RecordValidationContext(
                operation=operation,
                source_path=source_path,
            ),
        )
        raise ChunkStoreRecordFormatError(message)
    return cast("_ChunkStoreRawResult", raw_result)


def _extract_result_list(
    raw_result: _ChunkStoreRawResult,
    key: _RawResultListKey,
    *,
    operation: str,
    source_path: str,
) -> list[object]:
    value = raw_result.get(key)
    if not isinstance(value, list):
        message = _build_record_format_error_message(
            reason="raw backend result field must be a list",
            field_name=key,
            value=value,
            context=_RecordValidationContext(
                operation=operation,
                source_path=source_path,
            ),
        )
        raise ChunkStoreRecordFormatError(
            message,
        )
    return value


def _normalize_stored_chunk(
    raw_chunk: _RawStoredChunk,
    *,
    context: _RecordValidationContext,
) -> StoredChunk:
    if not isinstance(raw_chunk.document, str) or raw_chunk.document.strip() == "":
        message = _build_record_format_error_message(
            reason="stored document must be a non-empty string",
            field_name=DOCUMENTS_KEY,
            value=raw_chunk.document,
            context=context,
        )
        raise ChunkStoreRecordFormatError(message)

    normalized_embedding = _validate_record_embedding(
        raw_chunk.embedding,
        context=context,
    )
    normalized_metadata = _normalize_metadata(
        raw_chunk.metadata,
        context=context,
    )
    expected_id = _build_chunk_id(
        normalized_metadata.source_path,
        normalized_metadata.chunk_index,
    )
    normalized_context = _with_record_metadata(
        context,
        metadata_source_path=normalized_metadata.source_path,
        chunk_index=normalized_metadata.chunk_index,
    )
    if normalized_metadata.source_path != context.source_path:
        message = _build_record_format_error_message(
            reason=REASON_STORED_SOURCE_PATH_MISMATCH,
            field_name=SOURCE_PATH_KEY,
            value=normalized_metadata.source_path,
            context=normalized_context,
        )
        raise ChunkStoreRecordFormatError(message)
    if not isinstance(raw_chunk.chunk_id, str) or raw_chunk.chunk_id != expected_id:
        message = _build_record_format_error_message(
            reason="stored id does not match metadata",
            field_name=IDS_KEY,
            value=raw_chunk.chunk_id,
            context=normalized_context,
        )
        raise ChunkStoreRecordFormatError(message)

    return StoredChunk(
        id=raw_chunk.chunk_id,
        text=raw_chunk.document,
        embedding=normalized_embedding,
        metadata=normalized_metadata,
    )


def _validate_record_embedding(
    embedding: object,
    *,
    context: _RecordValidationContext,
) -> list[float]:
    if not isinstance(embedding, list) or not embedding:
        message = _build_record_format_error_message(
            reason="stored embedding must be a non-empty list",
            field_name=EMBEDDINGS_KEY,
            value=embedding,
            context=context,
        )
        raise ChunkStoreRecordFormatError(message)

    normalized: list[float] = []
    for index, value in enumerate(embedding):
        if not isinstance(value, Real) or isinstance(value, bool):
            raise ChunkStoreRecordFormatError(
                _build_record_format_error_message(
                    reason=(REASON_STORED_EMBEDDING_VALUES_MUST_BE_FINITE_NUMBERS),
                    field_name=f"{EMBEDDINGS_KEY}[{index}]",
                    value=value,
                    context=context,
                ),
            )
        numeric_value = float(value)
        if not math.isfinite(numeric_value):
            raise ChunkStoreRecordFormatError(
                _build_record_format_error_message(
                    reason=(REASON_STORED_EMBEDDING_VALUES_MUST_BE_FINITE_NUMBERS),
                    field_name=f"{EMBEDDINGS_KEY}[{index}]",
                    value=value,
                    context=context,
                ),
            )
        normalized.append(numeric_value)
    return normalized


def _normalize_metadata(
    metadata: object,
    *,
    context: _RecordValidationContext,
) -> StoredChunkMetadata:
    validated_metadata = _validate_raw_metadata(
        metadata,
        context=context,
    )

    required_fields = (
        SOURCE_PATH_KEY,
        CHUNK_INDEX_KEY,
        HEADERS_KEY,
        TAGS_KEY,
        CREATED_AT_KEY,
        UPDATED_AT_KEY,
    )
    for field_name in required_fields:
        if field_name not in validated_metadata:
            message = _build_record_format_error_message(
                reason="stored metadata missing required field",
                field_name=field_name,
                context=context,
            )
            raise ChunkStoreRecordFormatError(message)

    normalized_source_path = _validate_record_source_path(
        validated_metadata[SOURCE_PATH_KEY],
        context=context,
    )
    metadata_context = _with_record_metadata(
        context,
        metadata_source_path=normalized_source_path,
    )
    chunk_index = _validate_record_chunk_index(
        validated_metadata[CHUNK_INDEX_KEY],
        context=metadata_context,
    )
    field_context = _with_record_metadata(
        metadata_context,
        chunk_index=chunk_index,
    )
    headers = _validate_record_string_field(
        validated_metadata[HEADERS_KEY],
        field_name=HEADERS_KEY,
        context=field_context,
    )
    tags = _validate_record_tags(
        validated_metadata[TAGS_KEY],
        context=field_context,
    )
    created_at = _validate_record_string_field(
        validated_metadata[CREATED_AT_KEY],
        field_name=CREATED_AT_KEY,
        context=field_context,
    )
    updated_at = _validate_record_string_field(
        validated_metadata[UPDATED_AT_KEY],
        field_name=UPDATED_AT_KEY,
        context=field_context,
    )

    return StoredChunkMetadata(
        source_path=normalized_source_path,
        chunk_index=chunk_index,
        headers=headers,
        tags=tags,
        created_at=created_at,
        updated_at=updated_at,
    )


def _validate_raw_metadata(
    metadata: object,
    *,
    context: _RecordValidationContext,
) -> _ChunkStoreRawMetadata:
    if not isinstance(metadata, dict):
        message = _build_record_format_error_message(
            reason="stored metadata must be a dict",
            field_name=METADATAS_KEY,
            value=metadata,
            context=context,
        )
        raise ChunkStoreRecordFormatError(message)
    return cast("_ChunkStoreRawMetadata", metadata)


def _validate_record_source_path(
    stored_source_path: object,
    *,
    context: _RecordValidationContext,
) -> str:
    if not isinstance(stored_source_path, str) or stored_source_path == "":
        message = _build_record_format_error_message(
            reason="stored source_path must be a non-empty string",
            field_name=SOURCE_PATH_KEY,
            value=stored_source_path,
            context=context,
        )
        raise ChunkStoreRecordFormatError(
            message,
        )
    return stored_source_path


def _validate_record_chunk_index(
    chunk_index: object,
    *,
    context: _RecordValidationContext,
) -> int:
    if (
        not isinstance(chunk_index, int)
        or isinstance(chunk_index, bool)
        or chunk_index < MINIMUM_CHUNK_INDEX
    ):
        message = _build_record_format_error_message(
            reason="stored chunk_index must be a non-negative integer",
            field_name=CHUNK_INDEX_KEY,
            value=chunk_index,
            context=context,
        )
        raise ChunkStoreRecordFormatError(
            message,
        )
    return chunk_index


def _validate_record_string_field(
    value: object,
    *,
    field_name: str,
    context: _RecordValidationContext,
) -> str:
    if not isinstance(value, str):
        message = _build_record_format_error_message(
            reason=f"stored {field_name} must be a string",
            field_name=field_name,
            value=value,
            context=context,
        )
        raise ChunkStoreRecordFormatError(message)
    return value


def _validate_record_tags(
    tags: object,
    *,
    context: _RecordValidationContext,
) -> list[str]:
    if not isinstance(tags, list):
        message = _build_record_format_error_message(
            reason="stored tags must be a list[str]",
            field_name=TAGS_KEY,
            value=tags,
            context=context,
        )
        raise ChunkStoreRecordFormatError(message)
    for index, tag in enumerate(tags):
        if not isinstance(tag, str):
            message = _build_record_format_error_message(
                reason="stored tags must contain only strings",
                field_name=f"{TAGS_KEY}[{index}]",
                value=tag,
                context=context,
            )
            raise ChunkStoreRecordFormatError(message)
    return list(tags)


def _with_input_chunk_index(
    context: _InputValidationContext,
    chunk_index: int,
) -> _InputValidationContext:
    return _InputValidationContext(
        operation=context.operation,
        source_path=context.source_path,
        chunk_index=chunk_index,
    )


def _with_record_metadata(
    context: _RecordValidationContext,
    *,
    metadata_source_path: str | None = None,
    chunk_index: int | None = None,
) -> _RecordValidationContext:
    return _RecordValidationContext(
        operation=context.operation,
        source_path=context.source_path,
        record_index=context.record_index,
        metadata_source_path=(
            metadata_source_path
            if metadata_source_path is not None
            else context.metadata_source_path
        ),
        chunk_index=chunk_index if chunk_index is not None else context.chunk_index,
    )


def _build_input_validation_error_message(
    field_name: str,
    reason: str,
    value: object,
    context: _InputValidationContext,
) -> str:
    details = [f"field={field_name!r}", f"value={value!r}"]
    if context.source_path is not None:
        details.append(f"{SOURCE_PATH_KEY}={context.source_path!r}")
    if context.chunk_index is not None:
        details.append(f"{CHUNK_INDEX_KEY}={context.chunk_index}")
    return f"{context.operation} validation failed: {reason} ({', '.join(details)})"


def _build_record_format_error_message(
    reason: str,
    context: _RecordValidationContext,
    field_name: str | None = None,
    value: object = _MISSING,
) -> str:
    details = [
        f"operation={context.operation!r}",
        f"{SOURCE_PATH_KEY}={context.source_path!r}",
    ]
    if field_name is not None:
        details.append(f"field={field_name!r}")
    if context.record_index is not None:
        details.append(f"record_index={context.record_index}")
    if context.metadata_source_path is not None:
        details.append(
            f"metadata_{SOURCE_PATH_KEY}={context.metadata_source_path!r}",
        )
    if context.chunk_index is not None:
        details.append(f"{CHUNK_INDEX_KEY}={context.chunk_index}")
    if value is not _MISSING:
        details.append(f"value={value!r}")
    return f"{RECORD_FORMAT_ERROR_PREFIX}: {reason} ({', '.join(details)})"


def _get_vector_dimension(chunks: list[StoredChunk]) -> int | None:
    if not chunks:
        return None
    return len(chunks[FIRST_ITEM_INDEX].embedding)


__all__ = [
    "ChromaChunkStore",
    "ChunkCollection",
    "ChunkStoreBackendError",
    "ChunkStoreDuplicateChunkIndexError",
    "ChunkStoreInputError",
    "ChunkStoreRecordFormatError",
    "StoredChunk",
    "StoredChunkMetadata",
]
