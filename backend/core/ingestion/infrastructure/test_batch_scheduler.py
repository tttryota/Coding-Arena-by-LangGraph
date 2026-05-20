from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, cast

import pytest
from structlog.testing import capture_logs

from core.ingestion.domain.chunk_splitter import ChunkSplitResult
from core.ingestion.infrastructure.batch_executor import (
    BatchExecutionConfig,
    run_once,
)
from core.ingestion.infrastructure.batch_scheduler_types import (
    BatchRunStatus,
    BatchRunSummary,
    BatchSchedulerConfigError,
    BatchTrigger,
    ChunkStoreDeleteResult,
    ChunkStoreUpsertInput,
    ChunkStoreUpsertResult,
)
from core.ingestion.infrastructure.embedder_types import (
    ChunkEmbeddingResult,
    EmbeddingModelCallError,
)
from core.ingestion.infrastructure.tagger import ChunkTaggingResult

if TYPE_CHECKING:
    from collections.abc import MutableMapping
    from pathlib import Path

    from core.ingestion.infrastructure.file_diff_detector import FileDiffResult

_TARGET_PATH = "/vault/study"


class ChunkStoreWriteError(Exception):
    pass


@dataclass(frozen=True)
class _FileDiffResultFixture:
    target_path: str
    new_files: list[str]
    updated_files: list[str]
    deleted_files: list[str]
    new_count: int
    updated_count: int
    deleted_count: int



@dataclass
class _Dependencies:
    diff_detector: _RecordingDiffDetector
    markdown_loader: _RecordingMarkdownLoader
    chunk_splitter: _RecordingChunkSplitter
    chunk_tagger: _RecordingChunkTagger
    embedder: _RecordingEmbedder
    chunk_store: _RecordingChunkStore
    operations: list[tuple[str, str]]


class _RecordingDiffDetector:
    def __init__(
        self,
        *,
        result: FileDiffResult | None = None,
        error: Exception | None = None,
    ) -> None:
        self._result = result
        self._error = error
        self.calls: list[str] = []

    def detect(self, target_path: str | Path) -> FileDiffResult:
        self.calls.append(str(target_path))
        if self._error is not None:
            raise self._error
        assert self._result is not None
        return self._result


class _RecordingMarkdownLoader:
    def __init__(
        self,
        operations: list[tuple[str, str]],
        *,
        contents: dict[str, str] | None = None,
        errors: dict[str, Exception] | None = None,
    ) -> None:
        self._operations = operations
        self._contents = dict(contents or {})
        self._errors = dict(errors or {})
        self.calls: list[str] = []

    def load(self, source_path: str | Path) -> str:
        normalized = str(source_path)
        self.calls.append(normalized)
        self._operations.append(("load", normalized))
        error = self._errors.get(normalized)
        if error is not None:
            raise error
        return self._contents.get(normalized, f"body::{normalized}")


class _RecordingChunkSplitter:
    def __init__(
        self,
        operations: list[tuple[str, str]],
        *,
        chunk_counts: dict[str, int] | None = None,
        empty_sources: set[str] | None = None,
        errors: dict[str, Exception] | None = None,
    ) -> None:
        self._operations = operations
        self._chunk_counts = dict(chunk_counts or {})
        self._empty_sources = set(empty_sources or set())
        self._errors = dict(errors or {})
        self.calls: list[str] = []

    def split(
        self,
        markdown_text: str,
        *,
        source_path: str | None = None,
    ) -> list[ChunkSplitResult]:
        resolved_path = source_path or markdown_text
        self.calls.append(resolved_path)
        self._operations.append(("split", resolved_path))
        error = self._errors.get(resolved_path)
        if error is not None:
            raise error
        if resolved_path in self._empty_sources:
            return []
        chunk_count = self._chunk_counts.get(resolved_path, 1)
        return [
            ChunkSplitResult(
                content=f"chunk::{resolved_path}::{chunk_index}",
                heading_path=[resolved_path],
                token_count=32,
            )
            for chunk_index in range(chunk_count)
        ]


class _RecordingChunkTagger:
    def __init__(
        self,
        operations: list[tuple[str, str]],
        *,
        errors: dict[str, Exception] | None = None,
    ) -> None:
        self._operations = operations
        self._errors = dict(errors or {})
        self.calls: list[str] = []

    def tag(
        self,
        chunks: list[ChunkSplitResult],
        *,
        source_path: str,
    ) -> list[ChunkTaggingResult]:
        self.calls.append(source_path)
        self._operations.append(("tag", source_path))
        error = self._errors.get(source_path)
        if error is not None:
            raise error
        return [
            ChunkTaggingResult(
                chunk_index=index,
                tags=[f"tag:{source_path}:{index}"],
            )
            for index in range(len(chunks))
        ]


