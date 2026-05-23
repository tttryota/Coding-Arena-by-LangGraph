"""Ingestion RDB Store concrete implementations のテスト。

SqlIngestionFeedbackStore, SqlFileDiffSnapshotStore の Protocol 準拠と CRUD 動作を検証。
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

import pytest
from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker


def _setup_db() -> Engine:
    import infrastructure.rdb.models  # noqa: F401
    from infrastructure.rdb.base import Base

    eng = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(eng)
    return eng


@pytest.fixture
def engine() -> Engine:
    return _setup_db()


@pytest.fixture
def db_session(engine: Engine) -> Session:
    factory = sessionmaker(bind=engine)
    session = factory()
    try:
        yield session  # type: ignore[misc]
    finally:
        session.close()


@pytest.fixture
def roadmap_row(db_session: Session) -> object:
    from infrastructure.rdb.models import Roadmap

    r = Roadmap(id=uuid.uuid4(), topic="TypeScript", created_at=datetime.now(tz=UTC))
    db_session.add(r)
    db_session.commit()
    return r


@pytest.fixture
def roadmap_item_row(db_session: Session, roadmap_row: object) -> object:
    from infrastructure.rdb.models import RoadmapItem

    now = datetime.now(tz=UTC)
    item = RoadmapItem(
        id=uuid.uuid4(), roadmap_id=roadmap_row.id,  # type: ignore[union-attr]
        level="detail", title="ジェネリクス", description="TS generics",
        order=1, score=0, created_at=now, updated_at=now,
    )
    db_session.add(item)
    db_session.commit()
    return item


# ---------------------------------------------------------------------------
# SqlIngestionFeedbackStore
# ---------------------------------------------------------------------------


class TestSqlIngestionFeedbackStoreCreate:
    def test_create_persists_and_returns_record(
        self, engine: Engine, db_session: Session,
    ) -> None:
        from ingestion.domain.ingestion_feedback_types import (
            NewIngestionFeedbackRecord,
        )
        from ingestion.infrastructure.sql_ingestion_feedback_store import (
            SqlIngestionFeedbackStore,
        )

        store = SqlIngestionFeedbackStore(engine)
        now_str = datetime.now(tz=UTC).isoformat()
        record = NewIngestionFeedbackRecord(
            source_path="study/ts/generics.md",
            roadmap_item_id=None,
            title="内容精査",
            body="ジェネリクスの説明が正確です",
            is_read=False,
            created_at=now_str,
            read_at=None,
        )
        result = store.create(record)

        assert result.id is not None
        assert result.source_path == "study/ts/generics.md"
        assert result.title == "内容精査"
        assert result.is_read is False

    def test_create_with_roadmap_item_id(
        self, engine: Engine, db_session: Session, roadmap_item_row: object,
    ) -> None:
        from ingestion.domain.ingestion_feedback_types import (
            NewIngestionFeedbackRecord,
        )
        from ingestion.infrastructure.sql_ingestion_feedback_store import (
            SqlIngestionFeedbackStore,
        )

        store = SqlIngestionFeedbackStore(engine)
        record = NewIngestionFeedbackRecord(
            source_path="study/ts/generics.md",
            roadmap_item_id=roadmap_item_row.id,  # type: ignore[union-attr]
            title="関連あり",
            body="関連フィードバック",
            is_read=False,
            created_at=datetime.now(tz=UTC).isoformat(),
            read_at=None,
        )
        result = store.create(record)

        assert result.roadmap_item_id == roadmap_item_row.id  # type: ignore[union-attr]


class TestSqlIngestionFeedbackStoreListing:
    def _seed_feedbacks(self, engine: Engine) -> None:
        from ingestion.domain.ingestion_feedback_types import (
            NewIngestionFeedbackRecord,
        )
        from ingestion.infrastructure.sql_ingestion_feedback_store import (
            SqlIngestionFeedbackStore,
        )

        store = SqlIngestionFeedbackStore(engine)
        for i in range(3):
            store.create(NewIngestionFeedbackRecord(
                source_path=f"file{i}.md",
                roadmap_item_id=None,
                title=f"FB{i}",
                body=f"body{i}",
                is_read=i == 1,
                created_at=f"2026-05-{20 + i:02d}T00:00:00+00:00",
                read_at=f"2026-05-{20 + i:02d}T01:00:00+00:00" if i == 1 else None,
            ))

    def test_find_feedbacks_all(self, engine: Engine, db_session: Session) -> None:
        from ingestion.infrastructure.sql_ingestion_feedback_store import (
            SqlIngestionFeedbackStore,
        )

        self._seed_feedbacks(engine)
        store = SqlIngestionFeedbackStore(engine)
        results = store.find_feedbacks(date_from=None, date_to=None, read_status="all")

        assert len(results) == 3

    def test_find_feedbacks_unread_only(self, engine: Engine, db_session: Session) -> None:
        from ingestion.infrastructure.sql_ingestion_feedback_store import (
            SqlIngestionFeedbackStore,
        )

        self._seed_feedbacks(engine)
        store = SqlIngestionFeedbackStore(engine)
        results = store.find_feedbacks(date_from=None, date_to=None, read_status="unread")

        assert len(results) == 2
        assert all(not r.is_read for r in results)

    def test_find_feedbacks_with_date_range(self, engine: Engine, db_session: Session) -> None:
        from ingestion.infrastructure.sql_ingestion_feedback_store import (
            SqlIngestionFeedbackStore,
        )

        self._seed_feedbacks(engine)
        store = SqlIngestionFeedbackStore(engine)
        results = store.find_feedbacks(
            date_from="2026-05-21T00:00:00+00:00",
            date_to="2026-05-22T23:59:59+00:00",
            read_status="all",
        )

        assert len(results) == 2


class TestSqlIngestionFeedbackStoreReadWriter:
    def test_get_by_id_returns_record(self, engine: Engine, db_session: Session) -> None:
        from ingestion.domain.ingestion_feedback_types import (
            NewIngestionFeedbackRecord,
        )
        from ingestion.infrastructure.sql_ingestion_feedback_store import (
            SqlIngestionFeedbackStore,
        )

        store = SqlIngestionFeedbackStore(engine)
        created = store.create(NewIngestionFeedbackRecord(
            source_path="test.md", roadmap_item_id=None, title="T", body="B",
            is_read=False, created_at=datetime.now(tz=UTC).isoformat(), read_at=None,
        ))
        result = store.get_by_id(created.id)

        assert result is not None
        assert result.title == "T"

    def test_get_by_id_returns_none_for_missing(self, engine: Engine, db_session: Session) -> None:
        from ingestion.infrastructure.sql_ingestion_feedback_store import (
            SqlIngestionFeedbackStore,
        )

        store = SqlIngestionFeedbackStore(engine)
        result = store.get_by_id(uuid.uuid4())

        assert result is None

    def test_update_read_status(self, engine: Engine, db_session: Session) -> None:
        from ingestion.domain.ingestion_feedback_types import (
            NewIngestionFeedbackRecord,
        )
        from ingestion.infrastructure.sql_ingestion_feedback_store import (
            SqlIngestionFeedbackStore,
        )

        store = SqlIngestionFeedbackStore(engine)
        created = store.create(NewIngestionFeedbackRecord(
            source_path="test.md", roadmap_item_id=None, title="T", body="B",
            is_read=False, created_at=datetime.now(tz=UTC).isoformat(), read_at=None,
        ))
        read_at = datetime.now(tz=UTC).isoformat()
        updated = store.update_read_status(created.id, is_read=True, read_at=read_at)

        assert updated.is_read is True
        assert updated.read_at is not None


# ---------------------------------------------------------------------------
# SqlFileDiffSnapshotStore
# ---------------------------------------------------------------------------


class TestSqlFileDiffSnapshotStore:
    def test_load_returns_none_when_no_snapshot(self, engine: Engine, db_session: Session) -> None:
        from ingestion.infrastructure.sql_file_diff_snapshot_store import (
            SqlFileDiffSnapshotStore,
        )

        store = SqlFileDiffSnapshotStore(engine)
        result = store.load("/nonexistent")

        assert result is None

    def test_replace_and_load_roundtrip(self, engine: Engine, db_session: Session) -> None:
        from ingestion.infrastructure.sql_file_diff_snapshot_store import (
            SqlFileDiffSnapshotStore,
        )

        store = SqlFileDiffSnapshotStore(engine)
        files = {"file1.md": 12345, "file2.md": 67890}
        store.replace("/vault/path", files)

        result = store.load("/vault/path")

        assert result == files

    def test_replace_overwrites_existing(self, engine: Engine, db_session: Session) -> None:
        from ingestion.infrastructure.sql_file_diff_snapshot_store import (
            SqlFileDiffSnapshotStore,
        )

        store = SqlFileDiffSnapshotStore(engine)
        store.replace("/vault", {"old.md": 111})
        store.replace("/vault", {"new.md": 222})

        result = store.load("/vault")

        assert result == {"new.md": 222}

    def test_different_keys_are_independent(self, engine: Engine, db_session: Session) -> None:
        from ingestion.infrastructure.sql_file_diff_snapshot_store import (
            SqlFileDiffSnapshotStore,
        )

        store = SqlFileDiffSnapshotStore(engine)
        store.replace("/vault1", {"a.md": 1})
        store.replace("/vault2", {"b.md": 2})

        assert store.load("/vault1") == {"a.md": 1}
        assert store.load("/vault2") == {"b.md": 2}
