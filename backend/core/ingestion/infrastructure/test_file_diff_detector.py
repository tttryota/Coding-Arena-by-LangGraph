from __future__ import annotations

import os
from pathlib import Path
from typing import TYPE_CHECKING, Protocol, TypedDict, cast

if TYPE_CHECKING:
    from collections.abc import MutableMapping

import pytest

from core.ingestion.infrastructure.file_diff_detector import (
    FileDiffResult,
    InvalidTargetPathError,
    ScanStatePersistenceError,
    TargetPathAccessError,
    TargetPathNotFoundError,
    detect,
)

if TYPE_CHECKING:
    from types import TracebackType


class _RecordingSnapshotStore:
    def __init__(
        self,
        snapshots: dict[str, dict[str, int]] | None = None,
        *,
        load_error: RuntimeError | None = None,
        replace_error: RuntimeError | None = None,
    ) -> None:
        self._snapshots = {
            snapshot_key: dict(files)
            for snapshot_key, files in (snapshots or {}).items()
        }
        self._load_error = load_error
        self._replace_error = replace_error
        self.load_calls: list[str] = []
        self.replace_calls: list[tuple[str, dict[str, int]]] = []

    def load(self, snapshot_key: str) -> dict[str, int] | None:
        self.load_calls.append(snapshot_key)
        if self._load_error is not None:
            raise self._load_error
        stored = self._snapshots.get(snapshot_key)
        if stored is None:
            return None
        return dict(stored)

    def replace(self, snapshot_key: str, files: dict[str, int]) -> None:
        self.replace_calls.append((snapshot_key, dict(files)))
        if self._replace_error is not None:
            raise self._replace_error
        self._snapshots[snapshot_key] = dict(files)

    def snapshot_for_last_replace(self) -> dict[str, int]:
        assert self.replace_calls
        return dict(self.replace_calls[-1][1])


def _snapshot_key(target_path: Path) -> str:
    return str(target_path.resolve())


def _write_markdown_file(
    target_path: Path,
    relative_path: str,
    *,
    content: str = "# note\n",
    mtime_ns: int,
) -> None:
    file_path = target_path / Path(relative_path)
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_text(content, encoding="utf-8")
    os.utime(file_path, ns=(mtime_ns, mtime_ns))


def _write_plain_file(
    target_path: Path,
    relative_path: str,
    *,
    content: str = "plain\n",
) -> None:
    file_path = target_path / Path(relative_path)
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_text(content, encoding="utf-8")


class _NormalizedResult(TypedDict):
    target_path: str
    new_files: list[str]
    updated_files: list[str]
    deleted_files: list[str]
    new_count: int
    updated_count: int
    deleted_count: int


class _ScandirIterator(Protocol):
    def __iter__(self) -> _ScandirIterator: ...
    def __next__(self) -> os.DirEntry[str]: ...
    def __enter__(self) -> _ScandirIterator: ...
    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> bool | None: ...
    def close(self) -> None: ...


def _normalize_result(result: FileDiffResult) -> _NormalizedResult:
    assert type(result.target_path) is str
    assert type(result.new_files) is list
    assert type(result.updated_files) is list
    assert type(result.deleted_files) is list
    assert all(type(path) is str for path in result.new_files)
    assert all(type(path) is str for path in result.updated_files)
    assert all(type(path) is str for path in result.deleted_files)
    assert type(result.new_count) is int
    assert type(result.updated_count) is int
    assert type(result.deleted_count) is int

    normalized: _NormalizedResult = {
        "target_path": result.target_path,
        "new_files": result.new_files,
        "updated_files": result.updated_files,
        "deleted_files": result.deleted_files,
        "new_count": result.new_count,
        "updated_count": result.updated_count,
        "deleted_count": result.deleted_count,
    }
    return normalized


def _assert_paths_are_posix_normalized(paths: list[str]) -> None:
    for path in paths:
        assert "\\" not in path
        assert path == Path(path).as_posix()
        assert not path.startswith("/")


def _patch_scandir_failure(
    monkeypatch: pytest.MonkeyPatch,
    *,
    failing_path: Path,
) -> None:
    original_scandir = os.scandir

    def patched_scandir(path: str | os.PathLike[str]) -> _ScandirIterator:
        if Path(path) == failing_path:
            msg = "permission denied"
            raise PermissionError(msg)
        return cast("_ScandirIterator", original_scandir(path))

    monkeypatch.setattr(os, "scandir", patched_scandir)


