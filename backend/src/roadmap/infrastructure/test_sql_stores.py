"""Roadmap RDB Store + UuidGenerator + InMemoryJobStatusStore のテスト。"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

import pytest
from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


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
def roadmap_with_items(db_session: Session) -> object:
    from infrastructure.rdb.models import Roadmap, RoadmapItem

    now = datetime.now(tz=UTC)
    roadmap = Roadmap(id=uuid.uuid4(), topic="React", created_at=now)
    db_session.add(roadmap)
    db_session.flush()
    major = RoadmapItem(
        id=uuid.uuid4(), roadmap_id=roadmap.id, parent_id=None,
        level="major", title="Hooks", description="React Hooks",
        order=1, score=0, created_at=now, updated_at=now,
    )
    detail = RoadmapItem(
        id=uuid.uuid4(), roadmap_id=roadmap.id, parent_id=major.id,
        level="detail", title="useState", description="useState hook",
        order=1, score=50, last_quiz_at=now, created_at=now, updated_at=now,
    )
    db_session.add_all([major, detail])
    db_session.commit()
    return roadmap


# ---------------------------------------------------------------------------
# SqlRoadmapPersistenceWriter
# ---------------------------------------------------------------------------


class TestSqlRoadmapPersistenceWriter:
    def test_save_items_persists_roadmap_and_items(
        self, engine: Engine, db_session: Session,
    ) -> None:
        """テスト対象: SqlRoadmapPersistenceWriter の処理。
        テストケース: 個別条件での処理を検証する。
        期待結果: 想定どおりの処理結果が得られる。"""
        from infrastructure.rdb.models import Roadmap, RoadmapItem
        from roadmap.infrastructure.sql_roadmap_persistence_writer import (
            SqlRoadmapPersistenceWriter,
        )

        store = SqlRoadmapPersistenceWriter(engine)
        roadmap_id = uuid.uuid4()
        now_str = datetime.now(tz=UTC).isoformat()

        from roadmap.domain.roadmap_persistence_types import FlatRoadmapItem

        items = [
            FlatRoadmapItem(
                id=uuid.uuid4(), roadmap_id=roadmap_id, parent_id=None,
                level="major", title="TypeScript", description="TS基礎",
                order=1, score=0, created_at=now_str, updated_at=now_str,
            ),
        ]
        store.save_items(roadmap_id, "TypeScript", items)

        with Session(engine) as s:
            roadmap = s.get(Roadmap, roadmap_id)
            assert roadmap is not None
            assert roadmap.topic == "TypeScript"
            item_rows = s.query(RoadmapItem).filter_by(roadmap_id=roadmap_id).all()
            assert len(item_rows) == 1
            assert item_rows[0].title == "TypeScript"

    def test_save_items_with_multiple_items(
        self, engine: Engine, db_session: Session,
    ) -> None:
        """テスト対象: SqlRoadmapPersistenceWriter の処理。
        テストケース: 個別条件での処理を検証する。
        期待結果: 想定どおりの処理結果が得られる。"""
        from infrastructure.rdb.models import RoadmapItem
        from roadmap.domain.roadmap_persistence_types import FlatRoadmapItem
        from roadmap.infrastructure.sql_roadmap_persistence_writer import (
            SqlRoadmapPersistenceWriter,
        )

        store = SqlRoadmapPersistenceWriter(engine)
        roadmap_id = uuid.uuid4()
        parent_id = uuid.uuid4()
        now_str = datetime.now(tz=UTC).isoformat()

        items = [
            FlatRoadmapItem(
                id=parent_id, roadmap_id=roadmap_id, parent_id=None,
                level="major", title="大枠", description="大枠の説明",
                order=1, score=0, created_at=now_str, updated_at=now_str,
            ),
            FlatRoadmapItem(
                id=uuid.uuid4(), roadmap_id=roadmap_id, parent_id=parent_id,
                level="middle", title="中枠", description="中枠の説明",
                order=1, score=0, created_at=now_str, updated_at=now_str,
            ),
        ]
        store.save_items(roadmap_id, "React", items)

        with Session(engine) as s:
            rows = s.query(RoadmapItem).filter_by(roadmap_id=roadmap_id).all()
            assert len(rows) == 2


# ---------------------------------------------------------------------------
# SqlRoadmapRetrievalReader
# ---------------------------------------------------------------------------


class TestSqlRoadmapRetrievalReader:
    def test_find_roadmap_returns_record(
        self, engine: Engine, db_session: Session, roadmap_with_items: object,
    ) -> None:
        """テスト対象: SqlRoadmapRetrievalReader の処理。
        テストケース: 個別条件での処理を検証する。
        期待結果: 想定どおりの処理結果が得られる。"""
        from roadmap.infrastructure.sql_roadmap_retrieval_reader import (
            SqlRoadmapRetrievalReader,
        )

        store = SqlRoadmapRetrievalReader(engine)
        result = store.find_roadmap(roadmap_with_items.id)  # type: ignore[union-attr]

        assert result is not None
        assert result.topic == "React"
        assert len(result.items) == 2

    def test_find_roadmap_returns_none_for_missing(
        self, engine: Engine, db_session: Session,
    ) -> None:
        """テスト対象: SqlRoadmapRetrievalReader の処理。
        テストケース: 個別条件での処理を検証する。
        期待結果: 想定どおりの処理結果が得られる。"""
        from roadmap.infrastructure.sql_roadmap_retrieval_reader import (
            SqlRoadmapRetrievalReader,
        )

        store = SqlRoadmapRetrievalReader(engine)
        result = store.find_roadmap(uuid.uuid4())

        assert result is None

    def test_find_all_roadmaps_returns_list(
        self, engine: Engine, db_session: Session, roadmap_with_items: object,
    ) -> None:
        """テスト対象: SqlRoadmapRetrievalReader の処理。
        テストケース: 個別条件での処理を検証する。
        期待結果: 想定どおりの処理結果が得られる。"""
        from roadmap.infrastructure.sql_roadmap_retrieval_reader import (
            SqlRoadmapRetrievalReader,
        )

        store = SqlRoadmapRetrievalReader(engine)
        results = store.find_all_roadmaps()

        assert len(results) >= 1
        assert any(r.topic == "React" for r in results)

    def test_find_all_roadmaps_returns_empty_when_none(
        self, engine: Engine, db_session: Session,
    ) -> None:
        """テスト対象: SqlRoadmapRetrievalReader の処理。
        テストケース: 個別条件での処理を検証する。
        期待結果: 想定どおりの処理結果が得られる。"""
        from roadmap.infrastructure.sql_roadmap_retrieval_reader import (
            SqlRoadmapRetrievalReader,
        )

        store = SqlRoadmapRetrievalReader(engine)
        results = store.find_all_roadmaps()

        assert results == []


# ---------------------------------------------------------------------------
# SqlRoadmapItemCrudStore
# ---------------------------------------------------------------------------


class TestSqlRoadmapItemCrudStore:
    def test_find_roadmap_returns_record(
        self, engine: Engine, db_session: Session, roadmap_with_items: object,
    ) -> None:
        """テスト対象: SqlRoadmapItemCrudStore の処理。
        テストケース: 個別条件での処理を検証する。
        期待結果: 想定どおりの処理結果が得られる。"""
        from roadmap.infrastructure.sql_roadmap_item_crud_store import (
            SqlRoadmapItemCrudStore,
        )

        store = SqlRoadmapItemCrudStore(engine)
        result = store.find_roadmap(roadmap_with_items.id)  # type: ignore[union-attr]

        assert result is not None
        assert len(result.items) == 2

    def test_find_roadmap_returns_none_for_missing(
        self, engine: Engine, db_session: Session,
    ) -> None:
        """テスト対象: SqlRoadmapItemCrudStore の処理。
        テストケース: 個別条件での処理を検証する。
        期待結果: 想定どおりの処理結果が得られる。"""
        from roadmap.infrastructure.sql_roadmap_item_crud_store import (
            SqlRoadmapItemCrudStore,
        )

        store = SqlRoadmapItemCrudStore(engine)
        result = store.find_roadmap(uuid.uuid4())

        assert result is None

    def test_find_item_returns_record(
        self, engine: Engine, db_session: Session, roadmap_with_items: object,
    ) -> None:
        """テスト対象: SqlRoadmapItemCrudStore の処理。
        テストケース: 個別条件での処理を検証する。
        期待結果: 想定どおりの処理結果が得られる。"""
        from infrastructure.rdb.models import RoadmapItem
        from roadmap.infrastructure.sql_roadmap_item_crud_store import (
            SqlRoadmapItemCrudStore,
        )

        store = SqlRoadmapItemCrudStore(engine)
        with Session(engine) as s:
            first_item = s.query(RoadmapItem).filter_by(
                roadmap_id=roadmap_with_items.id,  # type: ignore[union-attr]
            ).first()

        result = store.find_item(first_item.id)  # type: ignore[union-attr]

        assert result is not None
        assert result.title in ("Hooks", "useState")

    def test_find_item_returns_none_for_missing(
        self, engine: Engine, db_session: Session,
    ) -> None:
        """テスト対象: SqlRoadmapItemCrudStore の処理。
        テストケース: 個別条件での処理を検証する。
        期待結果: 想定どおりの処理結果が得られる。"""
        from roadmap.infrastructure.sql_roadmap_item_crud_store import (
            SqlRoadmapItemCrudStore,
        )

        store = SqlRoadmapItemCrudStore(engine)
        result = store.find_item(uuid.uuid4())

        assert result is None

    def test_replace_items_replaces_all(
        self, engine: Engine, db_session: Session, roadmap_with_items: object,
    ) -> None:
        """テスト対象: SqlRoadmapItemCrudStore の処理。
        テストケース: 個別条件での処理を検証する。
        期待結果: 想定どおりの処理結果が得られる。"""
        from infrastructure.rdb.models import RoadmapItem
        from roadmap.domain.roadmap_item_crud_types import RoadmapItemCrudItem
        from roadmap.infrastructure.sql_roadmap_item_crud_store import (
            SqlRoadmapItemCrudStore,
        )

        store = SqlRoadmapItemCrudStore(engine)
        roadmap_id = roadmap_with_items.id  # type: ignore[union-attr]

        new_items = [
            RoadmapItemCrudItem(
                id=uuid.uuid4(), roadmap_id=roadmap_id, parent_id=None,
                level="major", title="新しい大枠", description="新しい説明",
                order=1, score=0,
            ),
        ]
        store.replace_items(roadmap_id, new_items)

        with Session(engine) as s:
            rows = s.query(RoadmapItem).filter_by(roadmap_id=roadmap_id).all()
            assert len(rows) == 1
            assert rows[0].title == "新しい大枠"


# ---------------------------------------------------------------------------
# InMemoryJobStatusStore
# ---------------------------------------------------------------------------


class TestInMemoryJobStatusStore:
    def test_create_and_get_queued_job(self) -> None:
        """テスト対象: InMemoryJobStatusStore の処理。
        テストケース: 個別条件での処理を検証する。
        期待結果: 想定どおりの処理結果が得られる。"""
        from roadmap.infrastructure.in_memory_job_status_store import (
            InMemoryJobStatusStore,
        )

        store = InMemoryJobStatusStore()
        job_id = uuid.uuid4()
        store.create_queued_job(job_id, "TypeScript")
        result = store.get_job(job_id)

        assert result["status"] == "queued"

    def test_mark_running(self) -> None:
        """テスト対象: InMemoryJobStatusStore の処理。
        テストケース: 個別条件での処理を検証する。
        期待結果: 想定どおりの処理結果が得られる。"""
        from roadmap.infrastructure.in_memory_job_status_store import (
            InMemoryJobStatusStore,
        )

        store = InMemoryJobStatusStore()
        job_id = uuid.uuid4()
        store.create_queued_job(job_id, "React")
        store.mark_running(job_id)
        result = store.get_job(job_id)

        assert result["status"] == "running"

    def test_mark_completed(self) -> None:
        """テスト対象: InMemoryJobStatusStore の処理。
        テストケース: 個別条件での処理を検証する。
        期待結果: 想定どおりの処理結果が得られる。"""
        from roadmap.infrastructure.in_memory_job_status_store import (
            InMemoryJobStatusStore,
        )

        store = InMemoryJobStatusStore()
        job_id = uuid.uuid4()
        roadmap_id = uuid.uuid4()
        store.create_queued_job(job_id, "Vue")
        store.mark_running(job_id)
        store.mark_completed(job_id, roadmap_id)
        result = store.get_job(job_id)

        assert result["status"] == "completed"
        assert result["roadmap_id"] == roadmap_id  # type: ignore[typeddict-item]

    def test_mark_failed(self) -> None:
        """テスト対象: InMemoryJobStatusStore の処理。
        テストケース: 個別条件での処理を検証する。
        期待結果: 想定どおりの処理結果が得られる。"""
        from roadmap.infrastructure.in_memory_job_status_store import (
            InMemoryJobStatusStore,
        )

        store = InMemoryJobStatusStore()
        job_id = uuid.uuid4()
        store.create_queued_job(job_id, "Go")
        store.mark_running(job_id)
        store.mark_failed(job_id, "llm_request_failed", "LLM timeout")
        result = store.get_job(job_id)

        assert result["status"] == "failed"
        assert result["error_code"] == "llm_request_failed"  # type: ignore[typeddict-item]

    def test_get_job_raises_for_missing(self) -> None:
        """テスト対象: get_job 関数。
        テストケース: 個別条件での処理を検証する。
        期待結果: 想定どおりの処理結果が得られる。"""
        from roadmap.domain.roadmap_generation_types import (
            RoadmapGenerationJobNotFoundError,
        )
        from roadmap.infrastructure.in_memory_job_status_store import (
            InMemoryJobStatusStore,
        )

        store = InMemoryJobStatusStore()
        with pytest.raises(RoadmapGenerationJobNotFoundError):
            store.get_job(uuid.uuid4())


# ---------------------------------------------------------------------------
# UuidGenerator
# ---------------------------------------------------------------------------


class TestUuidGenerator:
    def test_generates_valid_uuid(self) -> None:
        """テスト対象: UuidGenerator の処理。
        テストケース: 個別条件での処理を検証する。
        期待結果: 想定どおりの処理結果が得られる。"""
        from infrastructure.uuid_generator import UuidGenerator

        gen = UuidGenerator()
        result = gen.generate()

        assert isinstance(result, uuid.UUID)

    def test_generates_unique_values(self) -> None:
        """テスト対象: UuidGenerator の処理。
        テストケース: 個別条件での処理を検証する。
        期待結果: 想定どおりの処理結果が得られる。"""
        from infrastructure.uuid_generator import UuidGenerator

        gen = UuidGenerator()
        results = {gen.generate() for _ in range(100)}

        assert len(results) == 100
