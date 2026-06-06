"""コーディングセッション用 LLM アダプタのテスト。"""

from __future__ import annotations

import json
from dataclasses import dataclass

import pytest


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
# CodexLectureGenerationLlm
# ---------------------------------------------------------------------------


class TestCodexLectureGenerationLlm:
    def test_returns_lecture_content(self) -> None:
        from quiz.infrastructure.codex_coding_llm_adapters import (
            CodexLectureGenerationLlm,
        )

        canned = json.dumps({"lecture_content": "ジェネリクスとは型安全な再利用を可能にする仕組みです。"})
        transport = FakeTransport(canned)
        adapter = CodexLectureGenerationLlm(transport)

        result = adapter.generate_lecture("ジェネリクス", "型パラメータの基礎")
        assert result.lecture_content == "ジェネリクスとは型安全な再利用を可能にする仕組みです。"

    def test_empty_content_raises(self) -> None:
        from quiz.infrastructure.codex_coding_llm_adapters import (
            CodexLectureGenerationLlm,
            LectureGenerationError,
        )

        canned = json.dumps({"lecture_content": "  "})
        transport = FakeTransport(canned)
        adapter = CodexLectureGenerationLlm(transport)

        with pytest.raises(LectureGenerationError):
            adapter.generate_lecture("テスト", "テスト")


# ---------------------------------------------------------------------------
# CodexLectureChatResponseLlm
# ---------------------------------------------------------------------------


class TestCodexLectureChatResponseLlm:
    def test_returns_response_text(self) -> None:
        from quiz.infrastructure.codex_coding_llm_adapters import (
            CodexLectureChatResponseLlm,
        )

        transport = FakeTransport("型パラメータは関数やクラスに型の柔軟性を与えます。")
        adapter = CodexLectureChatResponseLlm(transport)

        result = adapter.generate_chat_response("座学テキスト", "型パラメータって何?")
        assert "型パラメータ" in result


# ---------------------------------------------------------------------------
# CodexCodingProblemSetDesignLlm
# ---------------------------------------------------------------------------


_VALID_DESIGN_RESPONSE = json.dumps({
    "confirmation_points": [
        {"id": "cp-001", "content": "基本的な型パラメータ", "start_format": "rewrite", "end_format": "fill_blank"},
        {"id": "cp-002", "content": "制約付きジェネリクス", "start_format": "fill_blank", "end_format": "extend"},
        {"id": "cp-003", "content": "ジェネリクスの実用", "start_format": "bug_fix", "end_format": "implement"},
    ],
})


class TestCodexCodingProblemSetDesignLlm:
    def test_returns_confirmation_points(self) -> None:
        from quiz.infrastructure.codex_coding_llm_adapters import (
            CodexCodingProblemSetDesignLlm,
        )

        transport = FakeTransport(_VALID_DESIGN_RESPONSE)
        adapter = CodexCodingProblemSetDesignLlm(transport)

        result = adapter.design_problem_set("ジェネリクス", "型パラメータ", "座学テキスト")
        assert len(result.confirmation_points) == 3
        assert result.confirmation_points[0].id == "cp-001"
        assert result.confirmation_points[0].start_format == "rewrite"
        assert result.confirmation_points[0].end_format == "fill_blank"

    def test_empty_points_raises(self) -> None:
        from quiz.infrastructure.codex_coding_llm_adapters import (
            CodexCodingProblemSetDesignLlm,
            CodingProblemSetDesignError,
        )

        bad = json.dumps({"confirmation_points": []})
        transport = FakeTransport(bad)
        adapter = CodexCodingProblemSetDesignLlm(transport)

        with pytest.raises(CodingProblemSetDesignError):
            adapter.design_problem_set("テスト", "テスト", "テスト")

    def test_reversed_format_order_raises(self) -> None:
        from quiz.infrastructure.codex_coding_llm_adapters import (
            CodexCodingProblemSetDesignLlm,
            CodingProblemSetDesignError,
        )

        bad = json.dumps({
            "confirmation_points": [
                {"id": "cp-001", "content": "テスト", "start_format": "implement", "end_format": "rewrite"},
            ],
        })
        transport = FakeTransport(bad)
        adapter = CodexCodingProblemSetDesignLlm(transport)

        with pytest.raises(CodingProblemSetDesignError):
            adapter.design_problem_set("テスト", "テスト", "テスト")

    def test_invalid_format_raises(self) -> None:
        from quiz.infrastructure.codex_coding_llm_adapters import (
            CodexCodingProblemSetDesignLlm,
            CodingProblemSetDesignError,
        )

        bad = json.dumps({
            "confirmation_points": [
                {"id": "cp-001", "content": "テスト", "start_format": "invalid", "end_format": "rewrite"},
                {"id": "cp-002", "content": "テスト", "start_format": "rewrite", "end_format": "fill_blank"},
                {"id": "cp-003", "content": "テスト", "start_format": "rewrite", "end_format": "implement"},
            ],
        })
        transport = FakeTransport(bad)
        adapter = CodexCodingProblemSetDesignLlm(transport)

        with pytest.raises(CodingProblemSetDesignError):
            adapter.design_problem_set("テスト", "テスト", "テスト")


