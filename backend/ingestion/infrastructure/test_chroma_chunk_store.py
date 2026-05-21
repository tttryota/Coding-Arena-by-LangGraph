import copy
import math
from collections.abc import MutableMapping
from typing import Any, cast

import pytest
from structlog.testing import capture_logs

from ingestion.infrastructure.batch_scheduler_types import (
    ChunkStoreChunkInput,
    ChunkStoreDeleteResult,
    ChunkStoreUpsertInput,
    ChunkStoreUpsertResult,
)
from ingestion.infrastructure.chroma_chunk_store import (
    ChromaChunkStore,
    ChunkCollection,
    ChunkStoreBackendError,
    ChunkStoreDuplicateChunkIndexError,
    ChunkStoreInputError,
    ChunkStoreRecordFormatError,
    StoredChunk,
)


class _ChunkCollectionDouble:
    def __init__(
        self,
        *,
        records: list[dict[str, object]] | None = None,
        raw_get_result: dict[str, object] | None = None,
        upsert_error: Exception | None = None,
        get_error: Exception | None = None,
        delete_error: Exception | None = None,
    ) -> None:
        self._records = copy.deepcopy(records or [])
        self._raw_get_result = copy.deepcopy(raw_get_result)
        self._upsert_error = upsert_error
        self._get_error = get_error
        self._delete_error = delete_error
        self.upsert_calls: list[dict[str, object]] = []
        self.get_calls: list[dict[str, object]] = []
        self.delete_calls: list[dict[str, object]] = []

    @property
    def records(self) -> list[dict[str, object]]:
        return copy.deepcopy(self._records)

    def upsert(
        self,
        ids: list[str],
        documents: list[str],
        embeddings: list[list[float]],
        metadatas: list[dict[str, object]],
    ) -> None:
        self.upsert_calls.append(
            {
                "ids": list(ids),
                "documents": list(documents),
                "embeddings": [list(embedding) for embedding in embeddings],
                "metadatas": copy.deepcopy(metadatas),
            },
        )
        if self._upsert_error is not None:
            raise self._upsert_error

        by_id = {record["id"]: copy.deepcopy(record) for record in self._records}
        for chunk_id, document, embedding, metadata in zip(
            ids,
            documents,
            embeddings,
            metadatas,
            strict=True,
        ):
            by_id[chunk_id] = {
                "id": chunk_id,
                "document": document,
                "embedding": list(embedding),
                "metadata": copy.deepcopy(metadata),
            }
        self._records = list(by_id.values())

    def get(self, where: dict[str, object]) -> dict[str, object]:
        self.get_calls.append(copy.deepcopy(where))
        if self._get_error is not None:
            raise self._get_error
        if self._raw_get_result is not None:
            return copy.deepcopy(self._raw_get_result)

        source_path = where["source_path"]
        matched_records = [
            record
            for record in self._records
            if _record_source_path(record) == source_path
        ]
        return {
            "ids": [record["id"] for record in matched_records],
            "documents": [record["document"] for record in matched_records],
            "embeddings": [
                copy.deepcopy(record["embedding"]) for record in matched_records
            ],
            "metadatas": [
                copy.deepcopy(record["metadata"]) for record in matched_records
            ],
        }

    def delete(self, where: dict[str, object]) -> None:
        self.delete_calls.append(copy.deepcopy(where))
        if self._delete_error is not None:
            raise self._delete_error

        source_path = where["source_path"]
        self._records = [
            record
            for record in self._records
            if _record_source_path(record) != source_path
        ]


def _record_source_path(record: dict[str, object]) -> object:
    metadata = cast("MutableMapping[str, object]", record["metadata"])
    return metadata["source_path"]


def _make_store(collection: _ChunkCollectionDouble) -> ChromaChunkStore:
    return ChromaChunkStore(cast("ChunkCollection", collection))


