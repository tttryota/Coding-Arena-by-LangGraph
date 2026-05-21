from __future__ import annotations

from pathlib import Path
from typing import Protocol

class FileDiffResult:
    target_path: str
    new_files: list[str]
    updated_files: list[str]
    deleted_files: list[str]
    new_count: int
    updated_count: int
    deleted_count: int


class TargetPathNotFoundError(Exception): ...


class InvalidTargetPathError(Exception): ...


class TargetPathAccessError(Exception): ...


class ScanStatePersistenceError(Exception): ...


class FileDiffSnapshotStore(Protocol):
    def load(self, snapshot_key: str) -> dict[str, int] | None: ...
    def replace(self, snapshot_key: str, files: dict[str, int]) -> None: ...


def detect(target_path: str | Path, snapshot_store: FileDiffSnapshotStore) -> FileDiffResult: ...
