from __future__ import annotations

from pathlib import Path
from typing import Protocol


class FileDiffResult:
    new_files: list[str]
    modified_files: list[str]
    deleted_files: list[str]
    new_count: int
    modified_count: int
    deleted_count: int


class TargetPathNotFoundError(Exception): ...


class TargetPathTypeError(Exception): ...


class TargetPathAccessError(Exception): ...


class SnapshotPersistenceError(Exception): ...


class SnapshotStore(Protocol):
    def load(self, snapshot_key: str) -> dict[str, int] | None: ...
    def replace(self, snapshot_key: str, files: dict[str, int]) -> None: ...


def detect(target_path: str | Path, snapshot_store: SnapshotStore) -> FileDiffResult: ...
