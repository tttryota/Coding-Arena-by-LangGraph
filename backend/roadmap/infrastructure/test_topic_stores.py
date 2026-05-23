"""Topic Store 群のテスト。SqlTopicStore, ChromaNoteTopicReader, PresetTopicFileReader。"""

from __future__ import annotations

import json

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


# ---------------------------------------------------------------------------
# SqlTopicStore
# ---------------------------------------------------------------------------


class TestSqlTopicStore:
    def test_create_and_list_manual_topics(
        self, engine: Engine, db_session: Session,
    ) -> None:
        from roadmap.infrastructure.sql_topic_store import SqlTopicStore

        store = SqlTopicStore(engine)
        store.create_manual_topic("TypeScript", "typescript")
        store.create_manual_topic("React", "react")

        results = store.list_manual_topics()

        assert len(results) == 2
        assert results[0].name == "TypeScript"
        assert results[0].source == "manual"
        assert results[1].name == "React"
        assert results[1].source == "manual"

    def test_find_topic_by_canonical_name(
        self, engine: Engine, db_session: Session,
    ) -> None:
        from roadmap.infrastructure.sql_topic_store import SqlTopicStore

        store = SqlTopicStore(engine)
        store.create_manual_topic("Go", "go")

        result = store.find_topic_by_canonical_name("go")

        assert result is not None
        assert result.name == "Go"

    def test_find_topic_returns_none_for_missing(
        self, engine: Engine, db_session: Session,
    ) -> None:
        from roadmap.infrastructure.sql_topic_store import SqlTopicStore

        store = SqlTopicStore(engine)

        assert store.find_topic_by_canonical_name("nonexistent") is None

    def test_create_returns_record(
        self, engine: Engine, db_session: Session,
    ) -> None:
        from roadmap.infrastructure.sql_topic_store import SqlTopicStore

        store = SqlTopicStore(engine)
        result = store.create_manual_topic("Python", "python")

        assert result.name == "Python"
        assert result.canonical_name == "python"
        assert result.source == "manual"


# ---------------------------------------------------------------------------
# ChromaNoteTopicReader
# ---------------------------------------------------------------------------


class FakeMetadataCollection:
    def __init__(self, metadatas: list[dict]) -> None:
        self._metadatas = metadatas
        self.last_include: list[str] = []

    def get(self, include: list[str]) -> dict:
        self.last_include = include
        return {"metadatas": self._metadatas}


class TestChromaNoteTopicReader:
    def test_list_note_topics(self) -> None:
        from roadmap.infrastructure.chroma_note_topic_reader import (
            ChromaNoteTopicReader,
        )

        collection = FakeMetadataCollection([
            {"tags": ["TypeScript", "React"]},
            {"tags": ["TypeScript"]},
        ])
        reader = ChromaNoteTopicReader(collection)

        result = reader.list_note_topics()

        assert len(result) == 2
        by_canonical = {r.canonical_name: r.name for r in result}
        assert "typescript" in by_canonical
        assert "react" in by_canonical
        assert by_canonical["typescript"] == "TypeScript"
        assert by_canonical["react"] == "React"
        assert collection.last_include == ["metadatas"]

    def test_list_note_topics_empty(self) -> None:
        from roadmap.infrastructure.chroma_note_topic_reader import (
            ChromaNoteTopicReader,
        )

        collection = FakeMetadataCollection([])
        reader = ChromaNoteTopicReader(collection)

        assert reader.list_note_topics() == []

    def test_list_note_counts(self) -> None:
        from roadmap.infrastructure.chroma_note_topic_reader import (
            ChromaNoteTopicReader,
        )

        collection = FakeMetadataCollection([
            {"tags": ["TypeScript", "React"], "source_path": "note1.md"},
            {"tags": ["TypeScript"], "source_path": "note1.md"},
            {"tags": ["TypeScript"], "source_path": "note2.md"},
            {"tags": ["React"], "source_path": "note3.md"},
        ])
        reader = ChromaNoteTopicReader(collection)

        result = reader.list_note_counts(["typescript", "react"])

        counts = {r.canonical_name: r.note_count for r in result}
        assert counts["typescript"] == 2
        assert counts["react"] == 2

    def test_list_note_counts_zero_for_unknown(self) -> None:
        from roadmap.infrastructure.chroma_note_topic_reader import (
            ChromaNoteTopicReader,
        )

        collection = FakeMetadataCollection([])
        reader = ChromaNoteTopicReader(collection)

        result = reader.list_note_counts(["unknown"])

        assert result[0].canonical_name == "unknown"
        assert result[0].note_count == 0


# ---------------------------------------------------------------------------
# PresetTopicFileReader
# ---------------------------------------------------------------------------


class TestPresetTopicFileReader:
    def test_reads_preset_file(self, tmp_path: object) -> None:
        from pathlib import Path

        from roadmap.infrastructure.preset_topic_file_reader import (
            PresetTopicFileReader,
        )

        preset_file = Path(str(tmp_path)) / "presets.json"
        preset_file.write_text(
            json.dumps([
                {"name": "TypeScript", "canonical_name": "typescript"},
                {"name": "React", "canonical_name": "react"},
            ]),
            encoding="utf-8",
        )

        reader = PresetTopicFileReader(preset_file)
        result = reader.list_preset_topics()

        assert len(result) == 2
        assert result[0].name == "TypeScript"
        assert result[0].canonical_name == "typescript"
        assert result[1].name == "React"
        assert result[1].canonical_name == "react"

    def test_returns_empty_for_missing_file(self, tmp_path: object) -> None:
        from pathlib import Path

        from roadmap.infrastructure.preset_topic_file_reader import (
            PresetTopicFileReader,
        )

        reader = PresetTopicFileReader(Path(str(tmp_path)) / "nonexistent.json")

        assert reader.list_preset_topics() == []
