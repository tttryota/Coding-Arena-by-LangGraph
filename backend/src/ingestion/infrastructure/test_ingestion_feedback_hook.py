"""IngestionFeedbackHook + RoadmapItemReaderAdapter の単体テスト。"""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID, uuid4

import pytest

from ingestion.infrastructure.ingestion_feedback_hook import (
    IngestionFeedbackHook,
    RoadmapItemReaderAdapter,
)

# ---------------------------------------------------------------------------
# Stub helpers
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class _ItemRecord:
    id: UUID
    parent_id: UUID | None
    level: str
    title: str
    description: str
    order: int
    score: int
    last_quiz_at: str | None = None


@dataclass(frozen=True)
class _RoadmapRecord:
    roadmap_id: UUID
    topic: str
    items: list[_ItemRecord]


class _StubRetrievalReader:
    def __init__(self, roadmaps: list[_RoadmapRecord]) -> None:
        self._roadmaps = roadmaps

    def find_all_roadmaps(self) -> list[_RoadmapRecord]:
        return list(self._roadmaps)


class _RecordingLlmClient:
    """LLM スタブ。呼び出しを記録する。"""

    def __init__(self, *, raise_error: Exception | None = None) -> None:
        self.captured_requests: list[object] = []
        self._raise_error = raise_error

    def analyze(self, request: object) -> object:
        from ingestion.domain.ingestion_feedback_types import (
            IngestionFeedbackLlmResponse,
        )

        self.captured_requests.append(request)
        if self._raise_error is not None:
            raise self._raise_error
        return IngestionFeedbackLlmResponse(
            selected_roadmap_item_id=None,
            accuracy_check="ok",
            improvement_suggestions=["テスト提案"],
        )


class _StubWriter:
    def __init__(self) -> None:
        self.records: list[object] = []

    def create(self, record: object) -> object:
        from ingestion.domain.ingestion_feedback_types import StoredIngestionFeedback

        self.records.append(record)
        return StoredIngestionFeedback(
            id=uuid4(),
            source_path=record.source_path,  # type: ignore[union-attr]
            roadmap_item_id=None,
            title="test",
            body="test",
            is_read=False,
            created_at="2026-05-24T00:00:00+00:00",
            read_at=None,
        )


_LONG_TEXT = "This is a long enough chunk text for analysis purposes." * 3


# ---------------------------------------------------------------------------
# RoadmapItemReaderAdapter
# ---------------------------------------------------------------------------


class TestRoadmapItemReaderAdapterEmpty:
    def test_returns_empty_list_when_no_roadmaps(self) -> None:
        """テスト対象: RoadmapItemReaderAdapterEmpty の処理。
        テストケース: 個別条件での処理を検証する。
        期待結果: 想定どおりの処理結果が得られる。"""
        adapter = RoadmapItemReaderAdapter(_StubRetrievalReader(roadmaps=[]))

        result = adapter.list_items()

        assert result == []


