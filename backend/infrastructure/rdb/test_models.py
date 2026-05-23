import uuid
from datetime import UTC, datetime

from sqlalchemy import Engine, create_engine, inspect
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from infrastructure.rdb.base import Base
from infrastructure.rdb.models import (
    DiffSnapshot,
    IngestionFeedback,
    QuizAnswer,
    QuizSession,
    Roadmap,
    RoadmapItem,
    SummaryTestResult,
    Topic,
)

EXPECTED_TABLES = {
    "roadmaps",
    "roadmap_items",
    "quiz_sessions",
    "quiz_answers",
    "ingestion_feedbacks",
    "summary_test_results",
    "topics",
    "diff_snapshots",
}


def _create_in_memory_engine() -> Engine:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    return engine


class TestTableCreation:
    def test_all_tables_created(self) -> None:
        engine = _create_in_memory_engine()
        inspector = inspect(engine)
        tables = set(inspector.get_table_names())
        assert tables == EXPECTED_TABLES


class TestRoadmap:
    def test_insert_and_read(self) -> None:
        engine = _create_in_memory_engine()
        now = datetime.now(tz=UTC)
        roadmap = Roadmap(
            id=uuid.uuid4(),
            topic="TypeScript",
            created_at=now,
        )
        with Session(engine) as session:
            session.add(roadmap)
            session.commit()
            result = session.get(Roadmap, roadmap.id)

        assert result is not None
        assert result.topic == "TypeScript"

    def test_roadmap_has_items_relationship(self) -> None:
        engine = _create_in_memory_engine()
        now = datetime.now(tz=UTC)
        roadmap = Roadmap(id=uuid.uuid4(), topic="React", created_at=now)
        item = RoadmapItem(
            id=uuid.uuid4(),
            roadmap_id=roadmap.id,
            level="major",
            title="Hooks",
            description="React Hooks",
            order=1,
            score=0,
            created_at=now,
            updated_at=now,
        )
        with Session(engine) as session:
            session.add_all([roadmap, item])
            session.commit()
            loaded = session.get(Roadmap, roadmap.id)
            assert loaded is not None
            assert len(loaded.items) == 1
            assert loaded.items[0].title == "Hooks"


class TestRoadmapItem:
    def test_insert_and_read(self) -> None:
        engine = _create_in_memory_engine()
        now = datetime.now(tz=UTC)
        roadmap = Roadmap(id=uuid.uuid4(), topic="TS", created_at=now)
        item = RoadmapItem(
            id=uuid.uuid4(),
            roadmap_id=roadmap.id,
            parent_id=None,
            level="major",
            title="TypeScript",
            description="TypeScriptの基礎",
            order=1,
            score=0,
            last_quiz_at=None,
            created_at=now,
            updated_at=now,
        )
        with Session(engine) as session:
            session.add_all([roadmap, item])
            session.commit()
            result = session.get(RoadmapItem, item.id)

        assert result is not None
        assert result.title == "TypeScript"
        assert result.level == "major"

    def test_self_referential_parent_child(self) -> None:
        engine = _create_in_memory_engine()
        now = datetime.now(tz=UTC)
        roadmap = Roadmap(id=uuid.uuid4(), topic="TS", created_at=now)
        parent = RoadmapItem(
            id=uuid.uuid4(),
            roadmap_id=roadmap.id,
            parent_id=None,
            level="major",
            title="Parent",
            description="Parent item",
            order=1,
            score=0,
            created_at=now,
            updated_at=now,
        )
        child = RoadmapItem(
            id=uuid.uuid4(),
            roadmap_id=roadmap.id,
            parent_id=parent.id,
            level="middle",
            title="Child",
            description="Child item",
            order=1,
            score=0,
            created_at=now,
            updated_at=now,
        )
        with Session(engine) as session:
            session.add_all([roadmap, parent, child])
            session.commit()
            loaded = session.get(RoadmapItem, parent.id)
            assert loaded is not None
            assert len(loaded.children) == 1
            assert loaded.children[0].title == "Child"


class TestQuizSession:
    def test_insert_with_roadmap_item(self) -> None:
        engine = _create_in_memory_engine()
        now = datetime.now(tz=UTC)
        roadmap = Roadmap(id=uuid.uuid4(), topic="TS", created_at=now)
        item = RoadmapItem(
            id=uuid.uuid4(),
            roadmap_id=roadmap.id,
            level="detail",
            title="ジェネリクス",
            description="ジェネリクスの基本",
            order=1,
            score=0,
            created_at=now,
            updated_at=now,
        )
        quiz_session = QuizSession(
            id=uuid.uuid4(),
            roadmap_item_id=item.id,
            status="in_progress",
            started_at=now,
            completed_at=None,
        )
        with Session(engine) as session:
            session.add_all([roadmap, item, quiz_session])
            session.commit()
            result = session.get(QuizSession, quiz_session.id)
            assert result is not None
            assert result.status == "in_progress"
            assert result.roadmap_item.title == "ジェネリクス"


