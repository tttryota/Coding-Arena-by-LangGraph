"""FileDiffSnapshotStore Protocol の SQLAlchemy concrete 実装。"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy.orm import Session

from infrastructure.rdb.models import DiffSnapshot

if TYPE_CHECKING:
    from sqlalchemy import Engine


class SqlFileDiffSnapshotStore:
    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def load(self, snapshot_key: str) -> dict[str, int] | None:
        with Session(self._engine) as s:
            row = s.get(DiffSnapshot, snapshot_key)
            if row is None:
                return None
            return json.loads(row.files_json)

    def replace(self, snapshot_key: str, files: dict[str, int]) -> None:
        with Session(self._engine) as s, s.begin():
            row = s.get(DiffSnapshot, snapshot_key)
            if row is None:
                row = DiffSnapshot(
                    snapshot_key=snapshot_key,
                    files_json=json.dumps(files),
                    updated_at=datetime.now(tz=UTC),
                )
                s.add(row)
            else:
                row.files_json = json.dumps(files)
                row.updated_at = datetime.now(tz=UTC)


__all__ = ["SqlFileDiffSnapshotStore"]
