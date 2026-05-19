import logging
import os
from pathlib import Path
from types import TracebackType
from typing import Protocol, Self, TypedDict

import pytest

from core.ingestion.infrastructure.file_diff_detector import (
    FileDiffResult,
    SnapshotPersistenceError,
    TargetPathAccessError,
    TargetPathNotFoundError,
    TargetPathTypeError,
    detect,
)


class _RecordingSnapshotStore:
    def __init__(
        self,
        snapshots: dict[str, dict[str, int]] | None = None,
        *,
        load_error: Exception | None = None,
        replace_error: Exception | None = None,
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
        files = self._snapshots.get(snapshot_key)
        if files is None:
            return None
        return dict(files)

    def replace(self, snapshot_key: str, files: dict[str, int]) -> None:
        normalized_files = dict(files)
        self.replace_calls.append((snapshot_key, normalized_files))
        if self._replace_error is not None:
            raise self._replace_error
        self._snapshots[snapshot_key] = normalized_files

    def snapshot_for(self, snapshot_key: str) -> dict[str, int] | None:
        files = self._snapshots.get(snapshot_key)
        if files is None:
            return None
        return dict(files)


class _NormalizedFileDiffResult(TypedDict):
    new_files: list[str]
    modified_files: list[str]
    deleted_files: list[str]
    new_count: int
    modified_count: int
    deleted_count: int


class _SupportsScandirIterator(Protocol):
    def __enter__(self) -> Self: ...

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> bool | None: ...

    def __iter__(self) -> Self: ...

    def __next__(self) -> os.DirEntry[str]: ...


def _snapshot_key(target_path: Path) -> str:
    return str(target_path.resolve())


def _write_markdown_file(target_path: Path, relative_path: str, mtime_ns: int) -> None:
    file_path = target_path / Path(relative_path)
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_text(f"# {relative_path}\n", encoding="utf-8")
    os.utime(file_path, ns=(mtime_ns, mtime_ns))


def _write_plain_file(target_path: Path, relative_path: str) -> None:
    file_path = target_path / Path(relative_path)
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_text(relative_path, encoding="utf-8")


def _normalize_result(result: FileDiffResult) -> _NormalizedFileDiffResult:
    assert isinstance(result.new_files, list)
    assert isinstance(result.modified_files, list)
    assert isinstance(result.deleted_files, list)
    assert all(isinstance(path, str) for path in result.new_files)
    assert all(isinstance(path, str) for path in result.modified_files)
    assert all(isinstance(path, str) for path in result.deleted_files)
    assert type(result.new_count) is int
    assert type(result.modified_count) is int
    assert type(result.deleted_count) is int
    return {
        "new_files": list(result.new_files),
        "modified_files": list(result.modified_files),
        "deleted_files": list(result.deleted_files),
        "new_count": result.new_count,
        "modified_count": result.modified_count,
        "deleted_count": result.deleted_count,
    }


def _assert_paths_are_posix_normalized(paths: list[str]) -> None:
    assert all("\\" not in path for path in paths)


class _WindowsLikeRelativePath:
    def __init__(self, relative_path: Path) -> None:
        self._relative_path = relative_path

    def __fspath__(self) -> str:
        return str(self)

    def __getattr__(self, name: str) -> object:
        return getattr(self._relative_path, name)

    def __str__(self) -> str:
        return self._relative_path.as_posix().replace("/", "\\")

    def as_posix(self) -> str:
        return self._relative_path.as_posix()


def _patch_relative_path_stringification_as_windows(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    original_relative_to = Path.relative_to

    def _patched_relative_to(self: Path, *other: Path) -> _WindowsLikeRelativePath:
        relative_path = original_relative_to(self, *other)
        return _WindowsLikeRelativePath(relative_path)

    monkeypatch.setattr(Path, "relative_to", _patched_relative_to)


class _MtimeAccessFailingStatResult:
    def __init__(self, stat_result: os.stat_result) -> None:
        self._stat_result = stat_result

    def __getattr__(self, name: str) -> object:
        return getattr(self._stat_result, name)

    @property
    def st_mtime_ns(self) -> int:
        msg = "mtime lookup failed"
        raise OSError(msg)


class _PatchedDirEntry:
    def __init__(self, dir_entry: os.DirEntry[str], failing_path: str) -> None:
        self._dir_entry = dir_entry
        self._failing_path = failing_path

    def __getattr__(self, name: str) -> object:
        return getattr(self._dir_entry, name)

    def stat(
        self,
        *,
        follow_symlinks: bool = True,
    ) -> _MtimeAccessFailingStatResult | os.stat_result:
        stat_result = self._dir_entry.stat(follow_symlinks=follow_symlinks)
        if os.path.normpath(self._dir_entry.path) != self._failing_path:
            return stat_result
        return _MtimeAccessFailingStatResult(stat_result)


class _PatchedScandirIterator:
    def __init__(self, iterator: _SupportsScandirIterator, failing_path: str) -> None:
        self._iterator = iterator
        self._failing_path = failing_path

    def __enter__(self) -> "_PatchedScandirIterator":
        self._iterator.__enter__()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> bool | None:
        return self._iterator.__exit__(exc_type, exc, tb)

    def __iter__(self) -> "_PatchedScandirIterator":
        return self

    def __next__(self) -> os.DirEntry[str] | _PatchedDirEntry:
        dir_entry = next(self._iterator)
        if os.path.normpath(dir_entry.path) != self._failing_path:
            return dir_entry
        return _PatchedDirEntry(dir_entry, self._failing_path)


def _patch_mtime_lookup_failure(
    monkeypatch: pytest.MonkeyPatch,
    failing_path: Path,
) -> None:
    normalized_failing_path = os.path.normpath(os.fsdecode(failing_path))
    original_path_stat = Path.stat
    original_path_lstat = Path.lstat
    original_os_stat = os.stat
    original_os_lstat = os.lstat
    original_os_scandir = os.scandir

    def _wrap_stat_result_for_path(
        path: str | os.PathLike[str],
        stat_result: os.stat_result,
    ) -> _MtimeAccessFailingStatResult | os.stat_result:
        normalized_path = os.path.normpath(os.fsdecode(path))
        if normalized_path != normalized_failing_path:
            return stat_result
        return _MtimeAccessFailingStatResult(stat_result)

    def _patched_path_stat(
        self: Path,
        *,
        follow_symlinks: bool = True,
    ) -> _MtimeAccessFailingStatResult | os.stat_result:
        stat_result = original_path_stat(self, follow_symlinks=follow_symlinks)
        return _wrap_stat_result_for_path(self, stat_result)

    def _patched_path_lstat(
        self: Path,
    ) -> _MtimeAccessFailingStatResult | os.stat_result:
        stat_result = original_path_lstat(self)
        return _wrap_stat_result_for_path(self, stat_result)

    def _patched_os_stat(
        path: str | os.PathLike[str],
        *,
        dir_fd: int | None = None,
        follow_symlinks: bool = True,
    ) -> _MtimeAccessFailingStatResult | os.stat_result:
        stat_result = original_os_stat(
            path,
            dir_fd=dir_fd,
            follow_symlinks=follow_symlinks,
        )
        return _wrap_stat_result_for_path(path, stat_result)

    def _patched_os_lstat(
        path: str | os.PathLike[str],
        *,
        dir_fd: int | None = None,
    ) -> _MtimeAccessFailingStatResult | os.stat_result:
        stat_result = original_os_lstat(path, dir_fd=dir_fd)
        return _wrap_stat_result_for_path(path, stat_result)

    def _patched_os_scandir(
        path: str | os.PathLike[str],
    ) -> _PatchedScandirIterator:
        iterator = original_os_scandir(path)
        return _PatchedScandirIterator(iterator, normalized_failing_path)

    monkeypatch.setattr(Path, "stat", _patched_path_stat)
    monkeypatch.setattr(Path, "lstat", _patched_path_lstat)
    monkeypatch.setattr(os, "stat", _patched_os_stat)
    monkeypatch.setattr(os, "lstat", _patched_os_lstat)
    monkeypatch.setattr(os, "scandir", _patched_os_scandir)


_OBSERVABILITY_FIELD_NAMES = (
    "target_path",
    "scanned_entry_count",
    "markdown_file_count",
    "new_count",
    "modified_count",
    "deleted_count",
    "processing_time_ms",
)


def _get_observability_record(caplog: pytest.LogCaptureFixture) -> logging.LogRecord:
    matching_records = [
        record
        for record in caplog.records
        if all(hasattr(record, field_name) for field_name in _OBSERVABILITY_FIELD_NAMES)
    ]
    assert matching_records != []
    return matching_records[0]


class TestFileDiffDetectorPhase1:
    def test_tc_01_returns_single_markdown_file_as_new_on_initial_scan(
        self,
        tmp_path: Path,
    ) -> None:
        target_path = tmp_path / "study"
        target_path.mkdir()
        snapshot_key = _snapshot_key(target_path)
        _write_markdown_file(
            target_path,
            "python/basics.md",
            1716100000000000000,
        )
        snapshot_store = _RecordingSnapshotStore()

        actual = _normalize_result(detect(target_path, snapshot_store))

        assert actual == {
            "new_files": ["python/basics.md"],
            "modified_files": [],
            "deleted_files": [],
            "new_count": 1,
            "modified_count": 0,
            "deleted_count": 0,
        }
        assert snapshot_store.load_calls == [snapshot_key]
        assert snapshot_store.replace_calls == [
            (
                snapshot_key,
                {"python/basics.md": 1716100000000000000},
            ),
        ]

    def test_tc_02_returns_empty_diff_when_snapshot_matches_current_scan(
        self,
        tmp_path: Path,
    ) -> None:
        target_path = tmp_path / "study"
        target_path.mkdir()
        snapshot_key = _snapshot_key(target_path)
        _write_markdown_file(
            target_path,
            "python/basics.md",
            1716100000000000000,
        )
        snapshot_store = _RecordingSnapshotStore(
            {
                snapshot_key: {
                    "python/basics.md": 1716100000000000000,
                },
            },
        )

        actual = _normalize_result(detect(target_path, snapshot_store))

        assert actual == {
            "new_files": [],
            "modified_files": [],
            "deleted_files": [],
            "new_count": 0,
            "modified_count": 0,
            "deleted_count": 0,
        }
        assert snapshot_store.load_calls == [snapshot_key]
        assert snapshot_store.replace_calls == [
            (
                snapshot_key,
                {"python/basics.md": 1716100000000000000},
            ),
        ]

    def test_tc_03_normalizes_relative_target_path_and_detected_file_paths(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        target_path = tmp_path / "study"
        target_path.mkdir()
        snapshot_key = _snapshot_key(target_path)
        _write_markdown_file(target_path, "alpha.md", 1716100000000000000)
        _write_markdown_file(target_path, "python/intro.md", 1716100001000000000)
        snapshot_store = _RecordingSnapshotStore()
        monkeypatch.chdir(tmp_path)
        _patch_relative_path_stringification_as_windows(monkeypatch)

        actual = _normalize_result(detect("study", snapshot_store))

        assert actual == {
            "new_files": ["alpha.md", "python/intro.md"],
            "modified_files": [],
            "deleted_files": [],
            "new_count": 2,
            "modified_count": 0,
            "deleted_count": 0,
        }
        assert snapshot_store.load_calls == [snapshot_key]
        assert snapshot_store.replace_calls == [
            (
                snapshot_key,
                {
                    "alpha.md": 1716100000000000000,
                    "python/intro.md": 1716100001000000000,
                },
            ),
        ]
        _assert_paths_are_posix_normalized(actual["new_files"])
        _assert_paths_are_posix_normalized(list(snapshot_store.replace_calls[0][1]))


class TestFileDiffDetectorPhase2:
    def test_tc_10_recursively_scans_only_regular_md_files(
        self,
        tmp_path: Path,
    ) -> None:
        target_path = tmp_path / "study"
        target_path.mkdir()
        _write_markdown_file(
            target_path,
            "python/basics.md",
            1716100000000000000,
        )
        _write_markdown_file(
            target_path,
            "python/advanced.md",
            1716100001000000000,
        )
        _write_plain_file(target_path, "python/notes.txt")
        _write_plain_file(target_path, "README.MD")
        external_file_dir = tmp_path / "external-file"
        external_file_dir.mkdir()
        _write_markdown_file(external_file_dir, "latest.md", 1716100002000000000)
        assets_dir = target_path / "assets"
        assets_dir.mkdir()
        (assets_dir / "latest.md").symlink_to(external_file_dir / "latest.md")
        external_dir = tmp_path / "external-dir"
        external_dir.mkdir()
        _write_markdown_file(external_dir, "old.md", 1716100004000000000)
        (target_path / "archive").symlink_to(external_dir, target_is_directory=True)
        snapshot_store = _RecordingSnapshotStore()

        actual = _normalize_result(detect(target_path, snapshot_store))

        assert actual == {
            "new_files": ["python/advanced.md", "python/basics.md"],
            "modified_files": [],
            "deleted_files": [],
            "new_count": 2,
            "modified_count": 0,
            "deleted_count": 0,
        }

    def test_tc_11_classifies_new_modified_and_deleted_files_in_sorted_order(
        self,
        tmp_path: Path,
    ) -> None:
        target_path = tmp_path / "study"
        target_path.mkdir()
        snapshot_key = _snapshot_key(target_path)
        _write_markdown_file(
            target_path,
            "python/basics.md",
            1716200000000000000,
        )
        _write_markdown_file(
            target_path,
            "python/advanced.md",
            1716100001000000000,
        )
        _write_markdown_file(
            target_path,
            "python/async.md",
            1716200003000000000,
        )
        docker_dir = target_path / "docker"
        docker_dir.mkdir()
        external_dir = tmp_path / "external"
        external_dir.mkdir()
        _write_markdown_file(external_dir, "intro.md", 1716200004000000000)
        (docker_dir / "intro.md").symlink_to(external_dir / "intro.md")
        snapshot_store = _RecordingSnapshotStore(
            {
                snapshot_key: {
                    "python/advanced.md": 1716100001000000000,
                    "python/basics.md": 1716100000000000000,
                    "docker/intro.md": 1716099999000000000,
                },
            },
        )

        actual = _normalize_result(detect(target_path, snapshot_store))

        assert actual == {
            "new_files": ["python/async.md"],
            "modified_files": ["python/basics.md"],
            "deleted_files": ["docker/intro.md"],
            "new_count": 1,
            "modified_count": 1,
            "deleted_count": 1,
        }

    def test_tc_12_treats_rename_as_deleted_and_new(
        self,
        tmp_path: Path,
    ) -> None:
        target_path = tmp_path / "study"
        target_path.mkdir()
        snapshot_key = _snapshot_key(target_path)
        _write_markdown_file(
            target_path,
            "python/b.md",
            1716200000000000000,
        )
        snapshot_store = _RecordingSnapshotStore(
            {
                snapshot_key: {
                    "python/a.md": 1716100000000000000,
                },
            },
        )

        actual = _normalize_result(detect(target_path, snapshot_store))

        assert actual == {
            "new_files": ["python/b.md"],
            "modified_files": [],
            "deleted_files": ["python/a.md"],
            "new_count": 1,
            "modified_count": 0,
            "deleted_count": 1,
        }

    def test_tc_13_keeps_snapshots_isolated_per_target_path(
        self,
        tmp_path: Path,
    ) -> None:
        study_path = tmp_path / "study"
        study_path.mkdir()
        work_path = tmp_path / "work"
        work_path.mkdir()
        study_snapshot_key = _snapshot_key(study_path)
        work_snapshot_key = _snapshot_key(work_path)
        _write_markdown_file(
            study_path,
            "python/basics.md",
            1716200000000000000,
        )
        snapshot_store = _RecordingSnapshotStore(
            {
                study_snapshot_key: {
                    "python/basics.md": 1716100000000000000,
                },
                work_snapshot_key: {
                    "docs/spec.md": 1716000000000000000,
                },
            },
        )

        actual = _normalize_result(detect(study_path, snapshot_store))

        assert actual == {
            "new_files": [],
            "modified_files": ["python/basics.md"],
            "deleted_files": [],
            "new_count": 0,
            "modified_count": 1,
            "deleted_count": 0,
        }
        assert snapshot_store.load_calls == [study_snapshot_key]
        assert snapshot_store.replace_calls == [
            (
                study_snapshot_key,
                {"python/basics.md": 1716200000000000000},
            ),
        ]
        assert snapshot_store.snapshot_for(work_snapshot_key) == {
            "docs/spec.md": 1716000000000000000,
        }


class TestFileDiffDetectorPhase3:
    def test_tc_20_returns_empty_diff_and_saves_empty_snapshot_on_initial_empty_scan(
        self,
        tmp_path: Path,
    ) -> None:
        target_path = tmp_path / "study"
        target_path.mkdir()
        snapshot_key = _snapshot_key(target_path)
        _write_plain_file(target_path, "assets/logo.png")
        external_dir = tmp_path / "external"
        external_dir.mkdir()
        _write_markdown_file(external_dir, "old.md", 1716201001000000000)
        archive_dir = target_path / "archive"
        archive_dir.mkdir()
        (archive_dir / "old.md").symlink_to(external_dir / "old.md")
        snapshot_store = _RecordingSnapshotStore()

        actual = _normalize_result(detect(target_path, snapshot_store))

        assert actual == {
            "new_files": [],
            "modified_files": [],
            "deleted_files": [],
            "new_count": 0,
            "modified_count": 0,
            "deleted_count": 0,
        }
        assert snapshot_store.load_calls == [snapshot_key]
        assert snapshot_store.replace_calls == [(snapshot_key, {})]

    def test_tc_21_returns_all_previous_entries_as_deleted_when_scan_has_no_targets(
        self,
        tmp_path: Path,
    ) -> None:
        target_path = tmp_path / "study"
        target_path.mkdir()
        snapshot_key = _snapshot_key(target_path)
        _write_plain_file(target_path, "assets/logo.png")
        external_dir = tmp_path / "external"
        external_dir.mkdir()
        _write_markdown_file(external_dir, "old.md", 1716201001000000000)
        archive_dir = target_path / "archive"
        archive_dir.mkdir()
        (archive_dir / "old.md").symlink_to(external_dir / "old.md")
        snapshot_store = _RecordingSnapshotStore(
            {
                snapshot_key: {
                    "python/basics.md": 1716100000000000000,
                    "docker/intro.md": 1716099999000000000,
                },
            },
        )

        actual = _normalize_result(detect(target_path, snapshot_store))

        assert actual == {
            "new_files": [],
            "modified_files": [],
            "deleted_files": ["docker/intro.md", "python/basics.md"],
            "new_count": 0,
            "modified_count": 0,
            "deleted_count": 2,
        }
        assert snapshot_store.replace_calls == [(snapshot_key, {})]

    def test_tc_22_treats_same_path_replaced_by_symlink_as_deleted(
        self,
        tmp_path: Path,
    ) -> None:
        target_path = tmp_path / "study"
        target_path.mkdir()
        snapshot_key = _snapshot_key(target_path)
        external_dir = tmp_path / "external"
        external_dir.mkdir()
        _write_markdown_file(external_dir, "basics.md", 1716200000000000000)
        python_dir = target_path / "python"
        python_dir.mkdir()
        (python_dir / "basics.md").symlink_to(external_dir / "basics.md")
        snapshot_store = _RecordingSnapshotStore(
            {
                snapshot_key: {
                    "python/basics.md": 1716100000000000000,
                },
            },
        )

        actual = _normalize_result(detect(target_path, snapshot_store))

        assert actual == {
            "new_files": [],
            "modified_files": [],
            "deleted_files": ["python/basics.md"],
            "new_count": 0,
            "modified_count": 0,
            "deleted_count": 1,
        }

    def test_tc_23_detects_subsecond_mtime_change_as_modified(
        self,
        tmp_path: Path,
    ) -> None:
        target_path = tmp_path / "study"
        target_path.mkdir()
        snapshot_key = _snapshot_key(target_path)
        _write_markdown_file(
            target_path,
            "python/basics.md",
            1716100000000000123,
        )
        snapshot_store = _RecordingSnapshotStore(
            {
                snapshot_key: {
                    "python/basics.md": 1716100000000000000,
                },
            },
        )

        actual = _normalize_result(detect(target_path, snapshot_store))

        assert actual == {
            "new_files": [],
            "modified_files": ["python/basics.md"],
            "deleted_files": [],
            "new_count": 0,
            "modified_count": 1,
            "deleted_count": 0,
        }


class TestFileDiffDetectorPhase4:
    def test_tc_30_raises_not_found_error_for_missing_target_path(
        self,
        tmp_path: Path,
    ) -> None:
        target_path = tmp_path / "missing"
        snapshot_store = _RecordingSnapshotStore()

        with pytest.raises(TargetPathNotFoundError):
            detect(target_path, snapshot_store)

        assert snapshot_store.load_calls == []
        assert snapshot_store.replace_calls == []

    def test_tc_31_raises_type_error_for_non_directory_target_path(
        self,
        tmp_path: Path,
    ) -> None:
        target_path = tmp_path / "study.md"
        target_path.write_text("# file\n", encoding="utf-8")
        snapshot_store = _RecordingSnapshotStore()

        with pytest.raises(TargetPathTypeError):
            detect(target_path, snapshot_store)

        assert snapshot_store.load_calls == []
        assert snapshot_store.replace_calls == []

    def test_tc_32_raises_access_error_when_mtime_lookup_fails_during_scan(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        target_path = tmp_path / "study"
        target_path.mkdir()
        failing_path = target_path / "python" / "basics.md"
        _write_markdown_file(target_path, "python/basics.md", 1716100000000000000)
        snapshot_store = _RecordingSnapshotStore()
        _patch_mtime_lookup_failure(monkeypatch, failing_path)

        with pytest.raises(TargetPathAccessError):
            detect(target_path, snapshot_store)

        assert snapshot_store.replace_calls == []

    def test_tc_33_raises_snapshot_persistence_error_when_load_fails(
        self,
        tmp_path: Path,
    ) -> None:
        target_path = tmp_path / "study"
        target_path.mkdir()
        snapshot_key = _snapshot_key(target_path)
        snapshot_store = _RecordingSnapshotStore(
            load_error=RuntimeError("load failed"),
        )

        with pytest.raises(SnapshotPersistenceError):
            detect(target_path, snapshot_store)

        assert snapshot_store.load_calls == [snapshot_key]
        assert snapshot_store.replace_calls == []

    def test_tc_34_raises_snapshot_persistence_error_when_replace_fails(
        self,
        tmp_path: Path,
    ) -> None:
        target_path = tmp_path / "study"
        target_path.mkdir()
        snapshot_key = _snapshot_key(target_path)
        _write_markdown_file(
            target_path,
            "python/basics.md",
            1716100000000000000,
        )
        snapshot_store = _RecordingSnapshotStore(
            replace_error=RuntimeError("replace failed"),
        )

        with pytest.raises(SnapshotPersistenceError):
            detect(target_path, snapshot_store)

        assert snapshot_store.load_calls == [snapshot_key]
        assert snapshot_store.replace_calls == [
            (
                snapshot_key,
                {"python/basics.md": 1716100000000000000},
            ),
        ]

    def test_tc_35_emits_observability_fields_on_success(
        self,
        tmp_path: Path,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        target_path = tmp_path / "study"
        target_path.mkdir()
        snapshot_key = _snapshot_key(target_path)
        _write_markdown_file(
            target_path,
            "python/basics.md",
            1716200000000000000,
        )
        _write_markdown_file(
            target_path,
            "python/async.md",
            1716200003000000000,
        )
        _write_plain_file(target_path, "assets/logo.png")
        snapshot_store = _RecordingSnapshotStore(
            {
                snapshot_key: {
                    "python/basics.md": 1716100000000000000,
                },
            },
        )

        with caplog.at_level(logging.INFO):
            actual = _normalize_result(detect(target_path, snapshot_store))

        assert actual == {
            "new_files": ["python/async.md"],
            "modified_files": ["python/basics.md"],
            "deleted_files": [],
            "new_count": 1,
            "modified_count": 1,
            "deleted_count": 0,
        }

        record = _get_observability_record(caplog)
        assert getattr(record, "target_path", None) == snapshot_key
        assert type(getattr(record, "scanned_entry_count", None)) is int
        assert getattr(record, "scanned_entry_count", 0) >= 3
        assert getattr(record, "markdown_file_count", None) == 2
        assert getattr(record, "new_count", None) == 1
        assert getattr(record, "modified_count", None) == 1
        assert getattr(record, "deleted_count", None) == 0
        assert type(getattr(record, "processing_time_ms", None)) is int
        assert getattr(record, "processing_time_ms", -1) >= 0
