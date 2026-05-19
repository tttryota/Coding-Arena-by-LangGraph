from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from time import perf_counter_ns
from typing import Protocol

import structlog

logger = structlog.get_logger(__name__)


class TargetPathNotFoundError(Exception):
    pass


class InvalidTargetPathError(Exception):
    pass


class TargetPathAccessError(Exception):
    pass


class ScanStatePersistenceError(Exception):
    pass


class FileDiffSnapshotStore(Protocol):
    def load(self, snapshot_key: str) -> dict[str, int] | None: ...

    def replace(self, snapshot_key: str, files: dict[str, int]) -> None: ...


@dataclass(frozen=True)
class FileDiffResult:
    target_path: str
    new_files: list[str]
    updated_files: list[str]
    deleted_files: list[str]
    new_count: int
    updated_count: int
    deleted_count: int


@dataclass(frozen=True)
class _ScanResult:
    files: dict[str, int]
    scanned_entry_count: int
    markdown_file_count: int


def detect(
    target_path: str | Path,
    snapshot_store: FileDiffSnapshotStore,
) -> FileDiffResult:
    started_at_ns = perf_counter_ns()
    normalized_target_path = _validate_target_path(target_path)
    snapshot_key = str(normalized_target_path)
    previous_snapshot = _load_snapshot(snapshot_store, snapshot_key)
    scan_result = _scan_markdown_files(normalized_target_path)
    result = _build_result(
        target_path=snapshot_key,
        previous_snapshot=previous_snapshot,
        current_snapshot=scan_result.files,
    )
    _replace_snapshot(snapshot_store, snapshot_key, scan_result.files)
    _log_success(
        target_path=snapshot_key,
        result=result,
        scan_result=scan_result,
        started_at_ns=started_at_ns,
    )
    return result


def _validate_target_path(target_path: str | Path) -> Path:
    candidate = Path(target_path)

    try:
        if not candidate.exists():
            message = f"target path does not exist: {candidate}"
            raise TargetPathNotFoundError(message)
        if candidate.is_symlink() or not candidate.is_dir():
            message = f"target path must be a non-symlink directory: {candidate}"
            raise InvalidTargetPathError(message)
        return candidate.resolve()
    except (TargetPathNotFoundError, InvalidTargetPathError):
        raise
    except OSError as exc:
        message = f"failed to access target path: {candidate}"
        raise TargetPathAccessError(message) from exc


def _load_snapshot(
    snapshot_store: FileDiffSnapshotStore,
    snapshot_key: str,
) -> dict[str, int] | None:
    try:
        snapshot = snapshot_store.load(snapshot_key)
    except Exception as exc:
        message = f"failed to load snapshot: {snapshot_key}"
        raise ScanStatePersistenceError(message) from exc

    if snapshot is None:
        return None
    return dict(snapshot)


def _replace_snapshot(
    snapshot_store: FileDiffSnapshotStore,
    snapshot_key: str,
    files: dict[str, int],
) -> None:
    try:
        snapshot_store.replace(snapshot_key, dict(files))
    except Exception as exc:
        message = f"failed to persist snapshot: {snapshot_key}"
        raise ScanStatePersistenceError(message) from exc


def _scan_markdown_files(target_path: Path) -> _ScanResult:
    discovered_files: dict[str, int] = {}
    scanned_entry_count = 0
    directories_to_scan = [target_path]

    while directories_to_scan:
        current_directory = directories_to_scan.pop()
        entries = _scan_directory_entries(current_directory)

        for entry in entries:
            scanned_entry_count += 1
            _process_scanned_entry(
                target_path=target_path,
                entry=entry,
                discovered_files=discovered_files,
                directories_to_scan=directories_to_scan,
            )

    return _ScanResult(
        files=discovered_files,
        scanned_entry_count=scanned_entry_count,
        markdown_file_count=len(discovered_files),
    )


def _scan_directory_entries(current_directory: Path) -> list[os.DirEntry[str]]:
    try:
        with os.scandir(current_directory) as iterator:
            return sorted(iterator, key=lambda entry: entry.name)
    except OSError as exc:
        message = f"failed to scan directory: {current_directory}"
        raise TargetPathAccessError(message) from exc


def _process_scanned_entry(
    *,
    target_path: Path,
    entry: os.DirEntry[str],
    discovered_files: dict[str, int],
    directories_to_scan: list[Path],
) -> None:
    try:
        if entry.is_symlink():
            return
        if entry.is_dir(follow_symlinks=False):
            directories_to_scan.append(Path(entry.path))
            return
        if not entry.is_file(follow_symlinks=False):
            return
        if not _is_markdown_file(entry.name):
            return
        _record_markdown_file(target_path, entry, discovered_files)
    except OSError as exc:
        message = f"failed to inspect entry: {entry.path}"
        raise TargetPathAccessError(message) from exc


def _is_markdown_file(filename: str) -> bool:
    return filename.endswith(".md")


def _record_markdown_file(
    target_path: Path,
    entry: os.DirEntry[str],
    discovered_files: dict[str, int],
) -> None:
    stat_result = entry.stat(follow_symlinks=False)
    relative_path = Path(entry.path).relative_to(target_path).as_posix()
    discovered_files[relative_path] = stat_result.st_mtime_ns


def _build_result(
    *,
    target_path: str,
    previous_snapshot: dict[str, int] | None,
    current_snapshot: dict[str, int],
) -> FileDiffResult:
    current_paths = set(current_snapshot)

    if previous_snapshot is None:
        new_files = sorted(current_paths)
        updated_files: list[str] = []
        deleted_files: list[str] = []
    else:
        previous_paths = set(previous_snapshot)
        new_files = sorted(current_paths - previous_paths)
        updated_files = sorted(
            path
            for path in current_paths & previous_paths
            if current_snapshot[path] != previous_snapshot[path]
        )
        deleted_files = sorted(previous_paths - current_paths)

    return FileDiffResult(
        target_path=target_path,
        new_files=new_files,
        updated_files=updated_files,
        deleted_files=deleted_files,
        new_count=len(new_files),
        updated_count=len(updated_files),
        deleted_count=len(deleted_files),
    )


def _log_success(
    *,
    target_path: str,
    result: FileDiffResult,
    scan_result: _ScanResult,
    started_at_ns: int,
) -> None:
    processing_time_ms = (perf_counter_ns() - started_at_ns) // 1_000_000
    logger.info(
        "file_diff_detector_completed",
        target_path=target_path,
        scanned_entry_count=scan_result.scanned_entry_count,
        markdown_file_count=scan_result.markdown_file_count,
        new_count=result.new_count,
        updated_count=result.updated_count,
        deleted_count=result.deleted_count,
        processing_time_ms=processing_time_ms,
    )