class _RecordingEmbedder:
    def __init__(
        self,
        operations: list[tuple[str, str]],
        *,
        errors: dict[str, Exception] | None = None,
    ) -> None:
        self._operations = operations
        self._errors = dict(errors or {})
        self.calls: list[str] = []

    def embed(
        self,
        chunks: list[ChunkSplitResult],
        *,
        source_path: str,
    ) -> list[ChunkEmbeddingResult]:
        self.calls.append(source_path)
        self._operations.append(("embed", source_path))
        error = self._errors.get(source_path)
        if error is not None:
            raise error
        return [
            ChunkEmbeddingResult(
                chunk_index=index,
                embedding=[0.1 + float(index), 0.2],
            )
            for index in range(len(chunks))
        ]


class _RecordingChunkStore:
    def __init__(
        self,
        operations: list[tuple[str, str]],
        *,
        delete_errors: dict[str, Exception] | None = None,
        upsert_errors: dict[str, Exception] | None = None,
    ) -> None:
        self._operations = operations
        self._delete_errors = dict(delete_errors or {})
        self._upsert_errors = dict(upsert_errors or {})
        self.delete_calls: list[str] = []
        self.upsert_calls: list[str] = []

    def delete_by_source_path(self, source_path: str | Path) -> ChunkStoreDeleteResult:
        normalized = str(source_path)
        self.delete_calls.append(normalized)
        self._operations.append(("delete_by_source_path", normalized))
        error = self._delete_errors.get(normalized)
        if error is not None:
            raise error
        return ChunkStoreDeleteResult(
            source_path=normalized,
            deleted_count=1,
        )

    def upsert_chunks(
        self, upsert_input: ChunkStoreUpsertInput,
    ) -> ChunkStoreUpsertResult:
        source_path = str(upsert_input.source_path)
        self.upsert_calls.append(source_path)
        self._operations.append(("upsert_chunks", source_path))
        error = self._upsert_errors.get(source_path)
        if error is not None:
            raise error
        chunk_count = len(upsert_input.chunks)
        return ChunkStoreUpsertResult(
            source_path=source_path,
            stored_count=chunk_count,
            stored_ids=[
                f"{source_path}#{i}" for i in range(chunk_count)
            ],
        )


def _make_diff_result(
    *,
    new_files: list[str],
    updated_files: list[str],
    deleted_files: list[str],
) -> FileDiffResult:
    return cast(
        "FileDiffResult",
        _FileDiffResultFixture(
            target_path=_TARGET_PATH,
            new_files=list(new_files),
            updated_files=list(updated_files),
            deleted_files=list(deleted_files),
            new_count=len(new_files),
            updated_count=len(updated_files),
            deleted_count=len(deleted_files),
        ),
    )


def _make_dependencies(
    diff_result: FileDiffResult,
    *,
    loader_contents: dict[str, str] | None = None,
    loader_errors: dict[str, Exception] | None = None,
    split_chunk_counts: dict[str, int] | None = None,
    split_empty_sources: set[str] | None = None,
    split_errors: dict[str, Exception] | None = None,
    tag_errors: dict[str, Exception] | None = None,
    embed_errors: dict[str, Exception] | None = None,
    delete_errors: dict[str, Exception] | None = None,
    upsert_errors: dict[str, Exception] | None = None,
) -> _Dependencies:
    operations: list[tuple[str, str]] = []
    diff_detector = _RecordingDiffDetector(result=diff_result)
    markdown_loader = _RecordingMarkdownLoader(
        operations,
        contents=loader_contents,
        errors=loader_errors,
    )
    chunk_splitter = _RecordingChunkSplitter(
        operations,
        chunk_counts=split_chunk_counts,
        empty_sources=split_empty_sources,
        errors=split_errors,
    )
    chunk_tagger = _RecordingChunkTagger(operations, errors=tag_errors)
    embedder = _RecordingEmbedder(operations, errors=embed_errors)
    chunk_store = _RecordingChunkStore(
        operations,
        delete_errors=delete_errors,
        upsert_errors=upsert_errors,
    )
    return _Dependencies(
        diff_detector=diff_detector,
        markdown_loader=markdown_loader,
        chunk_splitter=chunk_splitter,
        chunk_tagger=chunk_tagger,
        embedder=embedder,
        chunk_store=chunk_store,
        operations=operations,
    )


