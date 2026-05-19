from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from pathlib import Path
from time import perf_counter_ns
from typing import Protocol

logger = logging.getLogger(__name__)


class TargetPathNotFoundError(Exception):
    pass


class TargetPathTypeError(Exception):
    pass


class TargetPathAccessError(Exception):
    pass


class SnapshotPersistenceError(Exception):
    pass


class SnapshotStore(Protocol):
    def load(self, snapshot_key: str) -> dict[str, int] | None: ...

    def replace(self, snapshot_key: str, files: dict[str, int]) -> None: ...


@dataclass(frozen=True)
class FileDiffResult:
    new_files: list[str]
    modified_files: list[str]
    deleted_files: list[str]
    new_count: int
    modified_count: int
    deleted_count: int


@dataclass(frozen=True)
class _ScanResult:
    files: dict[str, int]
    scanned_entry_count: int


def detect(target_path: str | Path, snapshot_store: SnapshotStore) -> FileDiffResult:
    started_at_ns = perf_counter_ns()
    normalized_target_path = Path(target_path).resolve()
    snapshot_key = str(normalized_target_path)

    _validate_target_path(normalized_target_path)

    previous_snapshot = _load_snapshot(snapshot_store, snapshot_key)
    scan_result = _scan_markdown_files(normalized_target_path)
    result = _build_result(previous_snapshot, scan_result.files)
    _replace_snapshot(snapshot_store, snapshot_key, scan_result.files)
    _log_success(
        snapshot_key=snapshot_key,
        scanned_entry_count=scan_result.scanned_entry_count,
        markdown_file_count=len(scan_result.files),
        result=result,
        started_at_ns=started_at_ns,
    )
    return result


def _validate_target_path(target_path: Path) -> None:
    if not target_path.exists():
        message = f"target path does not exist: {target_path}"
        raise TargetPathNotFoundError(message)
    if not target_path.is_dir():
        message = f"target path is not a directory: {target_path}"
        raise TargetPathTypeError(message)


def _load_snapshot(
    snapshot_store: SnapshotStore,
    snapshot_key: str,
) -> dict[str, int] | None:
    try:
        snapshot = snapshot_store.load(snapshot_key)
    except Exception as exc:
        message = f"failed to load snapshot for target path: {snapshot_key}"
        raise SnapshotPersistenceError(message) from exc
    if snapshot is None:
        return None
    return dict(snapshot)


def _replace_snapshot(
    snapshot_store: SnapshotStore,
    snapshot_key: str,
    files: dict[str, int],
) -> None:
    try:
        snapshot_store.replace(snapshot_key, dict(files))
    except Exception as exc:
        message = f"failed to replace snapshot for target path: {snapshot_key}"
        raise SnapshotPersistenceError(message) from exc


def _scan_markdown_files(target_path: Path) -> _ScanResult:
    files: dict[str, int] = {}
    scanned_entry_count = 0

    def _walk(directory: Path) -> None:
        nonlocal scanned_entry_count
        try:
            with os.scandir(directory) as entries:
                for entry in entries:
                    scanned_entry_count += 1
                    if entry.is_symlink():
                        continue
                    if entry.is_dir(follow_symlinks=False):
                        _walk(Path(entry.path))
                        continue
                    if not entry.is_file(follow_symlinks=False):
                        continue
                    if Path(entry.name).suffix != ".md":
                        continue
                    relative_path = Path(entry.path).relative_to(target_path)
                    normalized_relative_path = relative_path.as_posix()
                    files[normalized_relative_path] = entry.stat(
                        follow_symlinks=False,
                    ).st_mtime_ns
        except OSError as exc:
            message = f"failed to scan target path: {target_path}"
            raise TargetPathAccessError(message) from exc

    _walk(target_path)
    return _ScanResult(files=files, scanned_entry_count=scanned_entry_count)


def _build_result(
    previous_snapshot: dict[str, int] | None,
    current_snapshot: dict[str, int],
) -> FileDiffResult:
    previous_files = {} if previous_snapshot is None else previous_snapshot

    new_files = sorted(path for path in current_snapshot if path not in previous_files)
    modified_files = sorted(
        path
        for path, mtime_ns in current_snapshot.items()
        if path in previous_files and previous_files[path] != mtime_ns
    )
    deleted_files = sorted(path for path in previous_files if path not in current_snapshot)

    return FileDiffResult(
        new_files=new_files,
        modified_files=modified_files,
        deleted_files=deleted_files,
        new_count=len(new_files),
        modified_count=len(modified_files),
        deleted_count=len(deleted_files),
    )


def _log_success(
    *,
    snapshot_key: str,
    scanned_entry_count: int,
    markdown_file_count: int,
    result: FileDiffResult,
    started_at_ns: int,
) -> None:
    processing_time_ms = (perf_counter_ns() - started_at_ns) // 1_000_000
    logger.info(
        "file_diff_detected",
        extra={
            "target_path": snapshot_key,
            "scanned_entry_count": scanned_entry_count,
            "markdown_file_count": markdown_file_count,
            "new_count": result.new_count,
            "modified_count": result.modified_count,
            "deleted_count": result.deleted_count,
            "processing_time_ms": int(processing_time_ms),
        },
    )