# ---------------------------------------------------------------------------
# CodexCodingProblemDeliveryLlm
# ---------------------------------------------------------------------------


class TestCodexCodingProblemDeliveryLlm:
    def test_returns_question_and_code(self) -> None:
        from quiz.infrastructure.codex_coding_llm_adapters import (
            CodexCodingProblemDeliveryLlm,
        )

        canned = json.dumps({
            "question_text": "この関数の戻り値を変更してください",
            "example_code": "def greet(): return 'hello'",
        })
        transport = FakeTransport(canned)
        adapter = CodexCodingProblemDeliveryLlm(transport)

        result = adapter.deliver_problem("ジェネリクス", "基本型パラメータ", "rewrite", "座学")
        assert result.question_text == "この関数の戻り値を変更してください"
        assert result.example_code == "def greet(): return 'hello'"

    def test_prompt_contains_format(self) -> None:
        from quiz.infrastructure.codex_coding_llm_adapters import (
            CodexCodingProblemDeliveryLlm,
        )

        canned = json.dumps({"question_text": "Q", "example_code": "C"})
        transport = FakeTransport(canned)
        adapter = CodexCodingProblemDeliveryLlm(transport)

        adapter.deliver_problem("タイトル", "CP", "bug_fix", "座学")
        system_msg = transport.last_messages[0].content
        assert "bug_fix" in system_msg


# ---------------------------------------------------------------------------
# CodexCodeEvaluationLlm
# ---------------------------------------------------------------------------


class TestCodexCodeEvaluationLlm:
    def test_returns_evaluation(self) -> None:
        from quiz.infrastructure.codex_coding_llm_adapters import (
            CodexCodeEvaluationLlm,
        )

        canned = json.dumps({
            "score": 80,
            "feedback": "正しく動作しています",
        })
        transport = FakeTransport(canned)
        adapter = CodexCodeEvaluationLlm(transport)

        result = adapter.evaluate_code(
            question_text="問題",
            example_code="コード",
            user_code="回答",
            current_format="rewrite",
            confirmation_point_content="CP",
        )
        assert result.score == 80
        assert result.feedback == "正しく動作しています"

    def test_score_out_of_range_raises(self) -> None:
        from quiz.infrastructure.codex_coding_llm_adapters import (
            CodeEvaluationError,
            CodexCodeEvaluationLlm,
        )

        canned = json.dumps({
            "score": 150,
            "feedback": "ok",
        })
        transport = FakeTransport(canned)
        adapter = CodexCodeEvaluationLlm(transport)

        with pytest.raises(CodeEvaluationError):
            adapter.evaluate_code(
                question_text="Q", example_code="C", user_code="A",
                current_format="rewrite", confirmation_point_content="CP",
            )
