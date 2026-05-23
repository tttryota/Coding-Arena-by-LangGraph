"""Ingestion シナリオテスト I-1..I-3。

I-1: POST /ingestion/trigger → 実ファイルシステム → チャンク保存
I-2: generate_for_file → list_feedbacks で表示確認 (app 層直接)
I-3: 空チャンクスキップ (app 層直接)
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path

    from fastapi.testclient import TestClient

    from tests.integration.stubs.scenario_llm_transport import ScenarioLlmTransport


# ---------------------------------------------------------------------------
# I-1: バッチ実行トリガー
# ---------------------------------------------------------------------------


class TestI1BatchTrigger:
    def test_trigger_processes_markdown_files(
        self,
        client: TestClient,
        integration_container: object,
        scenario_transport: ScenarioLlmTransport,
        tmp_path: Path,
    ) -> None:
        # Arrange: tmp_path に markdown ファイルを作成
        md_file = tmp_path / "test_note.md"
        md_file.write_text(
            "# Test\n\nThis is a test note with enough text for chunking.",
            encoding="utf-8",
        )

        # Arrange: LLM (tagger) のレスポンスを設定
        scenario_transport.set_sequential_responses(
            [
                json.dumps({"tags": ["test"]}, ensure_ascii=False),
            ],
        )

        # Act
        resp = client.post(
            "/ingestion/trigger",
            json={"target_path": str(tmp_path), "trigger": "startup"},
        )

        # Assert: サマリー返却
        assert resp.status_code == 202
        data = resp.json()
        assert data["status"] in ("completed", "completed_with_errors")
        assert data["trigger"] == "startup"

        # Assert: diff 処理結果
        assert data["new_count"] >= 1
        assert data["ingest_target_count"] >= 1

        # Assert: チャンク保存
        assert data["stored_chunk_count"] >= 1


# ---------------------------------------------------------------------------
# I-2: フィードバック生成 → 一覧取得
# ---------------------------------------------------------------------------


class TestI2FeedbackGeneration:
    def test_generate_feedback_then_list(
        self,
        client: TestClient,
        integration_container: object,
        scenario_transport: ScenarioLlmTransport,
    ) -> None:
        """generate_for_file でフィードバック生成し、GET /feedbacks で確認。"""
        from ingestion.application.ingestion_feedback import generate_for_file
        from ingestion.domain.ingestion_feedback_types import (
            IngestionFeedbackChunkInput,
            IngestionFeedbackGenerateInput,
        )

        container = integration_container

        # Arrange: LLM レスポンス (フィードバック分析)
        llm_response = json.dumps(
            {
                "selected_roadmap_item_id": None,
                "accuracy_check": "正確に記述されています",
                "improvement_suggestions": ["より詳細な例を追加"],
            },
            ensure_ascii=False,
        )
        scenario_transport.set_sequential_responses([llm_response])

        # Act: フィードバック生成
        feedback_input = IngestionFeedbackGenerateInput(
            source_path="notes/test.md",
            chunks=[
                IngestionFeedbackChunkInput(
                    chunk_index=0,
                    text="TypeScript のジェネリクスは型パラメータを使って再利用可能な型を定義できます。",
                ),
            ],
            minimum_chunk_characters=10,
            generated_at="2026-05-23T00:00:00+00:00",
        )

        # RoadmapItemReader stub (空リスト)
        class _StubRoadmapReader:
            def list_items(self) -> list:
                return []

        result = generate_for_file(
            feedback_input,
            llm_client=container.ingestion_feedback_llm,  # type: ignore[attr-defined]
            roadmap_reader=_StubRoadmapReader(),
            writer=container.ingestion_feedback_store,  # type: ignore[attr-defined]
        )
        assert result.status == "created"

        # Act: GET /feedbacks で確認
        list_resp = client.get("/ingestion/feedbacks")
        assert list_resp.status_code == 200
        data = list_resp.json()
        assert data["total_count"] >= 1

        feedback = next(
            (f for f in data["items"] if f["source_path"] == "notes/test.md"),
            None,
        )
        assert feedback is not None
        assert feedback["is_read"] is False


# ---------------------------------------------------------------------------
# I-3: 空チャンクスキップ
# ---------------------------------------------------------------------------


class TestI3EmptyChunkSkip:
    def test_skips_when_chunks_below_minimum(
        self,
        integration_container: object,
        scenario_transport: ScenarioLlmTransport,
    ) -> None:
        """minimum_chunk_characters 未満のチャンクのみ → status="skipped"。"""
        from ingestion.application.ingestion_feedback import generate_for_file
        from ingestion.domain.ingestion_feedback_types import (
            IngestionFeedbackChunkInput,
            IngestionFeedbackGenerateInput,
        )

        class _StubRoadmapReader:
            def list_items(self) -> list:
                return []

        container = integration_container
        feedback_input = IngestionFeedbackGenerateInput(
            source_path="notes/short.md",
            chunks=[
                IngestionFeedbackChunkInput(chunk_index=0, text="短い"),
                IngestionFeedbackChunkInput(chunk_index=1, text="abc"),
            ],
            minimum_chunk_characters=100,
            generated_at="2026-05-23T00:00:00+00:00",
        )

        result = generate_for_file(
            feedback_input,
            llm_client=container.ingestion_feedback_llm,  # type: ignore[attr-defined]
            roadmap_reader=_StubRoadmapReader(),
            writer=container.ingestion_feedback_store,  # type: ignore[attr-defined]
        )

        assert result.status == "skipped"
        assert result.skip_reason == "no_analyzable_chunks"
        assert result.created_feedback is None
        assert scenario_transport.call_count == 0
