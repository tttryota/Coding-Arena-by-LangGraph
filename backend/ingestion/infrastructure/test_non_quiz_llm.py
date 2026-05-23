"""Non-Quiz LLM + Embedder concrete 実装のテスト。"""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass
from unittest.mock import MagicMock


@dataclass
class FakeMessage:
    role: str
    content: str


class FakeTransport:
    def __init__(self, response: str) -> None:
        self._response = response
        self.last_messages: list[object] = []

    def call(
        self,
        messages: list[object],
        *,
        model: str = "default",
        temperature: float = 0.7,
    ) -> str:
        self.last_messages = messages
        return self._response


# ---------------------------------------------------------------------------
# CodexRoadmapGenerationLlm
# ---------------------------------------------------------------------------


class TestCodexRoadmapGenerationLlm:
    def test_returns_json_string(self) -> None:
        from roadmap.infrastructure.codex_roadmap_generation_llm import (
            CodexRoadmapGenerationLlm,
        )

        canned = '{"items": [{"title": "TypeScript"}]}'
        transport = FakeTransport(canned)
        adapter = CodexRoadmapGenerationLlm(transport)

        result = adapter.generate_roadmap_json("TypeScript")

        assert result == canned
        assert len(transport.last_messages) == 2
        assert "TypeScript" in transport.last_messages[-1].content

    def test_error_raises_llm_error(self) -> None:
        import pytest

        from roadmap.domain.roadmap_generation_types import (
            RoadmapGenerationLlmError,
        )
        from roadmap.infrastructure.codex_roadmap_generation_llm import (
            CodexRoadmapGenerationLlm,
        )

        class FailingTransport:
            def call(self, messages: list[object], **kwargs: object) -> str:
                msg = "connection error"
                raise RuntimeError(msg)

        adapter = CodexRoadmapGenerationLlm(FailingTransport())  # type: ignore[arg-type]

        with pytest.raises(RoadmapGenerationLlmError):
            adapter.generate_roadmap_json("Python")


# ---------------------------------------------------------------------------
# CodexIngestionFeedbackLlm
# ---------------------------------------------------------------------------


class TestCodexIngestionFeedbackLlm:
    def test_returns_response(self) -> None:
        from ingestion.domain.ingestion_feedback_types import (
            IngestionFeedbackLlmRequest,
            RoadmapCandidate,
        )
        from ingestion.infrastructure.codex_ingestion_feedback_llm import (
            CodexIngestionFeedbackLlm,
        )

        item_id = uuid.uuid4()
        canned = json.dumps({
            "selected_roadmap_item_id": str(item_id),
            "accuracy_check": "内容は正確です",
            "improvement_suggestions": ["具体例を追加"],
        })
        transport = FakeTransport(canned)
        adapter = CodexIngestionFeedbackLlm(transport)

        request = IngestionFeedbackLlmRequest(
            source_path="study/ts.md",
            chunk_texts=["チャンク1"],
            roadmap_candidates=[RoadmapCandidate(id=item_id, display_path="TS > Generics")],
        )
        result = adapter.analyze(request)

        assert result.selected_roadmap_item_id == item_id
        assert result.accuracy_check == "内容は正確です"
        assert result.improvement_suggestions == ["具体例を追加"]

    def test_null_roadmap_item_id(self) -> None:
        from ingestion.domain.ingestion_feedback_types import (
            IngestionFeedbackLlmRequest,
        )
        from ingestion.infrastructure.codex_ingestion_feedback_llm import (
            CodexIngestionFeedbackLlm,
        )

        canned = json.dumps({
            "selected_roadmap_item_id": None,
            "accuracy_check": "OK",
            "improvement_suggestions": [],
        })
        transport = FakeTransport(canned)
        adapter = CodexIngestionFeedbackLlm(transport)

        request = IngestionFeedbackLlmRequest(
            source_path="test.md",
            chunk_texts=["text"],
            roadmap_candidates=[],
        )
        result = adapter.analyze(request)

        assert result.selected_roadmap_item_id is None
        assert result.accuracy_check == "OK"
        assert result.improvement_suggestions == []

    def test_invalid_json_raises_response_format_error(self) -> None:
        import pytest

        from ingestion.domain.ingestion_feedback_types import (
            IngestionFeedbackLlmRequest,
            IngestionFeedbackResponseFormatError,
        )
        from ingestion.infrastructure.codex_ingestion_feedback_llm import (
            CodexIngestionFeedbackLlm,
        )

        transport = FakeTransport("not json")
        adapter = CodexIngestionFeedbackLlm(transport)

        request = IngestionFeedbackLlmRequest(
            source_path="test.md",
            chunk_texts=["text"],
            roadmap_candidates=[],
        )
        with pytest.raises(IngestionFeedbackResponseFormatError):
            adapter.analyze(request)

    def test_transport_failure_raises_llm_call_error(self) -> None:
        import pytest

        from ingestion.domain.ingestion_feedback_types import (
            IngestionFeedbackLlmCallError,
            IngestionFeedbackLlmRequest,
        )
        from ingestion.infrastructure.codex_ingestion_feedback_llm import (
            CodexIngestionFeedbackLlm,
        )

        class FailingTransport:
            def call(self, messages: list[object], **kwargs: object) -> str:
                msg = "connection error"
                raise RuntimeError(msg)

        adapter = CodexIngestionFeedbackLlm(FailingTransport())  # type: ignore[arg-type]

        request = IngestionFeedbackLlmRequest(
            source_path="test.md",
            chunk_texts=["text"],
            roadmap_candidates=[],
        )
        with pytest.raises(IngestionFeedbackLlmCallError):
            adapter.analyze(request)


