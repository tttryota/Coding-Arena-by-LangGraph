"""Topic シナリオテスト F-4。

list_topic_candidates → register_manual_topic → 重複排除確認。
API エンドポイントがないため application 層を直接テスト。
実 SQLite + 実 ChromaDB を使用。
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class _PresetTopicRecord:
    name: str
    canonical_name: str


class _StubPresetReader:
    """テスト用の固定プリセットリーダー。"""

    def __init__(self, topics: list[_PresetTopicRecord]) -> None:
        self._topics = list(topics)

    def list_preset_topics(self) -> list[_PresetTopicRecord]:
        return list(self._topics)


def _add_note_chunk(container: object, tag: str) -> None:
    """ChromaDB にタグ付きチャンクを追加して note ソースを作る。"""
    from ingestion.domain.batch_scheduler_types import (
        ChunkStoreChunkInput,
        ChunkStoreUpsertInput,
    )

    chunk_store = container.chunk_store  # type: ignore[attr-defined]
    chunk_store.upsert_chunks(
        ChunkStoreUpsertInput(
            source_path=f"notes/{tag}.md",
            chunks=[
                ChunkStoreChunkInput(
                    chunk_index=0,
                    text=f"{tag} content",
                    embedding=[0.1] * 384,
                    headers=tag,
                    tags=[tag],
                    created_at="2026-05-20T00:00:00+00:00",
                    updated_at="2026-05-20T00:00:00+00:00",
                ),
            ],
        ),
    )


class TestF4TopicMergeAndManualRegistration:
    def test_three_source_merge_with_deduplication(
        self,
        integration_container: object,
    ) -> None:
        """3ソース (preset, manual, note) からマージし、重複排除を確認する。"""
        from roadmap.application.topic_listing import (
            list_topic_candidates,
            register_manual_topic,
        )

        container = integration_container
        topic_store = container.topic_store  # type: ignore[attr-defined]
        note_topic_reader = container.note_topic_reader  # type: ignore[attr-defined]

        # Arrange: preset に TypeScript を設定
        preset_reader = _StubPresetReader(
            [
                _PresetTopicRecord(name="TypeScript", canonical_name="typescript"),
            ],
        )

        # Arrange: manual に Docker を登録
        register_manual_topic(
            "Docker",
            topic_store=topic_store,
            note_count_reader=note_topic_reader,
        )

        # Arrange: note ソースを ChromaDB に追加
        _add_note_chunk(container, "react")

        # Act
        candidates = list_topic_candidates(
            preset_reader=preset_reader,
            note_topic_reader=note_topic_reader,
            topic_store=topic_store,
            note_count_reader=note_topic_reader,
        )

        # Assert: 3ソースからの候補が含まれる
        names = {c.name for c in candidates}
        assert "TypeScript" in names  # preset
        assert "Docker" in names  # manual
        assert "react" in names  # note

        # Assert: ソースが正しい
        ts = next(c for c in candidates if c.name == "TypeScript")
        docker = next(c for c in candidates if c.name == "Docker")
        react = next(c for c in candidates if c.name == "react")
        assert ts.source == "preset"
        assert docker.source == "manual"
        assert react.source == "note"

        # Assert: 重複排除 - canonical name ごとに1件
        canonical_names = [c.name.casefold() for c in candidates]
        assert len(canonical_names) == len(set(canonical_names))

    def test_manual_duplicate_detection(
        self,
        integration_container: object,
    ) -> None:
        """同じ canonical name で2回登録しても重複しない。"""
        from roadmap.application.topic_listing import register_manual_topic

        container = integration_container
        topic_store = container.topic_store  # type: ignore[attr-defined]
        note_topic_reader = container.note_topic_reader  # type: ignore[attr-defined]

        # Act: 1回目登録
        first = register_manual_topic(
            "Docker",
            topic_store=topic_store,
            note_count_reader=note_topic_reader,
        )

        # Act: 2回目登録 (大文字小文字違い)
        second = register_manual_topic(
            "docker",
            topic_store=topic_store,
            note_count_reader=note_topic_reader,
        )

        # Assert: 同じトピックが返る
        assert first.name == second.name
        assert first.source == "manual"

    def test_preset_overrides_manual_on_merge(
        self,
        integration_container: object,
    ) -> None:
        """preset と manual に同じトピックがある場合、preset が優先される。"""
        from roadmap.application.topic_listing import (
            list_topic_candidates,
            register_manual_topic,
        )

        container = integration_container
        topic_store = container.topic_store  # type: ignore[attr-defined]
        note_topic_reader = container.note_topic_reader  # type: ignore[attr-defined]

        # Arrange: manual に typescript を登録
        register_manual_topic(
            "typescript",
            topic_store=topic_store,
            note_count_reader=note_topic_reader,
        )

        # Arrange: preset にも TypeScript を設定
        preset_reader = _StubPresetReader(
            [
                _PresetTopicRecord(name="TypeScript", canonical_name="typescript"),
            ],
        )

        # Act
        candidates = list_topic_candidates(
            preset_reader=preset_reader,
            note_topic_reader=note_topic_reader,
            topic_store=topic_store,
            note_count_reader=note_topic_reader,
        )

        # Assert: preset が優先、かつ typescript は1件のみ
        ts_candidates = [c for c in candidates if c.name.casefold() == "typescript"]
        assert len(ts_candidates) == 1
        assert ts_candidates[0].source == "preset"