def _make_config(
    dependencies: _Dependencies,
    *,
    target_path: str = _TARGET_PATH,
) -> BatchExecutionConfig:
    return BatchExecutionConfig(
        target_path=target_path,
        diff_detector=dependencies.diff_detector,
        markdown_loader=dependencies.markdown_loader,
        chunk_splitter=dependencies.chunk_splitter,
        chunk_tagger=dependencies.chunk_tagger,
        embedder=dependencies.embedder,
        chunk_store=dependencies.chunk_store,
    )


def _normalize_summary(summary: BatchRunSummary) -> dict[str, object]:
    failed_files = [
        {
            "source_path": entry.source_path,
            "action": entry.action,
            "step": entry.step,
            "error_type": entry.error_type,
        }
        for entry in summary.failed_files
    ]
    return {
        "status": summary.status,
        "trigger": summary.trigger,
        "new_count": summary.new_count,
        "updated_count": summary.updated_count,
        "deleted_count": summary.deleted_count,
        "deleted_success_count": summary.deleted_success_count,
        "ingest_target_count": summary.ingest_target_count,
        "ingested_success_count": summary.ingested_success_count,
        "failed_file_count": summary.failed_file_count,
        "failed_files": failed_files,
        "stored_chunk_count": summary.stored_chunk_count,
    }


def _empty_summary(
    status: BatchRunStatus,
    *,
    trigger: BatchTrigger,
) -> dict[str, object]:
    return {
        "status": status,
        "trigger": trigger,
        "new_count": 0,
        "updated_count": 0,
        "deleted_count": 0,
        "deleted_success_count": 0,
        "ingest_target_count": 0,
        "ingested_success_count": 0,
        "failed_file_count": 0,
        "failed_files": [],
        "stored_chunk_count": 0,
    }


def _find_log_events(
    log_output: list[MutableMapping[str, object]],
    event_name: str,
) -> list[MutableMapping[str, object]]:
    return [entry for entry in log_output if entry.get("event") == event_name]


def _assert_log_contains(
    log_entry: MutableMapping[str, object],
    expected_fields: dict[str, object],
) -> None:
    assert set(expected_fields) <= set(log_entry)
    assert {field_name: log_entry[field_name] for field_name in expected_fields} == (
        expected_fields
    )