def _make_chunk(
    chunk_index: object,
    *,
    text: object = "TypeScriptのジェネリクスは型引数で再利用性を高める。",
    embedding: object = None,
    headers: object = "TypeScript入門 > ジェネリクス",
    tags: object = None,
    created_at: object = "2026-05-17T10:00:00+09:00",
    updated_at: object = "2026-05-17T10:00:00+09:00",
) -> ChunkStoreChunkInput:
    if embedding is None:
        embedding = [0.12, -0.03, 0.44, 0.08]
    if tags is None:
        tags = ["TypeScript"]
    return ChunkStoreChunkInput(
        chunk_index=cast("int", chunk_index),
        text=cast("str", text),
        embedding=cast("list[float]", embedding),
        headers=cast("str", headers),
        tags=cast("list[str]", tags),
        created_at=cast("str", created_at),
        updated_at=cast("str", updated_at),
    )


def _make_upsert_input(
    *,
    source_path: str,
    chunks: list[ChunkStoreChunkInput],
) -> ChunkStoreUpsertInput:
    return ChunkStoreUpsertInput(source_path=source_path, chunks=chunks)


def _make_raw_record(
    source_path: str,
    chunk_index: int,
    *,
    text: str,
    embedding: list[float],
    headers: str = "TypeScript入門 > ジェネリクス",
    tags: list[str] | None = None,
    created_at: str = "2026-05-17T10:00:00+09:00",
    updated_at: str = "2026-05-17T10:00:00+09:00",
) -> dict[str, object]:
    if tags is None:
        tags = ["TypeScript"]
    return {
        "id": f"{source_path}_{chunk_index}",
        "document": text,
        "embedding": list(embedding),
        "metadata": {
            "source_path": source_path,
            "chunk_index": chunk_index,
            "headers": headers,
            "tags": list(tags),
            "created_at": created_at,
            "updated_at": updated_at,
        },
    }


def _make_raw_get_result(records: list[dict[str, object]]) -> dict[str, object]:
    return {
        "ids": [record["id"] for record in records],
        "documents": [record["document"] for record in records],
        "embeddings": [copy.deepcopy(record["embedding"]) for record in records],
        "metadatas": [copy.deepcopy(record["metadata"]) for record in records],
    }


def _normalize_upsert_result(result: ChunkStoreUpsertResult) -> dict[str, object]:
    return {
        "source_path": result.source_path,
        "stored_count": result.stored_count,
        "stored_ids": list(result.stored_ids),
    }


def _normalize_delete_result(result: ChunkStoreDeleteResult) -> dict[str, object]:
    return {
        "source_path": result.source_path,
        "deleted_count": result.deleted_count,
    }


def _normalize_stored_chunks(chunks: list[StoredChunk]) -> list[dict[str, object]]:
    normalized: list[dict[str, object]] = []
    for chunk in chunks:
        metadata = chunk.metadata
        normalized.append(
            {
                "id": chunk.id,
                "text": chunk.text,
                "embedding": list(chunk.embedding),
                "metadata": {
                    "source_path": metadata.source_path,
                    "chunk_index": metadata.chunk_index,
                    "headers": metadata.headers,
                    "tags": list(metadata.tags),
                    "created_at": metadata.created_at,
                    "updated_at": metadata.updated_at,
                },
            },
        )
    return normalized


def _find_log_events(
    log_output: list[MutableMapping[str, object]],
    event_name: str,
) -> list[MutableMapping[str, object]]:
    return [entry for entry in log_output if entry.get("event") == event_name]


def _assert_single_log_event_includes(
    log_output: list[MutableMapping[str, object]],
    event_name: str,
    expected_fields: dict[str, object],
) -> MutableMapping[str, object]:
    matching_logs = _find_log_events(log_output, event_name)
    assert len(matching_logs) == 1
    log_entry = matching_logs[0]
    assert set(expected_fields) <= set(log_entry)
    assert {field_name: log_entry[field_name] for field_name in expected_fields} == (
        expected_fields
    )
    return log_entry