class _PatchedDirEntry:
    def __init__(self, entry: os.DirEntry[str], *, failing_path: Path) -> None:
        self._entry = entry
        self._failing_path = failing_path

    def __getattr__(self, name: str) -> object:
        return getattr(self._entry, name)

    def stat(self, *, follow_symlinks: bool = True) -> os.stat_result:
        if Path(self._entry.path) == self._failing_path:
            msg = "permission denied"
            raise PermissionError(msg)
        return self._entry.stat(follow_symlinks=follow_symlinks)


class _PatchedScandirIterator:
    def __init__(
        self,
        iterator: _ScandirIterator,
        *,
        failing_path: Path,
    ) -> None:
        self._iterator = iterator
        self._failing_path = failing_path

    def __iter__(self) -> _PatchedScandirIterator:
        return self

    def __next__(self) -> _PatchedDirEntry:
        return _PatchedDirEntry(next(self._iterator), failing_path=self._failing_path)

    def __enter__(self) -> _PatchedScandirIterator:
        self._iterator.__enter__()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> bool | None:
        return self._iterator.__exit__(exc_type, exc_value, traceback)

    def close(self) -> None:
        self._iterator.close()


def _patch_mtime_lookup_failure(
    monkeypatch: pytest.MonkeyPatch,
    *,
    failing_path: Path,
) -> None:
    original_scandir = os.scandir

    def patched_scandir(path: str | os.PathLike[str]) -> _PatchedScandirIterator:
        iterator = original_scandir(path)
        return _PatchedScandirIterator(
            cast("_ScandirIterator", iterator),
            failing_path=failing_path,
        )

    monkeypatch.setattr(os, "scandir", patched_scandir)


def _find_log_events(
    log_output: list[MutableMapping[str, object]],
    event_name: str,
) -> list[MutableMapping[str, object]]:
    return [entry for entry in log_output if entry.get("event") == event_name]