class TestRoadmapItemReaderAdapterDisplayPath:
    def test_builds_display_path_for_flat_items(self) -> None:
        """テスト対象: RoadmapItemReaderAdapterDisplayPath の処理。
        テストケース: 個別条件での処理を検証する。
        期待結果: 想定どおりの処理結果が得られる。"""
        major_id = uuid4()
        roadmap = _RoadmapRecord(
            roadmap_id=uuid4(),
            topic="TypeScript",
            items=[
                _ItemRecord(
                    id=major_id, parent_id=None, level="major",
                    title="基礎", description="desc", order=0, score=0,
                ),
            ],
        )
        adapter = RoadmapItemReaderAdapter(_StubRetrievalReader([roadmap]))

        result = adapter.list_items()

        assert len(result) == 1
        assert result[0].id == major_id
        assert result[0].display_path == "TypeScript > 基礎"

    def test_builds_nested_display_path(self) -> None:
        """テスト対象: RoadmapItemReaderAdapterDisplayPath の処理。
        テストケース: 個別条件での処理を検証する。
        期待結果: 想定どおりの処理結果が得られる。"""
        major_id = uuid4()
        middle_id = uuid4()
        detail_id = uuid4()
        roadmap = _RoadmapRecord(
            roadmap_id=uuid4(),
            topic="TypeScript",
            items=[
                _ItemRecord(
                    id=major_id, parent_id=None, level="major",
                    title="基礎", description="", order=0, score=0,
                ),
                _ItemRecord(
                    id=middle_id, parent_id=major_id, level="middle",
                    title="型システム", description="", order=0, score=0,
                ),
                _ItemRecord(
                    id=detail_id, parent_id=middle_id, level="detail",
                    title="ジェネリクス", description="", order=0, score=0,
                ),
            ],
        )
        adapter = RoadmapItemReaderAdapter(_StubRetrievalReader([roadmap]))

        result = adapter.list_items()

        assert len(result) == 3
        major = next(c for c in result if c.id == major_id)
        middle = next(c for c in result if c.id == middle_id)
        detail = next(c for c in result if c.id == detail_id)
        assert major.display_path == "TypeScript > 基礎"
        assert middle.display_path == "TypeScript > 基礎 > 型システム"
        assert detail.display_path == "TypeScript > 基礎 > 型システム > ジェネリクス"

    def test_merges_items_from_multiple_roadmaps(self) -> None:
        """テスト対象: RoadmapItemReaderAdapterDisplayPath の処理。
        テストケース: 個別条件での処理を検証する。
        期待結果: 想定どおりの処理結果が得られる。"""
        r1 = _RoadmapRecord(
            roadmap_id=uuid4(), topic="TypeScript",
            items=[
                _ItemRecord(
                    id=uuid4(), parent_id=None, level="major",
                    title="基礎", description="", order=0, score=0,
                ),
            ],
        )
        r2 = _RoadmapRecord(
            roadmap_id=uuid4(), topic="React",
            items=[
                _ItemRecord(
                    id=uuid4(), parent_id=None, level="major",
                    title="Hooks", description="", order=0, score=0,
                ),
            ],
        )
        adapter = RoadmapItemReaderAdapter(_StubRetrievalReader([r1, r2]))

        result = adapter.list_items()

        assert len(result) == 2
        paths = {c.display_path for c in result}
        assert "TypeScript > 基礎" in paths
        assert "React > Hooks" in paths

    def test_orphan_parent_shows_placeholder(self) -> None:
        """テスト対象: RoadmapItemReaderAdapterDisplayPath の処理。
        テストケース: 個別条件での処理を検証する。
        期待結果: 想定どおりの処理結果が得られる。"""
        orphan_parent_id = uuid4()
        item_id = uuid4()
        roadmap = _RoadmapRecord(
            roadmap_id=uuid4(), topic="Test",
            items=[
                _ItemRecord(
                    id=item_id, parent_id=orphan_parent_id, level="detail",
                    title="Child", description="", order=0, score=0,
                ),
            ],
        )
        adapter = RoadmapItemReaderAdapter(_StubRetrievalReader([roadmap]))

        result = adapter.list_items()

        assert len(result) == 1
        assert "?" in result[0].display_path
        assert result[0].display_path == "Test > ? > Child"

    def test_cycle_does_not_loop_infinitely(self) -> None:
        """テスト対象: RoadmapItemReaderAdapterDisplayPath の処理。
        テストケース: 個別条件での処理を検証する。
        期待結果: 想定どおりの処理結果が得られる。"""
        id_a = uuid4()
        id_b = uuid4()
        roadmap = _RoadmapRecord(
            roadmap_id=uuid4(), topic="Test",
            items=[
                _ItemRecord(
                    id=id_a, parent_id=id_b, level="major",
                    title="A", description="", order=0, score=0,
                ),
                _ItemRecord(
                    id=id_b, parent_id=id_a, level="major",
                    title="B", description="", order=0, score=0,
                ),
            ],
        )
        adapter = RoadmapItemReaderAdapter(_StubRetrievalReader([roadmap]))

        # 無限ループしなければ成功
        result = adapter.list_items()

        assert len(result) == 2