def _assert_log_entry_has_exc_info(log_entry: MutableMapping[str, object]) -> None:
    assert log_entry.get("exc_info") is True


class TestChromaChunkStore:
    # ------------------------------------------------------------------ #
    # Phase 1: minimal skeleton
    # ------------------------------------------------------------------ #

    def test_chunk_store_tc_01_upsert_returns_natural_key_ids_in_input_order(
        self,
    ) -> None:
        collection = _ChunkCollectionDouble()
        store = _make_store(collection)
        upsert_input = _make_upsert_input(
            source_path="study/typescript/generics.md",
            chunks=[
                _make_chunk(0),
                _make_chunk(
                    1,
                    text="extends で型制約を付与できる。",
                    embedding=[0.09, 0.11, -0.05, 0.27],
                ),
            ],
        )

        with capture_logs() as log_output:
            result = store.upsert_chunks(upsert_input)

        assert _normalize_upsert_result(result) == {
            "source_path": "study/typescript/generics.md",
            "stored_count": 2,
            "stored_ids": [
                "study/typescript/generics.md_0",
                "study/typescript/generics.md_1",
            ],
        }
        assert collection.upsert_calls == [
            {
                "ids": [
                    "study/typescript/generics.md_0",
                    "study/typescript/generics.md_1",
                ],
                "documents": [
                    "TypeScriptのジェネリクスは型引数で再利用性を高める。",
                    "extends で型制約を付与できる。",
                ],
                "embeddings": [
                    [0.12, -0.03, 0.44, 0.08],
                    [0.09, 0.11, -0.05, 0.27],
                ],
                "metadatas": [
                    {
                        "source_path": "study/typescript/generics.md",
                        "chunk_index": 0,
                        "headers": "TypeScript入門 > ジェネリクス",
                        "tags": ["TypeScript"],
                        "created_at": "2026-05-17T10:00:00+09:00",
                        "updated_at": "2026-05-17T10:00:00+09:00",
                    },
                    {
                        "source_path": "study/typescript/generics.md",
                        "chunk_index": 1,
                        "headers": "TypeScript入門 > ジェネリクス",
                        "tags": ["TypeScript"],
                        "created_at": "2026-05-17T10:00:00+09:00",
                        "updated_at": "2026-05-17T10:00:00+09:00",
                    },
                ],
            },
        ]
        _assert_single_log_event_includes(
            log_output,
            "chunk_store_upsert_completed",
            {
                "source_path": "study/typescript/generics.md",
                "chunk_count": 2,
                "stored_count": 2,
                "vector_dimension": 4,
            },
        )

    def test_chunk_store_tc_02_get_returns_chunks_sorted_by_chunk_index(self) -> None:
        source_path = "study/typescript/generics.md"
        collection = _ChunkCollectionDouble(
            raw_get_result=_make_raw_get_result(
                [
                    _make_raw_record(
                        source_path,
                        1,
                        text="extends で型制約を付与できる。",
                        embedding=[0.09, 0.11, -0.05, 0.27],
                    ),
                    _make_raw_record(
                        source_path,
                        0,
                        text="TypeScriptのジェネリクスは型引数で再利用性を高める。",
                        embedding=[0.12, -0.03, 0.44, 0.08],
                    ),
                ],
            ),
        )
        store = _make_store(collection)

        with capture_logs() as log_output:
            result = store.get_by_source_path(source_path)

        assert _normalize_stored_chunks(result) == [
            {
                "id": "study/typescript/generics.md_0",
                "text": "TypeScriptのジェネリクスは型引数で再利用性を高める。",
                "embedding": [0.12, -0.03, 0.44, 0.08],
                "metadata": {
                    "source_path": "study/typescript/generics.md",
                    "chunk_index": 0,
                    "headers": "TypeScript入門 > ジェネリクス",
                    "tags": ["TypeScript"],
                    "created_at": "2026-05-17T10:00:00+09:00",
                    "updated_at": "2026-05-17T10:00:00+09:00",
                },
            },
            {
                "id": "study/typescript/generics.md_1",
                "text": "extends で型制約を付与できる。",
                "embedding": [0.09, 0.11, -0.05, 0.27],
                "metadata": {
                    "source_path": "study/typescript/generics.md",
                    "chunk_index": 1,
                    "headers": "TypeScript入門 > ジェネリクス",
                    "tags": ["TypeScript"],
                    "created_at": "2026-05-17T10:00:00+09:00",
                    "updated_at": "2026-05-17T10:00:00+09:00",
                },
            },
        ]
        assert collection.get_calls == [{"source_path": source_path}]
        _assert_single_log_event_includes(
            log_output,
            "chunk_store_get_completed",
            {
                "source_path": source_path,
                "returned_count": 2,
            },
        )

    def test_chunk_store_tc_03_delete_removes_only_exact_source_path_records(
        self,
    ) -> None:
        source_path = "study/typescript/generics.md"
        bak_path = "study/typescript/generics.md.bak"
        collection = _ChunkCollectionDouble(
            records=[
                _make_raw_record(
                    source_path,
                    0,
                    text="TypeScriptのジェネリクスは型引数で再利用性を高める。",
                    embedding=[0.12, -0.03, 0.44, 0.08],
                ),
                _make_raw_record(
                    source_path,
                    1,
                    text="extends で型制約を付与できる。",
                    embedding=[0.09, 0.11, -0.05, 0.27],
                ),
                _make_raw_record(
                    bak_path,
                    0,
                    text="bak 側のチャンク",
                    embedding=[0.2, 0.3, 0.4, 0.5],
                ),
            ],
        )
        store = _make_store(collection)

        with capture_logs() as log_output:
            result = store.delete_by_source_path(source_path)

        assert _normalize_delete_result(result) == {
            "source_path": source_path,
            "deleted_count": 2,
        }
        assert collection.delete_calls == [{"source_path": source_path}]
        assert collection.records == [
            _make_raw_record(
                bak_path,
                0,
                text="bak 側のチャンク",
                embedding=[0.2, 0.3, 0.4, 0.5],
            ),
        ]
        _assert_single_log_event_includes(
            log_output,
            "chunk_store_delete_completed",
            {
                "source_path": source_path,
                "deleted_count": 2,
            },
        )

    # ------------------------------------------------------------------ #
    # Phase 2: core logic
    # ------------------------------------------------------------------ #

    def test_chunk_store_tc_10_empty_batch_short_circuits_without_backend_upsert(
        self,
    ) -> None:
        collection = _ChunkCollectionDouble()
        store = _make_store(collection)
        upsert_input = _make_upsert_input(source_path="study/empty.md", chunks=[])

        with capture_logs() as log_output:
            result = store.upsert_chunks(upsert_input)

        assert _normalize_upsert_result(result) == {
            "source_path": "study/empty.md",
            "stored_count": 0,
            "stored_ids": [],
        }
        assert collection.upsert_calls == []
        _assert_single_log_event_includes(
            log_output,
            "chunk_store_upsert_completed",
            {
                "source_path": "study/empty.md",
                "chunk_count": 0,
                "stored_count": 0,
                "vector_dimension": None,
            },
        )

    def test_chunk_store_tc_11_duplicate_chunk_index_is_rejected_before_upsert(
        self,
    ) -> None:
        collection = _ChunkCollectionDouble()
        store = _make_store(collection)
        upsert_input = _make_upsert_input(
            source_path="study/invalid.md",
            chunks=[
                _make_chunk(
                    0,
                    text="本文A",
                    embedding=[0.1, 0.2],
                    headers="",
                    tags=[],
                ),
                _make_chunk(
                    0,
                    text="本文B",
                    embedding=[0.3, 0.4],
                    headers="",
                    tags=[],
                ),
            ],
        )

        with pytest.raises(ChunkStoreDuplicateChunkIndexError) as exc_info:
            store.upsert_chunks(upsert_input)

        assert (
            str(exc_info.value) == "duplicate chunk_index in upsert batch "
            "(source_path='study/invalid.md', chunk_index=0)"
        )
        assert collection.upsert_calls == []

    def test_chunk_store_tc_12_get_uses_exact_source_path_not_prefix(
        self,
    ) -> None:
        source_path = "study/typescript/generics.md"
        collection = _ChunkCollectionDouble(
            records=[
                _make_raw_record(
                    "study/typescript/generics.md.bak",
                    0,
                    text="bak 側のチャンク",
                    embedding=[0.2, 0.3, 0.4, 0.5],
                ),
            ],
        )
        store = _make_store(collection)

        with capture_logs() as log_output:
            result = store.get_by_source_path(source_path)

        assert result == []
        assert collection.get_calls == [{"source_path": source_path}]
        _assert_single_log_event_includes(
            log_output,
            "chunk_store_get_completed",
            {
                "source_path": source_path,
                "returned_count": 0,
            },
        )

    def test_chunk_store_tc_13_delete_uses_exact_source_path_not_prefix(
        self,
    ) -> None:
        source_path = "study/typescript/generics.md"
        bak_path = "study/typescript/generics.md.bak"
        collection = _ChunkCollectionDouble(
            records=[
                _make_raw_record(
                    bak_path,
                    0,
                    text="bak 側のチャンク",
                    embedding=[0.2, 0.3, 0.4, 0.5],
                ),
            ],
        )
        store = _make_store(collection)

        with capture_logs() as log_output:
            result = store.delete_by_source_path(source_path)

        assert _normalize_delete_result(result) == {
            "source_path": source_path,
            "deleted_count": 0,
        }
        assert collection.delete_calls == [{"source_path": source_path}]
        assert collection.records == [
            _make_raw_record(
                bak_path,
                0,
                text="bak 側のチャンク",
                embedding=[0.2, 0.3, 0.4, 0.5],
            ),
        ]
        _assert_single_log_event_includes(
            log_output,
            "chunk_store_delete_completed",
            {
                "source_path": source_path,
                "deleted_count": 0,
            },
        )

    def test_chunk_store_tc_14_validation_error_wins_over_duplicate_chunk_index(
        self,
    ) -> None:
        collection = _ChunkCollectionDouble()
        store = _make_store(collection)
        upsert_input = _make_upsert_input(
            source_path="study/invalid.md",
            chunks=[
                _make_chunk(0, text="本文A", embedding=[0.1, 0.2], headers="", tags=[]),
                _make_chunk(0, text="   ", embedding=[0.3, 0.4], headers="", tags=[]),
            ],
        )

        with pytest.raises(ChunkStoreInputError) as exc_info:
            store.upsert_chunks(upsert_input)

        assert exc_info.type is ChunkStoreInputError
        assert collection.upsert_calls == []

    # ------------------------------------------------------------------ #
    # Phase 3: edge cases
    # ------------------------------------------------------------------ #

    @pytest.mark.parametrize(
        "invalid_chunks",
        [
            [_make_chunk(0, text="   ")],
            [_make_chunk(-1)],
            [_make_chunk(0, embedding=[])],
            [_make_chunk(0, embedding=[0.1, "0.2"])],
            [_make_chunk(0, embedding=[0.1, math.nan])],
            [_make_chunk(0, embedding=[0.1, math.inf])],
            [_make_chunk(0, tags=["ok", 1])],
            [_make_chunk(0, headers=1)],
            [_make_chunk(0, created_at=1)],
            [_make_chunk(0, updated_at=None)],
            [
                _make_chunk(0, embedding=[0.1, 0.2]),
                _make_chunk(1, embedding=[0.3, 0.4, 0.5]),
            ],
        ],
    )
    def test_chunk_store_tc_20_upsert_rejects_contract_violations_as_input_error(
        self,
        invalid_chunks: list[ChunkStoreChunkInput],
    ) -> None:
        collection = _ChunkCollectionDouble()
        store = _make_store(collection)

        with pytest.raises(ChunkStoreInputError):
            store.upsert_chunks(
                _make_upsert_input(
                    source_path="study/invalid.md",
                    chunks=invalid_chunks,
                ),
            )

        assert collection.upsert_calls == []

    def test_chunk_store_tc_20_upsert_rejects_empty_source_path(self) -> None:
        collection = _ChunkCollectionDouble()
        store = _make_store(collection)

        with pytest.raises(ChunkStoreInputError):
            store.upsert_chunks(
                _make_upsert_input(source_path="", chunks=[]),
            )

        assert collection.upsert_calls == []

    @pytest.mark.parametrize(
        ("operation_name", "call"),
        [
            ("delete", lambda store: store.delete_by_source_path("")),
            ("get", lambda store: store.get_by_source_path("")),
        ],
    )
    def test_chunk_store_tc_21_delete_and_get_reject_empty_source_path(
        self,
        operation_name: str,
        call: Any,
    ) -> None:
        collection = _ChunkCollectionDouble()
        store = _make_store(collection)

        with pytest.raises(ChunkStoreInputError):
            call(store)

        if operation_name == "get":
            assert collection.get_calls == []
        if operation_name == "delete":
            assert collection.delete_calls == []

    def test_chunk_store_tc_22_get_rejects_id_metadata_source_path_mismatch(
        self,
    ) -> None:
        collection = _ChunkCollectionDouble(
            raw_get_result=_make_raw_get_result(
                [
                    {
                        "id": "study/b.md_0",
                        "document": "本文A",
                        "embedding": [0.1, 0.2],
                        "metadata": {
                            "source_path": "study/a.md",
                            "chunk_index": 0,
                            "headers": "",
                            "tags": [],
                            "created_at": "2026-05-17T10:00:00+09:00",
                            "updated_at": "2026-05-17T10:00:00+09:00",
                        },
                    },
                ],
            ),
        )
        store = _make_store(collection)

        with pytest.raises(ChunkStoreRecordFormatError):
            store.get_by_source_path("study/a.md")

    @pytest.mark.parametrize(
        "raw_get_result",
        [
            # Case A: metadata missing created_at
            {
                "ids": ["study/a.md_0"],
                "documents": ["本文A"],
                "embeddings": [[0.1, 0.2]],
                "metadatas": [
                    {
                        "source_path": "study/a.md",
                        "chunk_index": 0,
                        "headers": "",
                        "tags": [],
                        "updated_at": "2026-05-17T10:00:00+09:00",
                    },
                ],
            },
            # Case B: chunk_index = -1
            _make_raw_get_result(
                [
                    {
                        "id": "study/a.md_-1",
                        "document": "本文A",
                        "embedding": [0.1, 0.2],
                        "metadata": {
                            "source_path": "study/a.md",
                            "chunk_index": -1,
                            "headers": "",
                            "tags": [],
                            "created_at": "2026-05-17T10:00:00+09:00",
                            "updated_at": "2026-05-17T10:00:00+09:00",
                        },
                    },
                ],
            ),
            # Case B: chunk_index non-integer
            _make_raw_get_result(
                [
                    {
                        "id": "study/a.md_0",
                        "document": "本文A",
                        "embedding": [0.1, 0.2],
                        "metadata": {
                            "source_path": "study/a.md",
                            "chunk_index": "0",
                            "headers": "",
                            "tags": [],
                            "created_at": "2026-05-17T10:00:00+09:00",
                            "updated_at": "2026-05-17T10:00:00+09:00",
                        },
                    },
                ],
            ),
            # Case C: text missing (documents key absent)
            {
                "ids": ["study/a.md_0"],
                "embeddings": [[0.1, 0.2]],
                "metadatas": [
                    {
                        "source_path": "study/a.md",
                        "chunk_index": 0,
                        "headers": "",
                        "tags": [],
                        "created_at": "2026-05-17T10:00:00+09:00",
                        "updated_at": "2026-05-17T10:00:00+09:00",
                    },
                ],
            },
            # Case C: text not string
            _make_raw_get_result(
                [
                    {
                        "id": "study/a.md_0",
                        "document": 123,
                        "embedding": [0.1, 0.2],
                        "metadata": {
                            "source_path": "study/a.md",
                            "chunk_index": 0,
                            "headers": "",
                            "tags": [],
                            "created_at": "2026-05-17T10:00:00+09:00",
                            "updated_at": "2026-05-17T10:00:00+09:00",
                        },
                    },
                ],
            ),
            # Case D: embedding empty
            _make_raw_get_result(
                [
                    {
                        "id": "study/a.md_0",
                        "document": "本文A",
                        "embedding": [],
                        "metadata": {
                            "source_path": "study/a.md",
                            "chunk_index": 0,
                            "headers": "",
                            "tags": [],
                            "created_at": "2026-05-17T10:00:00+09:00",
                            "updated_at": "2026-05-17T10:00:00+09:00",
                        },
                    },
                ],
            ),
            # Case E: embedding not list
            _make_raw_get_result(
                [
                    {
                        "id": "study/a.md_0",
                        "document": "本文A",
                        "embedding": "0.1,0.2",
                        "metadata": {
                            "source_path": "study/a.md",
                            "chunk_index": 0,
                            "headers": "",
                            "tags": [],
                            "created_at": "2026-05-17T10:00:00+09:00",
                            "updated_at": "2026-05-17T10:00:00+09:00",
                        },
                    },
                ],
            ),
            # Case F: embedding contains NaN
            _make_raw_get_result(
                [
                    {
                        "id": "study/a.md_0",
                        "document": "本文A",
                        "embedding": [0.1, math.nan],
                        "metadata": {
                            "source_path": "study/a.md",
                            "chunk_index": 0,
                            "headers": "",
                            "tags": [],
                            "created_at": "2026-05-17T10:00:00+09:00",
                            "updated_at": "2026-05-17T10:00:00+09:00",
                        },
                    },
                ],
            ),
            # Case F: embedding contains inf
            _make_raw_get_result(
                [
                    {
                        "id": "study/a.md_0",
                        "document": "本文A",
                        "embedding": [0.1, math.inf],
                        "metadata": {
                            "source_path": "study/a.md",
                            "chunk_index": 0,
                            "headers": "",
                            "tags": [],
                            "created_at": "2026-05-17T10:00:00+09:00",
                            "updated_at": "2026-05-17T10:00:00+09:00",
                        },
                    },
                ],
            ),
            # Case F: embedding contains non-numeric
            _make_raw_get_result(
                [
                    {
                        "id": "study/a.md_0",
                        "document": "本文A",
                        "embedding": [0.1, "0.2"],
                        "metadata": {
                            "source_path": "study/a.md",
                            "chunk_index": 0,
                            "headers": "",
                            "tags": [],
                            "created_at": "2026-05-17T10:00:00+09:00",
                            "updated_at": "2026-05-17T10:00:00+09:00",
                        },
                    },
                ],
            ),
        ],
    )
    def test_chunk_store_tc_23_get_rejects_malformed_records_as_record_format_error(
        self,
        raw_get_result: dict[str, object],
    ) -> None:
        collection = _ChunkCollectionDouble(raw_get_result=raw_get_result)
        store = _make_store(collection)

        with pytest.raises(ChunkStoreRecordFormatError):
            store.get_by_source_path("study/a.md")

    # ------------------------------------------------------------------ #
    # Phase 4: external integration
    # ------------------------------------------------------------------ #

    def test_chunk_store_tc_30_upsert_backend_errors_are_wrapped_with_cause(
        self,
    ) -> None:
        source_path = "study/backend/infra.md"
        backend_error = TimeoutError("upsert timed out")
        collection = _ChunkCollectionDouble(upsert_error=backend_error)
        store = _make_store(collection)

        with (
            capture_logs() as log_output,
            pytest.raises(
                ChunkStoreBackendError,
            ) as exc_info,
        ):
            store.upsert_chunks(
                _make_upsert_input(
                    source_path=source_path,
                    chunks=[_make_chunk(0, text="本文A", embedding=[0.1, 0.2])],
                ),
            )

        assert exc_info.value.__cause__ is backend_error
        assert (
            str(exc_info.value) == "chunk store upsert failed for "
            "source_path='study/backend/infra.md', chunk_count=1"
        )
        log_entry = _assert_single_log_event_includes(
            log_output,
            "chunk_store_upsert_failed",
            {
                "source_path": source_path,
                "chunk_count": 1,
            },
        )
        assert log_entry["error_type"] == "TimeoutError"
        _assert_log_entry_has_exc_info(log_entry)

    def test_chunk_store_tc_31_get_backend_errors_are_wrapped_with_cause(
        self,
    ) -> None:
        source_path = "study/backend/infra.md"
        backend_error = ConnectionError("collection unavailable")
        collection = _ChunkCollectionDouble(get_error=backend_error)
        store = _make_store(collection)

        with (
            capture_logs() as log_output,
            pytest.raises(
                ChunkStoreBackendError,
            ) as exc_info,
        ):
            store.get_by_source_path(source_path)

        assert exc_info.value.__cause__ is backend_error
        assert (
            str(exc_info.value) == "chunk store get failed for "
            "source_path='study/backend/infra.md'"
        )
        log_entry = _assert_single_log_event_includes(
            log_output,
            "chunk_store_get_failed",
            {"source_path": source_path},
        )
        assert log_entry["error_type"] == "ConnectionError"
        _assert_log_entry_has_exc_info(log_entry)

    def test_chunk_store_tc_32_delete_backend_errors_are_wrapped_with_cause(
        self,
    ) -> None:
        source_path = "study/backend/infra.md"
        backend_error = RuntimeError("delete failed")
        collection = _ChunkCollectionDouble(delete_error=backend_error)
        store = _make_store(collection)

        with (
            capture_logs() as log_output,
            pytest.raises(
                ChunkStoreBackendError,
            ) as exc_info,
        ):
            store.delete_by_source_path(source_path)

        assert exc_info.value.__cause__ is backend_error
        assert (
            str(exc_info.value) == "chunk store delete failed for "
            "source_path='study/backend/infra.md'"
        )
        log_entry = _assert_single_log_event_includes(
            log_output,
            "chunk_store_delete_failed",
            {"source_path": source_path},
        )
        assert log_entry["error_type"] == "RuntimeError"
        _assert_log_entry_has_exc_info(log_entry)

    @pytest.mark.parametrize(
        "raw_get_result",
        [
            pytest.param({"documents": []}, id="ids-missing"),
            pytest.param({"ids": "not-a-list"}, id="ids-not-list"),
        ],
    )
    def test_chunk_store_tc_32_delete_raises_backend_error_for_malformed_get_response(
        self,
        raw_get_result: dict[str, object],
    ) -> None:
        source_path = "study/typescript/generics.md"
        collection = _ChunkCollectionDouble(raw_get_result=raw_get_result)
        store = _make_store(collection)

        with (
            capture_logs() as log_output,
            pytest.raises(ChunkStoreBackendError),
        ):
            store.delete_by_source_path(source_path)

        log_entry = _assert_single_log_event_includes(
            log_output,
            "chunk_store_delete_failed",
            {"source_path": source_path},
        )
        assert log_entry["error_type"] == "BackendResponseError"
        assert "exc_info" not in log_entry