class TestFileDiffDetectorInitialScans:
    def test_tc_01_returns_all_markdown_files_as_new_and_persists_initial_snapshot(
        self,
        tmp_path: Path,
    ) -> None:
        target_path = tmp_path / "study"
        target_path.mkdir()
        _write_markdown_file(
            target_path,
            "typescript/generics.md",
            mtime_ns=1716112800000000000,
        )
        _write_markdown_file(
            target_path,
            "docker/dockerfile.md",
            mtime_ns=1716116400000000000,
        )
        _write_plain_file(target_path, "notes.txt")
        snapshot_store = _RecordingSnapshotStore()

        actual = _normalize_result(detect(target_path, snapshot_store))

        assert actual == {
            "target_path": str(target_path.resolve()),
            "new_files": ["docker/dockerfile.md", "typescript/generics.md"],
            "updated_files": [],
            "deleted_files": [],
            "new_count": 2,
            "updated_count": 0,
            "deleted_count": 0,
        }
        assert snapshot_store.replace_calls == [
            (
                _snapshot_key(target_path),
                {
                    "docker/dockerfile.md": 1716116400000000000,
                    "typescript/generics.md": 1716112800000000000,
                },
            ),
        ]

    def test_tc_02_returns_empty_diff_when_snapshot_matches_current_scan(
        self,
        tmp_path: Path,
    ) -> None:
        target_path = tmp_path / "study"
        target_path.mkdir()
        snapshot_store = _RecordingSnapshotStore(
            snapshots={
                _snapshot_key(target_path): {
                    "docker/dockerfile.md": 1716116400000000000,
                    "typescript/generics.md": 1716112800000000000,
                },
            },
        )
        _write_markdown_file(
            target_path,
            "typescript/generics.md",
            mtime_ns=1716112800000000000,
        )
        _write_markdown_file(
            target_path,
            "docker/dockerfile.md",
            mtime_ns=1716116400000000000,
        )

        actual = _normalize_result(detect(target_path, snapshot_store))

        assert actual == {
            "target_path": str(target_path.resolve()),
            "new_files": [],
            "updated_files": [],
            "deleted_files": [],
            "new_count": 0,
            "updated_count": 0,
            "deleted_count": 0,
        }
        assert snapshot_store.replace_calls == [
            (
                _snapshot_key(target_path),
                {
                    "docker/dockerfile.md": 1716116400000000000,
                    "typescript/generics.md": 1716112800000000000,
                },
            ),
        ]

    def test_normalizes_relative_target_path_to_absolute_path(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        target_path = tmp_path / "vault" / "study"
        target_path.mkdir(parents=True)
        _write_markdown_file(
            target_path,
            "notes/intro.md",
            mtime_ns=1716120000000000000,
        )
        snapshot_store = _RecordingSnapshotStore()
        monkeypatch.chdir(tmp_path)

        actual = _normalize_result(detect("vault/study", snapshot_store))

        resolved_key = str(target_path.resolve())
        assert actual["target_path"] == resolved_key
        assert actual["new_files"] == ["notes/intro.md"]
        assert snapshot_store.load_calls == [resolved_key]
        assert snapshot_store.replace_calls == [
            (resolved_key, {"notes/intro.md": 1716120000000000000}),
        ]

    def test_ignores_non_markdown_extensions_and_directories(
        self,
        tmp_path: Path,
    ) -> None:
        target_path = tmp_path / "study"
        target_path.mkdir()
        _write_markdown_file(
            target_path,
            "python/contextmanager.md",
            mtime_ns=1716111000000000000,
        )
        _write_plain_file(target_path, "notes.txt")
        _write_plain_file(target_path, "README.MD")
        _write_plain_file(target_path, "draft.markdown")
        (target_path / "just_a_directory.md").mkdir()
        snapshot_store = _RecordingSnapshotStore()

        actual = _normalize_result(detect(target_path, snapshot_store))

        assert actual["new_files"] == ["python/contextmanager.md"]
        assert actual["new_count"] == 1

    def test_recursively_detects_markdown_files_in_nested_subdirectories(
        self,
        tmp_path: Path,
    ) -> None:
        target_path = tmp_path / "study"
        target_path.mkdir()
        _write_markdown_file(
            target_path,
            "a/b/c/deep-note.md",
            mtime_ns=1716112000000000000,
        )
        snapshot_store = _RecordingSnapshotStore()

        actual = _normalize_result(detect(target_path, snapshot_store))

        assert actual["new_files"] == ["a/b/c/deep-note.md"]
        _assert_paths_are_posix_normalized(actual["new_files"])

    def test_tc_12_ignores_markdown_named_symlink_files(
        self,
        tmp_path: Path,
    ) -> None:
        target_path = tmp_path / "study"
        target_path.mkdir()
        _write_markdown_file(target_path, "topic.md", mtime_ns=1716113000000000000)
        (target_path / "alias.md").symlink_to(target_path / "topic.md")
        snapshot_store = _RecordingSnapshotStore()

        actual = _normalize_result(detect(target_path, snapshot_store))

        assert actual == {
            "target_path": str(target_path.resolve()),
            "new_files": ["topic.md"],
            "updated_files": [],
            "deleted_files": [],
            "new_count": 1,
            "updated_count": 0,
            "deleted_count": 0,
        }

    def test_tc_13_skips_symlink_directories_during_recursive_scan(
        self,
        tmp_path: Path,
    ) -> None:
        target_path = tmp_path / "study"
        target_path.mkdir()
        _write_markdown_file(target_path, "real/keep.md", mtime_ns=10)
        linked_directory = tmp_path / "linked-target"
        linked_directory.mkdir()
        _write_markdown_file(
            linked_directory,
            "skip.md",
            mtime_ns=11,
        )
        (target_path / "linked").symlink_to(linked_directory, target_is_directory=True)
        snapshot_store = _RecordingSnapshotStore()

        actual = _normalize_result(detect(target_path, snapshot_store))

        assert actual == {
            "target_path": str(target_path.resolve()),
            "new_files": ["real/keep.md"],
            "updated_files": [],
            "deleted_files": [],
            "new_count": 1,
            "updated_count": 0,
            "deleted_count": 0,
        }

    def test_returns_relative_posix_paths_in_all_result_lists(
        self,
        tmp_path: Path,
    ) -> None:
        target_path = tmp_path / "study"
        target_path.mkdir()
        snapshot_store = _RecordingSnapshotStore(
            snapshots={
                _snapshot_key(target_path): {
                    "python/contextmanager.md": 1716111000000000000,
                    "legacy/note.md": 1716111001000000000,
                },
            },
        )
        _write_markdown_file(
            target_path,
            "python/contextmanager.md",
            mtime_ns=1716111002000000000,
        )
        _write_markdown_file(
            target_path,
            "rust/ownership.md",
            mtime_ns=1716111003000000000,
        )

        actual = _normalize_result(detect(target_path, snapshot_store))

        assert len(actual["new_files"]) == 1
        assert len(actual["updated_files"]) == 1
        assert len(actual["deleted_files"]) == 1
        _assert_paths_are_posix_normalized(actual["new_files"])
        _assert_paths_are_posix_normalized(actual["updated_files"])
        _assert_paths_are_posix_normalized(actual["deleted_files"])

    def test_tc_14_does_not_report_updated_when_content_changes_but_mtime_matches(
        self,
        tmp_path: Path,
    ) -> None:
        target_path = tmp_path / "study"
        target_path.mkdir()
        mtime_ns = 1716115000000000000
        _write_markdown_file(
            target_path,
            "python/basics.md",
            content="before\n",
            mtime_ns=mtime_ns,
        )
        (target_path / "python" / "basics.md").write_text("after\n", encoding="utf-8")
        os.utime(target_path / "python" / "basics.md", ns=(mtime_ns, mtime_ns))
        snapshot_store = _RecordingSnapshotStore(
            snapshots={
                _snapshot_key(target_path): {
                    "python/basics.md": mtime_ns,
                },
            },
        )

        actual = _normalize_result(detect(target_path, snapshot_store))

        assert actual == {
            "target_path": str(target_path.resolve()),
            "new_files": [],
            "updated_files": [],
            "deleted_files": [],
            "new_count": 0,
            "updated_count": 0,
            "deleted_count": 0,
        }


class TestFileDiffDetectorDiffClassification:
    def test_tc_10_classifies_new_updated_and_deleted_files_together(
        self,
        tmp_path: Path,
    ) -> None:
        target_path = tmp_path / "study"
        target_path.mkdir()
        snapshot_store = _RecordingSnapshotStore(
            snapshots={
                _snapshot_key(target_path): {
                    "docker/dockerfile.md": 1716116400000000000,
                    "typescript/generics.md": 1716112800000000000,
                    "python/contextmanager.md": 1716111000000000000,
                },
            },
        )
        _write_markdown_file(
            target_path,
            "docker/dockerfile.md",
            mtime_ns=1716116400000000000,
        )
        _write_markdown_file(
            target_path,
            "typescript/generics.md",
            mtime_ns=1716120000000000000,
        )
        _write_markdown_file(
            target_path,
            "rust/ownership.md",
            mtime_ns=1716123600000000000,
        )

        actual = _normalize_result(detect(target_path, snapshot_store))
        expected_snapshot = {
            "docker/dockerfile.md": 1716116400000000000,
            "rust/ownership.md": 1716123600000000000,
            "typescript/generics.md": 1716120000000000000,
        }

        assert actual == {
            "target_path": str(target_path.resolve()),
            "new_files": ["rust/ownership.md"],
            "updated_files": ["typescript/generics.md"],
            "deleted_files": ["python/contextmanager.md"],
            "new_count": 1,
            "updated_count": 1,
            "deleted_count": 1,
        }
        assert snapshot_store.replace_calls == [
            (_snapshot_key(target_path), expected_snapshot),
        ]

    def test_tc_11_recursively_scans_subdirectories_and_only_includes_exact_md_files(
        self,
        tmp_path: Path,
    ) -> None:
        target_path = tmp_path / "study"
        target_path.mkdir()
        _write_markdown_file(
            target_path,
            "backend/api/design.md",
            mtime_ns=1,
        )
        _write_plain_file(target_path, "backend/api/README.MD")
        _write_plain_file(target_path, "backend/api/schema.markdown")
        _write_plain_file(target_path, "backend/todo.txt")
        snapshot_store = _RecordingSnapshotStore()

        actual = _normalize_result(detect(target_path, snapshot_store))

        assert actual == {
            "target_path": str(target_path.resolve()),
            "new_files": ["backend/api/design.md"],
            "updated_files": [],
            "deleted_files": [],
            "new_count": 1,
            "updated_count": 0,
            "deleted_count": 0,
        }

    def test_treats_renamed_file_as_deleted_and_new(
        self,
        tmp_path: Path,
    ) -> None:
        target_path = tmp_path / "study"
        target_path.mkdir()
        snapshot_store = _RecordingSnapshotStore(
            snapshots={
                _snapshot_key(target_path): {
                    "old-name.md": 1716118000000000000,
                },
            },
        )
        _write_markdown_file(
            target_path,
            "new-name.md",
            mtime_ns=1716118000000000000,
        )

        actual = _normalize_result(detect(target_path, snapshot_store))

        assert actual["new_files"] == ["new-name.md"]
        assert actual["updated_files"] == []
        assert actual["deleted_files"] == ["old-name.md"]

    def test_keeps_snapshots_isolated_per_target_path(
        self,
        tmp_path: Path,
    ) -> None:
        left_target_path = tmp_path / "left"
        right_target_path = tmp_path / "right"
        left_target_path.mkdir()
        right_target_path.mkdir()
        _write_markdown_file(
            left_target_path,
            "note.md",
            mtime_ns=1716119000000000000,
        )
        _write_markdown_file(
            right_target_path,
            "note.md",
            mtime_ns=1716119001000000000,
        )
        snapshot_store = _RecordingSnapshotStore(
            snapshots={
                _snapshot_key(left_target_path): {"note.md": 1716119000000000000},
                _snapshot_key(right_target_path): {"note.md": 1716118000000000000},
            },
        )

        left_actual = _normalize_result(detect(left_target_path, snapshot_store))
        right_actual = _normalize_result(detect(right_target_path, snapshot_store))

        assert left_actual["updated_files"] == []
        assert right_actual["updated_files"] == ["note.md"]

    def test_tc_20_returns_empty_diff_and_saves_empty_snapshot_on_initial_empty_scan(
        self,
        tmp_path: Path,
    ) -> None:
        target_path = tmp_path / "empty"
        target_path.mkdir()
        _write_plain_file(target_path, "assets/image.png")
        snapshot_store = _RecordingSnapshotStore()

        actual = _normalize_result(detect(target_path, snapshot_store))

        assert actual == {
            "target_path": str(target_path.resolve()),
            "new_files": [],
            "updated_files": [],
            "deleted_files": [],
            "new_count": 0,
            "updated_count": 0,
            "deleted_count": 0,
        }
        assert snapshot_store.replace_calls == [
            (_snapshot_key(target_path), {}),
        ]

    def test_tc_21_returns_all_previous_files_as_deleted_when_current_scan_has_no_targets(
        self,
        tmp_path: Path,
    ) -> None:
        target_path = tmp_path / "study"
        target_path.mkdir()
        _write_plain_file(target_path, "assets/logo.png")
        snapshot_store = _RecordingSnapshotStore(
            snapshots={
                _snapshot_key(target_path): {
                    "algorithms/bfs.md": 100,
                    "db/index.md": 200,
                },
            },
        )

        actual = _normalize_result(detect(target_path, snapshot_store))

        assert actual == {
            "target_path": str(target_path.resolve()),
            "new_files": [],
            "updated_files": [],
            "deleted_files": ["algorithms/bfs.md", "db/index.md"],
            "new_count": 0,
            "updated_count": 0,
            "deleted_count": 2,
        }
        assert snapshot_store.replace_calls == [(_snapshot_key(target_path), {})]

    def test_returns_empty_diff_when_previous_snapshot_is_empty_and_scan_has_no_targets(
        self,
        tmp_path: Path,
    ) -> None:
        target_path = tmp_path / "empty"
        target_path.mkdir()
        snapshot_store = _RecordingSnapshotStore(
            snapshots={_snapshot_key(target_path): {}},
        )

        actual = _normalize_result(detect(target_path, snapshot_store))

        assert actual == {
            "target_path": str(target_path.resolve()),
            "new_files": [],
            "updated_files": [],
            "deleted_files": [],
            "new_count": 0,
            "updated_count": 0,
            "deleted_count": 0,
        }

    def test_treats_same_path_replaced_by_symlink_as_deleted(
        self,
        tmp_path: Path,
    ) -> None:
        target_path = tmp_path / "study"
        target_path.mkdir()
        real_file = tmp_path / "shared.md"
        real_file.write_text("# shared\n", encoding="utf-8")
        (target_path / "note.md").symlink_to(real_file)
        snapshot_store = _RecordingSnapshotStore(
            snapshots={_snapshot_key(target_path): {"note.md": 1716119600000000000}},
        )

        actual = _normalize_result(detect(target_path, snapshot_store))

        assert actual["new_files"] == []
        assert actual["updated_files"] == []
        assert actual["deleted_files"] == ["note.md"]

    def test_detects_nanosecond_mtime_change_as_updated(
        self,
        tmp_path: Path,
    ) -> None:
        target_path = tmp_path / "study"
        target_path.mkdir()
        _write_markdown_file(
            target_path,
            "python/basics.md",
            mtime_ns=1716119700000000001,
        )
        snapshot_store = _RecordingSnapshotStore(
            snapshots={
                _snapshot_key(target_path): {
                    "python/basics.md": 1716119700000000000,
                },
            },
        )

        actual = _normalize_result(detect(target_path, snapshot_store))

        assert actual["updated_files"] == ["python/basics.md"]
        assert actual["updated_count"] == 1

    def test_tc_15_returns_deterministic_results_for_same_snapshot_and_directory_state(
        self,
        tmp_path: Path,
    ) -> None:
        target_path = tmp_path / "study"
        target_path.mkdir()
        _write_markdown_file(target_path, "a.md", mtime_ns=1716120000000000000)
        _write_markdown_file(target_path, "c.md", mtime_ns=1716120001000000000)
        initial_snapshot = {
            _snapshot_key(target_path): {
                "a.md": 1716119999000000000,
                "b.md": 1716119998000000000,
            },
        }

        first_snapshot_store = _RecordingSnapshotStore(snapshots=initial_snapshot)
        second_snapshot_store = _RecordingSnapshotStore(snapshots=initial_snapshot)

        first = _normalize_result(detect(target_path, first_snapshot_store))
        second = _normalize_result(detect(target_path, second_snapshot_store))
        expected = {
            "target_path": str(target_path.resolve()),
            "new_files": ["c.md"],
            "updated_files": ["a.md"],
            "deleted_files": ["b.md"],
            "new_count": 1,
            "updated_count": 1,
            "deleted_count": 1,
        }

        assert first == expected
        assert second == expected
        assert len(set(first["new_files"])) == len(first["new_files"])
        assert len(set(first["updated_files"])) == len(first["updated_files"])
        assert len(set(first["deleted_files"])) == len(first["deleted_files"])


class TestFileDiffDetectorPathValidationAndPersistenceErrors:
    def test_accepts_path_input_and_normalizes_target_path(
        self,
        tmp_path: Path,
    ) -> None:
        target_path = tmp_path / "study"
        target_path.mkdir()
        snapshot_store = _RecordingSnapshotStore()

        actual = _normalize_result(detect(Path(target_path), snapshot_store))

        assert actual["target_path"] == str(target_path.resolve())

    def test_accepts_absolute_string_input_without_changing_result_target_path(
        self,
        tmp_path: Path,
    ) -> None:
        target_path = tmp_path / "study"
        target_path.mkdir()
        snapshot_store = _RecordingSnapshotStore()

        actual = _normalize_result(detect(str(target_path.resolve()), snapshot_store))

        assert actual["target_path"] == str(target_path.resolve())

    def test_tc_30_raises_not_found_error_for_missing_target_path(
        self,
        tmp_path: Path,
    ) -> None:
        snapshot_store = _RecordingSnapshotStore()

        with pytest.raises(TargetPathNotFoundError):
            detect(tmp_path / "missing", snapshot_store)

        assert snapshot_store.replace_calls == []

    def test_tc_31_raises_invalid_target_path_error_for_non_directory_target_path(
        self,
        tmp_path: Path,
    ) -> None:
        target_path = tmp_path / "note.md"
        target_path.write_text("# note\n", encoding="utf-8")
        snapshot_store = _RecordingSnapshotStore()

        with pytest.raises(InvalidTargetPathError):
            detect(target_path, snapshot_store)

        assert snapshot_store.replace_calls == []

    def test_tc_32_raises_invalid_target_path_error_for_symlink_target_path(
        self,
        tmp_path: Path,
    ) -> None:
        actual_target = tmp_path / "actual"
        actual_target.mkdir()
        symlink_target = tmp_path / "linked"
        symlink_target.symlink_to(actual_target, target_is_directory=True)
        snapshot_store = _RecordingSnapshotStore()

        with pytest.raises(InvalidTargetPathError):
            detect(symlink_target, snapshot_store)

        assert snapshot_store.replace_calls == []

    def test_raises_access_error_when_target_directory_cannot_be_scanned(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        target_path = tmp_path / "study"
        target_path.mkdir()
        snapshot_store = _RecordingSnapshotStore()
        _patch_scandir_failure(monkeypatch, failing_path=target_path)

        with pytest.raises(TargetPathAccessError):
            detect(target_path, snapshot_store)

    def test_raises_access_error_when_nested_directory_cannot_be_scanned(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        target_path = tmp_path / "study"
        nested_path = target_path / "python"
        nested_path.mkdir(parents=True)
        _write_markdown_file(
            target_path,
            "typescript/generics.md",
            mtime_ns=1716121000000000000,
        )
        snapshot_store = _RecordingSnapshotStore()
        _patch_scandir_failure(monkeypatch, failing_path=nested_path)

        with pytest.raises(TargetPathAccessError):
            detect(target_path, snapshot_store)

    def test_raises_access_error_when_mtime_lookup_fails_for_markdown_file(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        target_path = tmp_path / "study"
        target_path.mkdir()
        failing_path = target_path / "python" / "basics.md"
        _write_markdown_file(
            target_path,
            "python/basics.md",
            mtime_ns=1716122000000000000,
        )
        snapshot_store = _RecordingSnapshotStore()
        _patch_mtime_lookup_failure(monkeypatch, failing_path=failing_path)

        with pytest.raises(TargetPathAccessError):
            detect(target_path, snapshot_store)

    def test_tc_34_raises_persistence_error_when_snapshot_load_fails(
        self,
        tmp_path: Path,
    ) -> None:
        target_path = tmp_path / "study"
        target_path.mkdir()
        snapshot_store = _RecordingSnapshotStore(load_error=RuntimeError("load failed"))

        with pytest.raises(ScanStatePersistenceError):
            detect(target_path, snapshot_store)

        assert snapshot_store.replace_calls == []

    def test_tc_35_raises_persistence_error_when_snapshot_save_fails(
        self,
        tmp_path: Path,
    ) -> None:
        target_path = tmp_path / "study"
        target_path.mkdir()
        _write_markdown_file(
            target_path,
            "python/basics.md",
            mtime_ns=1716123000000000000,
        )
        snapshot_store = _RecordingSnapshotStore(
            replace_error=RuntimeError("replace failed"),
        )

        with pytest.raises(ScanStatePersistenceError):
            detect(target_path, snapshot_store)

        assert snapshot_store.replace_calls == [
            (
                _snapshot_key(target_path),
                {"python/basics.md": 1716123000000000000},
            ),
        ]


class TestFileDiffDetectorObservabilityAndSnapshotPersistence:
    def test_tc_33_raises_access_error_and_does_not_save_snapshot_when_nested_directory_scan_fails(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        target_path = tmp_path / "study"
        nested_path = target_path / "private"
        target_path.mkdir()
        nested_path.mkdir()
        _write_markdown_file(
            target_path,
            "secret.md",
            mtime_ns=1716123000000000000,
        )
        snapshot_store = _RecordingSnapshotStore()
        _patch_scandir_failure(monkeypatch, failing_path=nested_path)

        with pytest.raises(TargetPathAccessError):
            detect(target_path, snapshot_store)

        assert snapshot_store.replace_calls == []

    def test_does_not_save_snapshot_when_nested_directory_scan_fails(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        target_path = tmp_path / "study"
        nested_path = target_path / "python"
        nested_path.mkdir(parents=True)
        _write_markdown_file(
            target_path,
            "python/basics.md",
            mtime_ns=1716124000000000000,
        )
        snapshot_store = _RecordingSnapshotStore()
        _patch_scandir_failure(monkeypatch, failing_path=nested_path)

        with pytest.raises(TargetPathAccessError):
            detect(target_path, snapshot_store)

        assert snapshot_store.replace_calls == []

    def test_does_not_save_snapshot_when_mtime_lookup_fails(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        target_path = tmp_path / "study"
        target_path.mkdir()
        failing_path = target_path / "python" / "basics.md"
        _write_markdown_file(
            target_path,
            "python/basics.md",
            mtime_ns=1716125000000000000,
        )
        snapshot_store = _RecordingSnapshotStore()
        _patch_mtime_lookup_failure(monkeypatch, failing_path=failing_path)

        with pytest.raises(TargetPathAccessError):
            detect(target_path, snapshot_store)

        assert snapshot_store.replace_calls == []

    def test_persists_latest_snapshot_with_relative_posix_paths_and_nanosecond_mtimes(
        self,
        tmp_path: Path,
    ) -> None:
        target_path = tmp_path / "study"
        target_path.mkdir()
        _write_markdown_file(
            target_path,
            "python/basics.md",
            mtime_ns=1716126000000000000,
        )
        _write_markdown_file(
            target_path,
            "typescript/generics.md",
            mtime_ns=1716126001000000000,
        )
        snapshot_store = _RecordingSnapshotStore()

        detect(target_path, snapshot_store)

        assert snapshot_store.replace_calls == [
            (
                _snapshot_key(target_path),
                {
                    "python/basics.md": 1716126000000000000,
                    "typescript/generics.md": 1716126001000000000,
                },
            ),
        ]

    def test_keeps_count_fields_consistent_with_each_result_list(
        self,
        tmp_path: Path,
    ) -> None:
        target_path = tmp_path / "study"
        target_path.mkdir()
        snapshot_store = _RecordingSnapshotStore(
            snapshots={
                _snapshot_key(target_path): {
                    "same.md": 1716126999000000000,
                    "updated.md": 1716126999000000000,
                    "deleted.md": 1716126999000000000,
                },
            },
        )
        _write_markdown_file(
            target_path,
            "same.md",
            mtime_ns=1716126999000000000,
        )
        _write_markdown_file(
            target_path,
            "updated.md",
            mtime_ns=1716127000000000000,
        )
        _write_markdown_file(
            target_path,
            "new.md",
            mtime_ns=1716127001000000000,
        )

        actual = _normalize_result(detect(target_path, snapshot_store))

        assert actual["new_count"] == len(actual["new_files"])
        assert actual["updated_count"] == len(actual["updated_files"])
        assert actual["deleted_count"] == len(actual["deleted_files"])
        assert actual["new_files"] == ["new.md"]
        assert actual["updated_files"] == ["updated.md"]
        assert actual["deleted_files"] == ["deleted.md"]

    def test_tc_36_emits_observability_fields_on_success(
        self,
        tmp_path: Path,
    ) -> None:
        from structlog.testing import capture_logs

        target_path = tmp_path / "study"
        target_path.mkdir()
        _write_markdown_file(
            target_path,
            "python/basics.md",
            mtime_ns=1716128000000000000,
        )
        _write_markdown_file(
            target_path,
            "python/async.md",
            mtime_ns=1716128001000000000,
        )
        _write_plain_file(target_path, "assets/logo.png")
        snapshot_store = _RecordingSnapshotStore(
            snapshots={
                _snapshot_key(target_path): {
                    "python/basics.md": 1716127000000000000,
                },
            },
        )

        with capture_logs() as cap_logs:
            actual = _normalize_result(detect(target_path, snapshot_store))

        assert actual == {
            "target_path": str(target_path.resolve()),
            "new_files": ["python/async.md"],
            "updated_files": ["python/basics.md"],
            "deleted_files": [],
            "new_count": 1,
            "updated_count": 1,
            "deleted_count": 0,
        }

        events = _find_log_events(cap_logs, "file_diff_detector_completed")
        assert len(events) == 1
        event = events[0]
        assert event["target_path"] == str(target_path.resolve())
        assert event["new_count"] == 1
        assert event["updated_count"] == 1
        assert event["deleted_count"] == 0
        assert type(event["processing_time_ms"]) is int
        assert event["processing_time_ms"] >= 0

    def test_tc_22_returns_nested_relative_posix_paths_in_lexicographic_order(
        self,
        tmp_path: Path,
    ) -> None:
        target_path = tmp_path / "study"
        target_path.mkdir()
        _write_markdown_file(
            target_path,
            "zeta/last.md",
            mtime_ns=1716129000000000000,
        )
        _write_markdown_file(
            target_path,
            "alpha/first.md",
            mtime_ns=1716129001000000000,
        )
        _write_markdown_file(
            target_path,
            "alpha/beta/middle.md",
            mtime_ns=1716129002000000000,
        )
        snapshot_store = _RecordingSnapshotStore()

        actual = _normalize_result(detect(target_path, snapshot_store))

        assert actual == {
            "target_path": str(target_path.resolve()),
            "new_files": [
                "alpha/beta/middle.md",
                "alpha/first.md",
                "zeta/last.md",
            ],
            "updated_files": [],
            "deleted_files": [],
            "new_count": 3,
            "updated_count": 0,
            "deleted_count": 0,
        }
        _assert_paths_are_posix_normalized(actual["new_files"])

    def test_updated_files_are_sorted_in_lexicographic_order(
        self,
        tmp_path: Path,
    ) -> None:
        target_path = tmp_path / "study"
        target_path.mkdir()
        _write_markdown_file(target_path, "zeta.md", mtime_ns=100)
        _write_markdown_file(target_path, "alpha.md", mtime_ns=200)
        _write_markdown_file(target_path, "middle.md", mtime_ns=300)
        snapshot_store = _RecordingSnapshotStore(
            snapshots={
                _snapshot_key(target_path): {
                    "zeta.md": 1,
                    "alpha.md": 2,
                    "middle.md": 3,
                },
            },
        )

        actual = _normalize_result(detect(target_path, snapshot_store))

        assert actual["updated_files"] == ["alpha.md", "middle.md", "zeta.md"]
        assert actual["updated_count"] == 3