# ---------------------------------------------------------------------------
# IngestionFeedbackHook
# ---------------------------------------------------------------------------


class TestIngestionFeedbackHookCallsGenerateForFile:
    def test_calls_generate_for_file_with_correct_input(self) -> None:
        """テスト対象: IngestionFeedbackHookCallsGenerateForFile の処理。
        テストケース: 個別条件での処理を検証する。
        期待結果: 想定どおりの処理結果が得られる。"""
        llm = _RecordingLlmClient()
        writer = _StubWriter()
        hook = IngestionFeedbackHook(
            llm_client=llm,  # type: ignore[arg-type]
            roadmap_reader=RoadmapItemReaderAdapter(_StubRetrievalReader([])),
            writer=writer,  # type: ignore[arg-type]
        )

        hook.on_file_ingested(
            source_path="notes/test.md",
            chunk_data=[(0, _LONG_TEXT)],
        )

        # writer に渡されたレコードを検証
        assert len(writer.records) == 1
        record = writer.records[0]
        assert record.source_path == "notes/test.md"  # type: ignore[union-attr]
        assert record.roadmap_item_id is None  # type: ignore[union-attr]
        assert record.is_read is False  # type: ignore[union-attr]
        assert record.read_at is None  # type: ignore[union-attr]

        # LLM に正しいリクエストが渡されたか検証
        assert len(llm.captured_requests) == 1
        llm_req = llm.captured_requests[0]
        assert llm_req.source_path == "notes/test.md"  # type: ignore[union-attr]
        assert llm_req.chunk_texts == [_LONG_TEXT]  # type: ignore[union-attr]

    def test_skips_when_chunks_too_short(self) -> None:
        """テスト対象: IngestionFeedbackHookCallsGenerateForFile の処理。
        テストケース: 個別条件での処理を検証する。
        期待結果: 想定どおりの処理結果が得られる。"""
        writer = _StubWriter()
        llm = _RecordingLlmClient()
        hook = IngestionFeedbackHook(
            llm_client=llm,  # type: ignore[arg-type]
            roadmap_reader=RoadmapItemReaderAdapter(_StubRetrievalReader([])),
            writer=writer,  # type: ignore[arg-type]
        )

        hook.on_file_ingested(
            source_path="notes/short.md",
            chunk_data=[(0, "short")],
        )

        assert len(writer.records) == 0
        assert len(llm.captured_requests) == 0

    def test_skips_when_chunk_data_empty(self) -> None:
        """テスト対象: IngestionFeedbackHookCallsGenerateForFile の処理。
        テストケース: 個別条件での処理を検証する。
        期待結果: 想定どおりの処理結果が得られる。"""
        writer = _StubWriter()
        hook = IngestionFeedbackHook(
            llm_client=_RecordingLlmClient(),  # type: ignore[arg-type]
            roadmap_reader=RoadmapItemReaderAdapter(_StubRetrievalReader([])),
            writer=writer,  # type: ignore[arg-type]
        )

        hook.on_file_ingested(source_path="notes/empty.md", chunk_data=[])

        assert len(writer.records) == 0

    def test_llm_error_propagates(self) -> None:
        """テスト対象: IngestionFeedbackHookCallsGenerateForFile の処理。
        テストケース: 個別条件での処理を検証する。
        期待結果: 想定どおりの処理結果が得られる。"""
        from ingestion.domain.ingestion_feedback_types import (
            IngestionFeedbackLlmCallError,
        )

        llm = _RecordingLlmClient(
            raise_error=IngestionFeedbackLlmCallError("llm failed"),
        )
        hook = IngestionFeedbackHook(
            llm_client=llm,  # type: ignore[arg-type]
            roadmap_reader=RoadmapItemReaderAdapter(_StubRetrievalReader([])),
            writer=_StubWriter(),  # type: ignore[arg-type]
        )

        with pytest.raises(IngestionFeedbackLlmCallError):
            hook.on_file_ingested(
                source_path="notes/test.md",
                chunk_data=[(0, _LONG_TEXT)],
            )