class TestQuizAnswer:
    def test_insert_and_read(self) -> None:
        engine = _create_in_memory_engine()
        now = datetime.now(tz=UTC)
        roadmap = Roadmap(id=uuid.uuid4(), topic="TS", created_at=now)
        item = RoadmapItem(
            id=uuid.uuid4(),
            roadmap_id=roadmap.id,
            level="detail",
            title="型ガード",
            description="型ガードの使い方",
            order=1,
            score=0,
            created_at=now,
            updated_at=now,
        )
        quiz_session = QuizSession(
            id=uuid.uuid4(),
            roadmap_item_id=item.id,
            status="in_progress",
            started_at=now,
        )
        answer = QuizAnswer(
            id=uuid.uuid4(),
            session_id=quiz_session.id,
            roadmap_item_id=item.id,
            confirmation_point_id="cp-001",
            question_number=1,
            question_text="型ガードとは何ですか?",
            answer_type="textarea",
            answer_text="型を絞り込むための条件分岐です",
            score=75,
            feedback="概ね正しいですが、具体例があるとより良いです",
            answered_at=now,
        )
        with Session(engine) as session:
            session.add_all([roadmap, item, quiz_session, answer])
            session.commit()
            result = session.get(QuizAnswer, answer.id)

        assert result is not None
        assert result.score == 75
        assert result.answer_type == "textarea"
        assert result.confirmation_point_id == "cp-001"


class TestIngestionFeedback:
    def test_insert_without_roadmap_item(self) -> None:
        engine = _create_in_memory_engine()
        now = datetime.now(tz=UTC)
        feedback = IngestionFeedback(
            id=uuid.uuid4(),
            source_path="study/ts/generics.md",
            roadmap_item_id=None,
            title="内容の正確性",
            body="ジェネリクスの説明が正確です",
            is_read=False,
            created_at=now,
            read_at=None,
        )
        with Session(engine) as session:
            session.add(feedback)
            session.commit()
            result = session.get(IngestionFeedback, feedback.id)

        assert result is not None
        assert result.source_path == "study/ts/generics.md"
        assert result.is_read is False


class TestSummaryTestResult:
    def test_insert_and_read(self) -> None:
        engine = _create_in_memory_engine()
        now = datetime.now(tz=UTC)
        roadmap = Roadmap(id=uuid.uuid4(), topic="TS", created_at=now)
        item = RoadmapItem(
            id=uuid.uuid4(),
            roadmap_id=roadmap.id,
            level="middle",
            title="型システム",
            description="TypeScriptの型システム",
            order=1,
            score=0,
            created_at=now,
            updated_at=now,
        )
        quiz_session = QuizSession(
            id=uuid.uuid4(),
            roadmap_item_id=item.id,
            status="completed",
            started_at=now,
            completed_at=now,
        )
        summary = SummaryTestResult(
            id=uuid.uuid4(),
            session_id=quiz_session.id,
            score=68,
            analysis="型ガードの使い分けが弱い傾向があります",
            created_at=now,
        )
        with Session(engine) as session:
            session.add_all([roadmap, item, quiz_session, summary])
            session.commit()
            result = session.get(SummaryTestResult, summary.id)

        assert result is not None
        assert result.score == 68
        assert "型ガード" in result.analysis


class TestTopic:
    def test_insert_and_read(self) -> None:
        engine = _create_in_memory_engine()
        now = datetime.now(tz=UTC)
        topic = Topic(
            id=uuid.uuid4(),
            name="TypeScript",
            canonical_name="typescript",
            source="manual",
            created_at=now,
        )
        with Session(engine) as session:
            session.add(topic)
            session.commit()
            result = session.get(Topic, topic.id)

        assert result is not None
        assert result.name == "TypeScript"
        assert result.canonical_name == "typescript"
        assert result.source == "manual"

    def test_canonical_name_is_unique(self) -> None:
        engine = _create_in_memory_engine()
        now = datetime.now(tz=UTC)
        t1 = Topic(
            id=uuid.uuid4(),
            name="TypeScript",
            canonical_name="typescript",
            source="manual",
            created_at=now,
        )
        t2 = Topic(
            id=uuid.uuid4(),
            name="TS",
            canonical_name="typescript",
            source="preset",
            created_at=now,
        )
        with Session(engine) as session:
            session.add(t1)
            session.commit()
            session.add(t2)
            try:
                session.commit()
                raised = False
            except IntegrityError:
                raised = True
        assert raised


class TestDiffSnapshot:
    def test_insert_and_read(self) -> None:
        engine = _create_in_memory_engine()
        now = datetime.now(tz=UTC)
        snapshot = DiffSnapshot(
            snapshot_key="/path/to/vault",
            files_json='{"file1.md": 12345}',
            updated_at=now,
        )
        with Session(engine) as session:
            session.add(snapshot)
            session.commit()
            result = session.get(DiffSnapshot, "/path/to/vault")

        assert result is not None
        assert result.files_json == '{"file1.md": 12345}'