class TestBatchSchedulerRunOnce:
    def test_tc_01_returns_skipped_no_diff_without_calling_a2_to_a5(self) -> None:
        dependencies = _make_dependencies(
            _make_diff_result(new_files=[], updated_files=[], deleted_files=[]),
        )
        config = _make_config(dependencies)

        result = run_once(config, trigger="startup")

        assert _normalize_summary(result) == _empty_summary(
            "skipped_no_diff",
            trigger="startup",
        )
        assert dependencies.diff_detector.calls == [_TARGET_PATH]
        assert dependencies.markdown_loader.calls == []
        assert dependencies.chunk_splitter.calls == []
        assert dependencies.chunk_tagger.calls == []
        assert dependencies.embedder.calls == []
        assert dependencies.chunk_store.delete_calls == []
        assert dependencies.chunk_store.upsert_calls == []

    def test_tc_02_aggregates_delete_new_and_updated_failure_as_completed_with_errors(
        self,
    ) -> None:
        dependencies = _make_dependencies(
            _make_diff_result(
                new_files=["docker/compose.md"],
                updated_files=["typescript/generics.md"],
                deleted_files=["python/contextmanager.md"],
            ),
            split_chunk_counts={
                "docker/compose.md": 2,
                "typescript/generics.md": 1,
            },
            embed_errors={
                "typescript/generics.md": EmbeddingModelCallError("embed failed"),
            },
        )
        config = _make_config(dependencies)

        result = run_once(config, trigger="interval")

        assert _normalize_summary(result) == {
            "status": "completed_with_errors",
            "trigger": "interval",
            "new_count": 1,
            "updated_count": 1,
            "deleted_count": 1,
            "deleted_success_count": 1,
            "ingest_target_count": 2,
            "ingested_success_count": 1,
            "failed_file_count": 1,
            "failed_files": [
                {
                    "source_path": "typescript/generics.md",
                    "action": "ingest_updated",
                    "step": "embed",
                    "error_type": "EmbeddingModelCallError",
                },
            ],
            "stored_chunk_count": 2,
        }
        assert dependencies.chunk_store.delete_calls == [
            "python/contextmanager.md",
        ]
        assert dependencies.chunk_store.upsert_calls == ["docker/compose.md"]
        assert ("delete_by_source_path", "typescript/generics.md") not in (
            dependencies.operations
        )
        assert (
            "upsert_chunks",
            "typescript/generics.md",
        ) not in dependencies.operations

    def test_tc_10_processes_deleted_then_new_then_updated_in_sorted_order(
        self,
    ) -> None:
        dependencies = _make_dependencies(
            _make_diff_result(
                new_files=["notes/z.md", "notes/a.md"],
                updated_files=["topics/d.md", "topics/c.md"],
                deleted_files=["zeta/old.md", "alpha/old.md"],
            ),
        )
        config = _make_config(dependencies)

        result = run_once(config, trigger="interval")

        assert _normalize_summary(result) == {
            "status": "completed",
            "trigger": "interval",
            "new_count": 2,
            "updated_count": 2,
            "deleted_count": 2,
            "deleted_success_count": 2,
            "ingest_target_count": 4,
            "ingested_success_count": 4,
            "failed_file_count": 0,
            "failed_files": [],
            "stored_chunk_count": 4,
        }
        assert dependencies.operations == [
            ("delete_by_source_path", "alpha/old.md"),
            ("delete_by_source_path", "zeta/old.md"),
            ("load", "notes/a.md"),
            ("split", "notes/a.md"),
            ("tag", "notes/a.md"),
            ("embed", "notes/a.md"),
            ("upsert_chunks", "notes/a.md"),
            ("load", "notes/z.md"),
            ("split", "notes/z.md"),
            ("tag", "notes/z.md"),
            ("embed", "notes/z.md"),
            ("upsert_chunks", "notes/z.md"),
            ("load", "topics/c.md"),
            ("split", "topics/c.md"),
            ("tag", "topics/c.md"),
            ("embed", "topics/c.md"),
            ("delete_by_source_path", "topics/c.md"),
            ("upsert_chunks", "topics/c.md"),
            ("load", "topics/d.md"),
            ("split", "topics/d.md"),
            ("tag", "topics/d.md"),
            ("embed", "topics/d.md"),
            ("delete_by_source_path", "topics/d.md"),
            ("upsert_chunks", "topics/d.md"),
        ]

    def test_tc_11_processes_new_files_in_sorted_pipeline_order(self) -> None:
        dependencies = _make_dependencies(
            _make_diff_result(
                new_files=["notes/b.md", "notes/a.md"],
                updated_files=[],
                deleted_files=[],
            ),
        )
        config = _make_config(dependencies)

        run_once(config, trigger="interval")

        assert dependencies.operations == [
            ("load", "notes/a.md"),
            ("split", "notes/a.md"),
            ("tag", "notes/a.md"),
            ("embed", "notes/a.md"),
            ("upsert_chunks", "notes/a.md"),
            ("load", "notes/b.md"),
            ("split", "notes/b.md"),
            ("tag", "notes/b.md"),
            ("embed", "notes/b.md"),
            ("upsert_chunks", "notes/b.md"),
        ]
        assert dependencies.chunk_store.delete_calls == []

    def test_tc_12_processes_updated_file_with_delete_after_embed_before_upsert(
        self,
    ) -> None:
        dependencies = _make_dependencies(
            _make_diff_result(
                new_files=[],
                updated_files=["topics/refactor.md"],
                deleted_files=[],
            ),
            split_chunk_counts={"topics/refactor.md": 2},
        )
        config = _make_config(dependencies)

        result = run_once(config, trigger="interval")

        assert _normalize_summary(result) == {
            "status": "completed",
            "trigger": "interval",
            "new_count": 0,
            "updated_count": 1,
            "deleted_count": 0,
            "deleted_success_count": 0,
            "ingest_target_count": 1,
            "ingested_success_count": 1,
            "failed_file_count": 0,
            "failed_files": [],
            "stored_chunk_count": 2,
        }
        assert dependencies.operations == [
            ("load", "topics/refactor.md"),
            ("split", "topics/refactor.md"),
            ("tag", "topics/refactor.md"),
            ("embed", "topics/refactor.md"),
            ("delete_by_source_path", "topics/refactor.md"),
            ("upsert_chunks", "topics/refactor.md"),
        ]

    def test_tc_13_treats_empty_split_for_new_file_as_success_without_saving(
        self,
    ) -> None:
        dependencies = _make_dependencies(
            _make_diff_result(
                new_files=["notes/empty-new.md"],
                updated_files=[],
                deleted_files=[],
            ),
            loader_contents={"notes/empty-new.md": "---\ntitle: only meta\n---\n"},
            split_empty_sources={"notes/empty-new.md"},
        )
        config = _make_config(dependencies)

        result = run_once(config, trigger="interval")

        assert _normalize_summary(result) == {
            "status": "completed",
            "trigger": "interval",
            "new_count": 1,
            "updated_count": 0,
            "deleted_count": 0,
            "deleted_success_count": 0,
            "ingest_target_count": 1,
            "ingested_success_count": 1,
            "failed_file_count": 0,
            "failed_files": [],
            "stored_chunk_count": 0,
        }
        assert dependencies.operations == [
            ("load", "notes/empty-new.md"),
            ("split", "notes/empty-new.md"),
        ]

    def test_tc_14_treats_empty_split_for_updated_file_as_success_after_delete(
        self,
    ) -> None:
        dependencies = _make_dependencies(
            _make_diff_result(
                new_files=[],
                updated_files=["notes/empty.md"],
                deleted_files=[],
            ),
            loader_contents={"notes/empty.md": "---\ntitle: only meta\n---\n"},
            split_empty_sources={"notes/empty.md"},
        )
        config = _make_config(dependencies)

        result = run_once(config, trigger="interval")

        assert _normalize_summary(result) == {
            "status": "completed",
            "trigger": "interval",
            "new_count": 0,
            "updated_count": 1,
            "deleted_count": 0,
            "deleted_success_count": 0,
            "ingest_target_count": 1,
            "ingested_success_count": 1,
            "failed_file_count": 0,
            "failed_files": [],
            "stored_chunk_count": 0,
        }
        assert dependencies.operations == [
            ("load", "notes/empty.md"),
            ("split", "notes/empty.md"),
            ("delete_by_source_path", "notes/empty.md"),
        ]

    def test_tc_15_collects_single_file_failures_and_continues_other_files(
        self,
    ) -> None:
        dependencies = _make_dependencies(
            _make_diff_result(
                new_files=["new/bad.md", "new/good.md"],
                updated_files=["updated/good.md"],
                deleted_files=["removed/bad.md"],
            ),
            loader_errors={"new/bad.md": FileNotFoundError("missing")},
            split_chunk_counts={"new/good.md": 1, "updated/good.md": 2},
            delete_errors={"removed/bad.md": ChunkStoreWriteError("delete failed")},
        )
        config = _make_config(dependencies)

        result = run_once(config, trigger="interval")
        summary = _normalize_summary(result)

        assert {
            key: value for key, value in summary.items() if key != "failed_files"
        } == {
            "status": "completed_with_errors",
            "trigger": "interval",
            "new_count": 2,
            "updated_count": 1,
            "deleted_count": 1,
            "deleted_success_count": 0,
            "ingest_target_count": 3,
            "ingested_success_count": 2,
            "failed_file_count": 2,
            "stored_chunk_count": 3,
        }
        failed_files = cast("list[dict[str, str]]", summary["failed_files"])
        assert sorted(
            failed_files,
            key=lambda entry: (
                entry["source_path"],
                entry["action"],
                entry["step"],
                entry["error_type"],
            ),
        ) == sorted(
            [
                {
                    "source_path": "removed/bad.md",
                    "action": "delete",
                    "step": "delete_removed_file",
                    "error_type": "ChunkStoreWriteError",
                },
                {
                    "source_path": "new/bad.md",
                    "action": "ingest_new",
                    "step": "load",
                    "error_type": "FileNotFoundError",
                },
            ],
            key=lambda entry: (
                entry["source_path"],
                entry["action"],
                entry["step"],
                entry["error_type"],
            ),
        )
        assert dependencies.operations == [
            ("delete_by_source_path", "removed/bad.md"),
            ("load", "new/bad.md"),
            ("load", "new/good.md"),
            ("split", "new/good.md"),
            ("tag", "new/good.md"),
            ("embed", "new/good.md"),
            ("upsert_chunks", "new/good.md"),
            ("load", "updated/good.md"),
            ("split", "updated/good.md"),
            ("tag", "updated/good.md"),
            ("embed", "updated/good.md"),
            ("delete_by_source_path", "updated/good.md"),
            ("upsert_chunks", "updated/good.md"),
        ]

    def test_tc_20_raises_config_error_for_empty_target_path(self) -> None:
        dependencies = _make_dependencies(
            _make_diff_result(new_files=[], updated_files=[], deleted_files=[]),
        )
        config = _make_config(dependencies, target_path="")

        with pytest.raises(BatchSchedulerConfigError):
            run_once(config, trigger="startup")

        assert dependencies.diff_detector.calls == []
        assert dependencies.markdown_loader.calls == []
        assert dependencies.chunk_splitter.calls == []
        assert dependencies.chunk_tagger.calls == []
        assert dependencies.embedder.calls == []
        assert dependencies.chunk_store.delete_calls == []
        assert dependencies.chunk_store.upsert_calls == []

    def test_tc_23_records_load_failure_for_updated_file_and_continues(self) -> None:
        dependencies = _make_dependencies(
            _make_diff_result(
                new_files=["new/good.md"],
                updated_files=["notes/moved.md"],
                deleted_files=[],
            ),
            loader_errors={"notes/moved.md": FileNotFoundError("missing")},
        )
        config = _make_config(dependencies)

        result = run_once(config, trigger="interval")

        assert _normalize_summary(result) == {
            "status": "completed_with_errors",
            "trigger": "interval",
            "new_count": 1,
            "updated_count": 1,
            "deleted_count": 0,
            "deleted_success_count": 0,
            "ingest_target_count": 2,
            "ingested_success_count": 1,
            "failed_file_count": 1,
            "failed_files": [
                {
                    "source_path": "notes/moved.md",
                    "action": "ingest_updated",
                    "step": "load",
                    "error_type": "FileNotFoundError",
                },
            ],
            "stored_chunk_count": 1,
        }
        assert dependencies.operations == [
            ("load", "new/good.md"),
            ("split", "new/good.md"),
            ("tag", "new/good.md"),
            ("embed", "new/good.md"),
            ("upsert_chunks", "new/good.md"),
            ("load", "notes/moved.md"),
        ]

    def test_tc_24_records_delete_old_chunks_failure_and_skips_upsert(self) -> None:
        dependencies = _make_dependencies(
            _make_diff_result(
                new_files=[],
                updated_files=["topics/topic.md"],
                deleted_files=[],
            ),
            delete_errors={"topics/topic.md": ChunkStoreWriteError("delete failed")},
        )
        config = _make_config(dependencies)

        result = run_once(config, trigger="interval")

        assert _normalize_summary(result) == {
            "status": "completed_with_errors",
            "trigger": "interval",
            "new_count": 0,
            "updated_count": 1,
            "deleted_count": 0,
            "deleted_success_count": 0,
            "ingest_target_count": 1,
            "ingested_success_count": 0,
            "failed_file_count": 1,
            "failed_files": [
                {
                    "source_path": "topics/topic.md",
                    "action": "ingest_updated",
                    "step": "delete_old_chunks",
                    "error_type": "ChunkStoreWriteError",
                },
            ],
            "stored_chunk_count": 0,
        }
        assert dependencies.operations == [
            ("load", "topics/topic.md"),
            ("split", "topics/topic.md"),
            ("tag", "topics/topic.md"),
            ("embed", "topics/topic.md"),
            ("delete_by_source_path", "topics/topic.md"),
        ]

    def test_tc_25_records_upsert_failure_after_successful_old_chunk_delete(
        self,
    ) -> None:
        dependencies = _make_dependencies(
            _make_diff_result(
                new_files=[],
                updated_files=["topics/topic.md"],
                deleted_files=[],
            ),
            upsert_errors={"topics/topic.md": ChunkStoreWriteError("upsert failed")},
        )
        config = _make_config(dependencies)

        result = run_once(config, trigger="interval")

        assert _normalize_summary(result) == {
            "status": "completed_with_errors",
            "trigger": "interval",
            "new_count": 0,
            "updated_count": 1,
            "deleted_count": 0,
            "deleted_success_count": 0,
            "ingest_target_count": 1,
            "ingested_success_count": 0,
            "failed_file_count": 1,
            "failed_files": [
                {
                    "source_path": "topics/topic.md",
                    "action": "ingest_updated",
                    "step": "upsert",
                    "error_type": "ChunkStoreWriteError",
                },
            ],
            "stored_chunk_count": 0,
        }
        assert dependencies.operations == [
            ("load", "topics/topic.md"),
            ("split", "topics/topic.md"),
            ("tag", "topics/topic.md"),
            ("embed", "topics/topic.md"),
            ("delete_by_source_path", "topics/topic.md"),
            ("upsert_chunks", "topics/topic.md"),
        ]

    def test_tc_30_returns_failed_summary_when_diff_detector_fails(self) -> None:
        operations: list[tuple[str, str]] = []
        dependencies = _Dependencies(
            diff_detector=_RecordingDiffDetector(error=RuntimeError("scan failed")),
            markdown_loader=_RecordingMarkdownLoader(operations),
            chunk_splitter=_RecordingChunkSplitter(operations),
            chunk_tagger=_RecordingChunkTagger(operations),
            embedder=_RecordingEmbedder(operations),
            chunk_store=_RecordingChunkStore(operations),
            operations=operations,
        )
        config = _make_config(dependencies)

        result = run_once(config, trigger="interval")

        assert _normalize_summary(result) == _empty_summary(
            "failed",
            trigger="interval",
        )
        assert dependencies.diff_detector.calls == [_TARGET_PATH]
        assert dependencies.markdown_loader.calls == []
        assert dependencies.chunk_splitter.calls == []
        assert dependencies.chunk_tagger.calls == []
        assert dependencies.embedder.calls == []
        assert dependencies.chunk_store.delete_calls == []
        assert dependencies.chunk_store.upsert_calls == []

    def test_tc_30b_returns_failed_summary_when_orchestration_raises_unexpectedly(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        dependencies = _make_dependencies(
            _make_diff_result(new_files=["a.md"], updated_files=[], deleted_files=[]),
        )
        config = _make_config(dependencies)

        original_sorted = sorted

        def _exploding_sorted(*args: object, **kwargs: object) -> list[object]:
            for arg in args:
                if isinstance(arg, list) and arg and isinstance(arg[0], str):
                    msg = "unexpected orchestration error"
                    raise RuntimeError(msg)
            return original_sorted(*args, **kwargs)

        monkeypatch.setattr("builtins.sorted", _exploding_sorted)

        result = run_once(config, trigger="interval")

        assert _normalize_summary(result) == _empty_summary(
            "failed",
            trigger="interval",
        )

    def test_tc_15b_split_failure_records_step_split_and_continues(self) -> None:
        dependencies = _make_dependencies(
            _make_diff_result(
                new_files=["new/bad-split.md", "new/good.md"],
                updated_files=[],
                deleted_files=[],
            ),
            split_errors={"new/bad-split.md": RuntimeError("split crashed")},
        )
        config = _make_config(dependencies)

        result = run_once(config, trigger="interval")
        summary = _normalize_summary(result)

        assert {
            key: value for key, value in summary.items() if key != "failed_files"
        } == {
            "status": "completed_with_errors",
            "trigger": "interval",
            "new_count": 2,
            "updated_count": 0,
            "deleted_count": 0,
            "deleted_success_count": 0,
            "ingest_target_count": 2,
            "ingested_success_count": 1,
            "failed_file_count": 1,
            "stored_chunk_count": 1,
        }
        failed_files = cast("list[dict[str, str]]", summary["failed_files"])
        assert failed_files == [
            {
                "source_path": "new/bad-split.md",
                "action": "ingest_new",
                "step": "split",
                "error_type": "RuntimeError",
            },
        ]
        assert dependencies.operations == [
            ("load", "new/bad-split.md"),
            ("split", "new/bad-split.md"),
            ("load", "new/good.md"),
            ("split", "new/good.md"),
            ("tag", "new/good.md"),
            ("embed", "new/good.md"),
            ("upsert_chunks", "new/good.md"),
        ]

    def test_tc_15c_tag_failure_records_step_tag_and_continues(self) -> None:
        dependencies = _make_dependencies(
            _make_diff_result(
                new_files=["new/bad-tag.md", "new/good.md"],
                updated_files=[],
                deleted_files=[],
            ),
            tag_errors={"new/bad-tag.md": RuntimeError("tag crashed")},
        )
        config = _make_config(dependencies)

        result = run_once(config, trigger="interval")
        summary = _normalize_summary(result)

        assert {
            key: value for key, value in summary.items() if key != "failed_files"
        } == {
            "status": "completed_with_errors",
            "trigger": "interval",
            "new_count": 2,
            "updated_count": 0,
            "deleted_count": 0,
            "deleted_success_count": 0,
            "ingest_target_count": 2,
            "ingested_success_count": 1,
            "failed_file_count": 1,
            "stored_chunk_count": 1,
        }
        failed_files = cast("list[dict[str, str]]", summary["failed_files"])
        assert failed_files == [
            {
                "source_path": "new/bad-tag.md",
                "action": "ingest_new",
                "step": "tag",
                "error_type": "RuntimeError",
            },
        ]
        assert dependencies.operations == [
            ("load", "new/bad-tag.md"),
            ("split", "new/bad-tag.md"),
            ("tag", "new/bad-tag.md"),
            ("load", "new/good.md"),
            ("split", "new/good.md"),
            ("tag", "new/good.md"),
            ("embed", "new/good.md"),
            ("upsert_chunks", "new/good.md"),
        ]


class TestBatchSchedulerLogging:
    def test_tc_32_logs_started_file_success_file_failure_and_completed_events(
        self,
    ) -> None:
        dependencies = _make_dependencies(
            _make_diff_result(
                new_files=["docker/compose.md"],
                updated_files=["react/hooks.md", "typescript/generics.md"],
                deleted_files=["python/contextmanager.md"],
            ),
            split_chunk_counts={
                "docker/compose.md": 2,
                "react/hooks.md": 3,
                "typescript/generics.md": 1,
            },
            embed_errors={
                "typescript/generics.md": EmbeddingModelCallError("embed failed"),
            },
        )
        config = _make_config(dependencies)

        with capture_logs() as log_output:
            run_once(config, trigger="interval")

        started_logs = _find_log_events(log_output, "ingestion_batch_started")
        file_completed_logs = _find_log_events(
            log_output,
            "ingestion_batch_file_completed",
        )
        file_failed_logs = _find_log_events(log_output, "ingestion_batch_file_failed")
        completed_logs = _find_log_events(log_output, "ingestion_batch_completed")

        assert len(started_logs) == 1
        _assert_log_contains(
            started_logs[0],
            {
                "trigger": "interval",
                "target_path": _TARGET_PATH,
            },
        )
        assert len(file_completed_logs) == 3
        assert {
            (
                entry["source_path"],
                entry["action"],
                entry["stored_chunk_count"],
            )
            for entry in file_completed_logs
        } == {
            ("python/contextmanager.md", "delete", 0),
            ("docker/compose.md", "ingest_new", 2),
            ("react/hooks.md", "ingest_updated", 3),
        }
        assert len(file_failed_logs) == 1
        _assert_log_contains(
            file_failed_logs[0],
            {
                "source_path": "typescript/generics.md",
                "action": "ingest_updated",
                "step": "embed",
                "error_type": "EmbeddingModelCallError",
            },
        )
        assert len(completed_logs) == 1
        _assert_log_contains(
            completed_logs[0],
            {
                "status": "completed_with_errors",
                "trigger": "interval",
                "new_count": 1,
                "updated_count": 2,
                "deleted_count": 1,
                "deleted_success_count": 1,
                "ingested_success_count": 2,
                "failed_file_count": 1,
                "stored_chunk_count": 5,
            },
        )

    def test_tc_33_logs_skipped_no_diff_event_with_required_fields(self) -> None:
        dependencies = _make_dependencies(
            _make_diff_result(new_files=[], updated_files=[], deleted_files=[]),
        )
        config = _make_config(dependencies)

        with capture_logs() as log_output:
            run_once(config, trigger="startup")

        skipped_logs = _find_log_events(log_output, "ingestion_batch_skipped_no_diff")
        completed_logs = _find_log_events(log_output, "ingestion_batch_completed")
        assert len(skipped_logs) == 1
        assert len(completed_logs) == 1
        _assert_log_contains(
            skipped_logs[0],
            {
                "trigger": "startup",
                "target_path": _TARGET_PATH,
                "new_count": 0,
                "updated_count": 0,
                "deleted_count": 0,
            },
        )
        _assert_log_contains(
            completed_logs[0],
            {
                "status": "skipped_no_diff",
                "trigger": "startup",
                "new_count": 0,
                "updated_count": 0,
                "deleted_count": 0,
                "deleted_success_count": 0,
                "ingested_success_count": 0,
                "failed_file_count": 0,
                "stored_chunk_count": 0,
            },
        )
