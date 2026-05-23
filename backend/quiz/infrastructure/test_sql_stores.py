"""Quiz RDB Store concrete implementations のテスト。

5 つの Store クラスの Protocol 準拠と CRUD 動作を検証する。
テストは in-memory SQLite で実行し、外部依存なし。
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
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
def roadmap(db_session: Session) -> object:
    from infrastructure.rdb.models import Roadmap

    r = Roadmap(id=uuid.uuid4(), topic="TypeScript", created_at=datetime.now(tz=UTC))
    db_session.add(r)
    db_session.commit()
    return r


@pytest.fixture
def roadmap_item(db_session: Session, roadmap: object) -> object:
    from infrastructure.rdb.models import RoadmapItem

    now = datetime.now(tz=UTC)
    item = RoadmapItem(
        id=uuid.uuid4(),
        roadmap_id=roadmap.id,  # type: ignore[union-attr]
        level="detail",
        title="ジェネリクス",
        description="ジェネリクスの基礎を理解する",
        order=1,
        score=0,
        created_at=now,
        updated_at=now,
    )
    db_session.add(item)
    db_session.commit()
    return item


@pytest.fixture
def quiz_session(db_session: Session, roadmap_item: object) -> object:
    from infrastructure.rdb.models import QuizSession

    qs = QuizSession(
        id=uuid.uuid4(),
        roadmap_item_id=roadmap_item.id,  # type: ignore[union-attr]
        status="in_progress",
        started_at=datetime.now(tz=UTC),
    )
    db_session.add(qs)
    db_session.commit()
    return qs


# ---------------------------------------------------------------------------
# Test helpers
# ---------------------------------------------------------------------------


@dataclass
class FakeAnswerRecord:
    question_number: int
    question_text: str
    answer_text: str
    answer_type: str
    score: int
    feedback: str
    confirmation_point_id: str


def _make_quiz_session(
    db_session: Session,
    roadmap_item: object,
    *,
    status: str = "in_progress",
) -> object:
    from infrastructure.rdb.models import QuizSession

    qs = QuizSession(
        id=uuid.uuid4(),
        roadmap_item_id=roadmap_item.id,  # type: ignore[union-attr]
        status=status,
        started_at=datetime.now(tz=UTC),
        completed_at=datetime.now(tz=UTC) if status == "completed" else None,
    )
    db_session.add(qs)
    db_session.commit()
    return qs


# ---------------------------------------------------------------------------
# SqlQuizSessionStore
# ---------------------------------------------------------------------------


class TestSqlQuizSessionStore:
    def test_create_session_returns_record_with_id(
        self, engine: Engine, db_session: Session, roadmap_item: object,
    ) -> None:
        from quiz.infrastructure.sql_quiz_session_store import SqlQuizSessionStore

        store = SqlQuizSessionStore(engine)
        result = store.create_session(str(roadmap_item.id))  # type: ignore[union-attr]

        assert result.id is not None
        assert result.roadmap_item_id == str(roadmap_item.id)  # type: ignore[union-attr]

    def test_create_session_persists_row(
        self, engine: Engine, db_session: Session, roadmap_item: object,
    ) -> None:
        from infrastructure.rdb.models import QuizSession
        from quiz.infrastructure.sql_quiz_session_store import SqlQuizSessionStore

        store = SqlQuizSessionStore(engine)
        result = store.create_session(str(roadmap_item.id))  # type: ignore[union-attr]

        with Session(engine) as s:
            row = s.get(QuizSession, uuid.UUID(result.id))
            assert row is not None
            assert row.status == "in_progress"

    def test_find_in_progress_by_item_returns_session(
        self, engine: Engine, db_session: Session, roadmap_item: object, quiz_session: object,
    ) -> None:
        from quiz.infrastructure.sql_quiz_session_store import SqlQuizSessionStore

        store = SqlQuizSessionStore(engine)
        result = store.find_in_progress_by_item(str(roadmap_item.id))  # type: ignore[union-attr]

        assert result is not None
        assert result.id == str(quiz_session.id)  # type: ignore[union-attr]

    def test_find_in_progress_by_item_returns_none_when_no_match(
        self, engine: Engine, db_session: Session,
    ) -> None:
        from quiz.infrastructure.sql_quiz_session_store import SqlQuizSessionStore

        store = SqlQuizSessionStore(engine)
        result = store.find_in_progress_by_item(str(uuid.uuid4()))

        assert result is None

    def test_find_session_returns_record(
        self, engine: Engine, db_session: Session, quiz_session: object,
    ) -> None:
        from quiz.infrastructure.sql_quiz_session_store import SqlQuizSessionStore

        store = SqlQuizSessionStore(engine)
        result = store.find_session(str(quiz_session.id))  # type: ignore[union-attr]

        assert result.id == str(quiz_session.id)  # type: ignore[union-attr]

    def test_complete_session_updates_status(
        self, engine: Engine, db_session: Session, roadmap_item: object, quiz_session: object,
    ) -> None:
        from infrastructure.rdb.models import QuizSession as QS
        from quiz.infrastructure.sql_quiz_session_store import SqlQuizSessionStore

        store = SqlQuizSessionStore(engine)
        completed_at = datetime.now(tz=UTC).isoformat()
        store.complete_session(
            str(quiz_session.id), str(roadmap_item.id), 85, completed_at,  # type: ignore[union-attr]
        )

        with Session(engine) as s:
            row = s.get(QS, quiz_session.id)  # type: ignore[union-attr]
            assert row is not None
            assert row.status == "completed"
            assert row.completed_at is not None

    def test_discard_session_sets_status_discarded(
        self, engine: Engine, db_session: Session, quiz_session: object,
    ) -> None:
        from infrastructure.rdb.models import QuizSession as QS
        from quiz.infrastructure.sql_quiz_session_store import SqlQuizSessionStore

        store = SqlQuizSessionStore(engine)
        store.discard_session(str(quiz_session.id))  # type: ignore[union-attr]

        with Session(engine) as s:
            row = s.get(QS, quiz_session.id)  # type: ignore[union-attr]
            assert row is not None
            assert row.status == "discarded"


# ---------------------------------------------------------------------------
# SqlQuizAnswerStore
# ---------------------------------------------------------------------------


class TestSqlQuizAnswerStore:
    def test_save_answer_persists_row(
        self, engine: Engine, db_session: Session, quiz_session: object, roadmap_item: object,
    ) -> None:
        from infrastructure.rdb.models import QuizAnswer
        from quiz.infrastructure.sql_quiz_answer_store import SqlQuizAnswerStore

        store = SqlQuizAnswerStore(engine)
        answer = FakeAnswerRecord(
            question_number=1,
            question_text="ジェネリクスとは?",
            answer_text="型パラメータで定義する仕組み",
            answer_type="textarea",
            score=80,
            feedback="正確です",
            confirmation_point_id="cp-001",
        )
        store.save_answer(str(quiz_session.id), answer)  # type: ignore[union-attr]

        with Session(engine) as s:
            rows = s.query(QuizAnswer).filter_by(session_id=quiz_session.id).all()  # type: ignore[union-attr]
            assert len(rows) == 1
            assert rows[0].question_text == "ジェネリクスとは?"
            assert rows[0].confirmation_point_id == "cp-001"

    def test_find_by_session_returns_ordered_answers(
        self, engine: Engine, db_session: Session, quiz_session: object, roadmap_item: object,
    ) -> None:
        from quiz.infrastructure.sql_quiz_answer_store import SqlQuizAnswerStore

        store = SqlQuizAnswerStore(engine)
        for i in range(3):
            store.save_answer(
                str(quiz_session.id),  # type: ignore[union-attr]
                FakeAnswerRecord(
                    question_number=i + 1,
                    question_text=f"問題{i + 1}",
                    answer_text=f"回答{i + 1}",
                    answer_type="textarea",
                    score=70 + i * 10,
                    feedback=f"FB{i + 1}",
                    confirmation_point_id=f"cp-{i + 1:03d}",
                ),
            )

        results = store.find_by_session(str(quiz_session.id))  # type: ignore[union-attr]

        assert len(results) == 3
        assert results[0].question_number == 1
        assert results[2].question_number == 3
        assert results[0].confirmation_point_id == "cp-001"

    def test_find_by_session_returns_empty_for_no_answers(
        self, engine: Engine, db_session: Session, quiz_session: object,
    ) -> None:
        from quiz.infrastructure.sql_quiz_answer_store import SqlQuizAnswerStore

        store = SqlQuizAnswerStore(engine)
        results = store.find_by_session(str(quiz_session.id))  # type: ignore[union-attr]

        assert results == []


# ---------------------------------------------------------------------------
# SqlRoadmapItemReadStore
# ---------------------------------------------------------------------------


class TestSqlRoadmapItemReadStore:
    def test_find_item_returns_record(
        self, engine: Engine, db_session: Session, roadmap_item: object,
    ) -> None:
        from quiz.infrastructure.sql_roadmap_item_read_store import (
            SqlRoadmapItemReadStore,
        )

        store = SqlRoadmapItemReadStore(engine)
        result = store.find_item(str(roadmap_item.id))  # type: ignore[union-attr]

        assert result is not None
        assert result.id == str(roadmap_item.id)  # type: ignore[union-attr]
        assert result.level == "detail"
        assert result.title == "ジェネリクス"
        assert result.description == "ジェネリクスの基礎を理解する"

    def test_find_item_returns_none_for_missing(
        self, engine: Engine, db_session: Session,
    ) -> None:
        from quiz.infrastructure.sql_roadmap_item_read_store import (
            SqlRoadmapItemReadStore,
        )

        store = SqlRoadmapItemReadStore(engine)
        result = store.find_item(str(uuid.uuid4()))

        assert result is None

    def test_item_exists_returns_true(
        self, engine: Engine, db_session: Session, roadmap_item: object,
    ) -> None:
        from quiz.infrastructure.sql_roadmap_item_read_store import (
            SqlRoadmapItemReadStore,
        )

        store = SqlRoadmapItemReadStore(engine)

        assert store.item_exists(str(roadmap_item.id)) is True  # type: ignore[union-attr]

    def test_item_exists_returns_false(
        self, engine: Engine, db_session: Session,
    ) -> None:
        from quiz.infrastructure.sql_roadmap_item_read_store import (
            SqlRoadmapItemReadStore,
        )

        store = SqlRoadmapItemReadStore(engine)

        assert store.item_exists(str(uuid.uuid4())) is False


# ---------------------------------------------------------------------------
# SqlProgressUpdateStore
# ---------------------------------------------------------------------------


class TestSqlProgressUpdateStore:
    def test_update_roadmap_item_progress(
        self, engine: Engine, db_session: Session, roadmap_item: object,
    ) -> None:
        from infrastructure.rdb.models import RoadmapItem
        from quiz.infrastructure.sql_progress_update_store import SqlProgressUpdateStore

        store = SqlProgressUpdateStore(engine)
        now = datetime.now(tz=UTC)
        store.update_roadmap_item_progress(str(roadmap_item.id), 85, now)  # type: ignore[union-attr]

        with Session(engine) as s:
            row = s.get(RoadmapItem, roadmap_item.id)  # type: ignore[union-attr]
            assert row is not None
            assert row.score == 85
            assert row.last_quiz_at is not None

    def test_save_summary_test_result(
        self, engine: Engine, db_session: Session, quiz_session: object, roadmap_item: object,
    ) -> None:
        from infrastructure.rdb.models import SummaryTestResult
        from quiz.infrastructure.sql_progress_update_store import SqlProgressUpdateStore

        store = SqlProgressUpdateStore(engine)
        store.save_summary_test_result(
            str(quiz_session.id), str(roadmap_item.id), 75, "型ガードの理解が弱い",  # type: ignore[union-attr]
        )

        with Session(engine) as s:
            rows = s.query(SummaryTestResult).filter_by(session_id=quiz_session.id).all()  # type: ignore[union-attr]
            assert len(rows) == 1
            assert rows[0].score == 75

    def test_complete_session(
        self, engine: Engine, db_session: Session, quiz_session: object,
    ) -> None:
        from infrastructure.rdb.models import QuizSession as QS
        from quiz.infrastructure.sql_progress_update_store import SqlProgressUpdateStore

        store = SqlProgressUpdateStore(engine)
        store.complete_session(str(quiz_session.id))  # type: ignore[union-attr]

        with Session(engine) as s:
            row = s.get(QS, quiz_session.id)  # type: ignore[union-attr]
            assert row is not None
            assert row.status == "completed"
            assert row.completed_at is not None


# ---------------------------------------------------------------------------
# SqlSummaryTestResultStore
# ---------------------------------------------------------------------------


class TestSqlSummaryTestResultStore:
    def test_save_result(
        self, engine: Engine, db_session: Session, quiz_session: object, roadmap_item: object,
    ) -> None:
        from infrastructure.rdb.models import SummaryTestResult
        from quiz.infrastructure.sql_summary_test_result_store import (
            SqlSummaryTestResultStore,
        )

        store = SqlSummaryTestResultStore(engine)
        store.save_result(
            str(quiz_session.id), str(roadmap_item.id), 70, "全体的に理解は良好",  # type: ignore[union-attr]
        )

        with Session(engine) as s:
            rows = s.query(SummaryTestResult).filter_by(session_id=quiz_session.id).all()  # type: ignore[union-attr]
            assert len(rows) == 1
            assert rows[0].analysis == "全体的に理解は良好"

    def test_find_by_roadmap_item_returns_records(
        self, engine: Engine, db_session: Session, roadmap: object, roadmap_item: object,
    ) -> None:
        from quiz.infrastructure.sql_summary_test_result_store import (
            SqlSummaryTestResultStore,
        )

        store = SqlSummaryTestResultStore(engine)

        qs1 = _make_quiz_session(db_session, roadmap_item, status="completed")
        qs2 = _make_quiz_session(db_session, roadmap_item, status="completed")
        store.save_result(str(qs1.id), str(roadmap_item.id), 70, "分析1")  # type: ignore[union-attr]
        store.save_result(str(qs2.id), str(roadmap_item.id), 85, "分析2")  # type: ignore[union-attr]

        results = store.find_by_roadmap_item(str(roadmap_item.id))  # type: ignore[union-attr]

        assert len(results) == 2
        assert all(r.session_id is not None for r in results)

    def test_find_by_roadmap_item_returns_empty_for_no_match(
        self, engine: Engine, db_session: Session,
    ) -> None:
        from quiz.infrastructure.sql_summary_test_result_store import (
            SqlSummaryTestResultStore,
        )

        store = SqlSummaryTestResultStore(engine)
        results = store.find_by_roadmap_item(str(uuid.uuid4()))

        assert results == []


# ---------------------------------------------------------------------------
# Error path tests
# ---------------------------------------------------------------------------


class TestStoreErrorPaths:
    def test_find_session_raises_for_missing_id(self, engine: Engine, db_session: Session) -> None:
        from quiz.infrastructure.sql_quiz_session_store import SqlQuizSessionStore

        store = SqlQuizSessionStore(engine)
        with pytest.raises(ValueError, match="not found"):
            store.find_session(str(uuid.uuid4()))

    def test_complete_session_raises_for_missing_id(self, engine: Engine, db_session: Session) -> None:
        from quiz.infrastructure.sql_quiz_session_store import SqlQuizSessionStore

        store = SqlQuizSessionStore(engine)
        with pytest.raises(ValueError, match="not found"):
            store.complete_session(str(uuid.uuid4()), str(uuid.uuid4()), 0, "2026-01-01T00:00:00")

    def test_discard_session_raises_for_missing_id(self, engine: Engine, db_session: Session) -> None:
        from quiz.infrastructure.sql_quiz_session_store import SqlQuizSessionStore

        store = SqlQuizSessionStore(engine)
        with pytest.raises(ValueError, match="not found"):
            store.discard_session(str(uuid.uuid4()))

    def test_save_answer_raises_for_missing_session(self, engine: Engine, db_session: Session) -> None:
        from quiz.infrastructure.sql_quiz_answer_store import SqlQuizAnswerStore

        store = SqlQuizAnswerStore(engine)
        answer = FakeAnswerRecord(
            question_number=1, question_text="Q", answer_text="A",
            answer_type="textarea", score=50, feedback="FB",
            confirmation_point_id="cp-001",
        )
        with pytest.raises(ValueError, match="not found"):
            store.save_answer(str(uuid.uuid4()), answer)

    def test_update_roadmap_item_progress_raises_for_missing_item(
        self, engine: Engine, db_session: Session,
    ) -> None:
        from quiz.infrastructure.sql_progress_update_store import SqlProgressUpdateStore

        store = SqlProgressUpdateStore(engine)
        with pytest.raises(ValueError, match="not found"):
            store.update_roadmap_item_progress(str(uuid.uuid4()), 80, datetime.now(tz=UTC))