# ---------------------------------------------------------------------------
# CodexLlmTagClassifier
# ---------------------------------------------------------------------------


class TestCodexLlmTagClassifier:
    def test_returns_tags(self) -> None:
        from ingestion.infrastructure.codex_llm_tag_classifier import (
            CodexLlmTagClassifier,
        )

        canned = json.dumps({"tags": ["TypeScript", "Generics"]})
        transport = FakeTransport(canned)
        classifier = CodexLlmTagClassifier(transport)

        result = classifier.classify("TypeScriptのジェネリクスについて")

        assert result == ["TypeScript", "Generics"]

    def test_invalid_json_raises_response_format_error(self) -> None:
        import pytest

        from ingestion.application.tagger import TaggingResponseFormatError
        from ingestion.infrastructure.codex_llm_tag_classifier import (
            CodexLlmTagClassifier,
        )

        transport = FakeTransport("invalid")
        classifier = CodexLlmTagClassifier(transport)

        with pytest.raises(TaggingResponseFormatError):
            classifier.classify("some text")

    def test_transport_failure_raises_llm_call_error(self) -> None:
        import pytest

        from ingestion.application.tagger import TaggingLlmCallError
        from ingestion.infrastructure.codex_llm_tag_classifier import (
            CodexLlmTagClassifier,
        )

        class FailingTransport:
            def call(self, messages: list[object], **kwargs: object) -> str:
                msg = "connection error"
                raise RuntimeError(msg)

        classifier = CodexLlmTagClassifier(FailingTransport())  # type: ignore[arg-type]

        with pytest.raises(TaggingLlmCallError):
            classifier.classify("some text")


# ---------------------------------------------------------------------------
# MultilingualE5Embedder
# ---------------------------------------------------------------------------


class TestMultilingualE5Embedder:
    def test_returns_embeddings(self) -> None:
        from ingestion.infrastructure.multilingual_e5_embedder import (
            MultilingualE5Embedder,
        )

        mock_model = MagicMock()

        class FakeArray:
            def __init__(self, data: list[list[float]]) -> None:
                self._data = data

            def __iter__(self):
                return iter([FakeVector(row) for row in self._data])

        class FakeVector:
            def __init__(self, data: list[float]) -> None:
                self._data = data

            def tolist(self) -> list[float]:
                return self._data

        mock_model.encode.return_value = FakeArray([
            [0.1, 0.2, 0.3],
            [0.4, 0.5, 0.6],
        ])

        embedder = MultilingualE5Embedder(mock_model)
        result = embedder.embed(["text1", "text2"])

        assert len(result) == 2
        assert result[0] == [0.1, 0.2, 0.3]
        assert result[1] == [0.4, 0.5, 0.6]
        mock_model.encode.assert_called_once_with(["text1", "text2"])

    def test_error_raises_embedding_model_call_error(self) -> None:
        import pytest

        from ingestion.domain.embedder_types import EmbeddingModelCallError
        from ingestion.infrastructure.multilingual_e5_embedder import (
            MultilingualE5Embedder,
        )

        mock_model = MagicMock()
        mock_model.encode.side_effect = RuntimeError("model error")

        embedder = MultilingualE5Embedder(mock_model)

        with pytest.raises(EmbeddingModelCallError):
            embedder.embed(["text"])
