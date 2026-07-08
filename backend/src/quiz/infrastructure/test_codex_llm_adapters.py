"""Quiz LLM アダプタ群のテスト。

FakeTransport で canned response を返し、
プロンプト構築とレスポンスパースの正当性を検証する。
"""

from __future__ import annotations

import json
from dataclasses import dataclass

# ---------------------------------------------------------------------------
# FakeTransport
# ---------------------------------------------------------------------------


@dataclass
class FakeMessage:
    role: str
    content: str


class FakeTransport:
    """CodexLlmTransport のテストダブル。canned response を返す。"""

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
# CodexQuestionSetDesignLlm
# ---------------------------------------------------------------------------


class TestCodexQuestionSetDesignLlm:
    def test_returns_confirmation_points(self) -> None:
        """テスト対象: CodexQuestionSetDesignLlm の処理。
        テストケース: 個別条件での処理を検証する。
        期待結果: 想定どおりの処理結果が得られる。"""
        from quiz.infrastructure.codex_llm_adapters import CodexQuestionSetDesignLlm

        canned = json.dumps({
            "topic_overview": "TypeScriptのジェネリクスは型安全なコードを書くための重要な機能です。",
            "confirmation_points": [
                {"id": "cp-001", "content": "型推論の仕組み", "format": "knowledge"},
                {"id": "cp-002", "content": "ジェネリクスの実装", "format": "knowledge_and_practice"},
            ],
        })
        transport = FakeTransport(canned)
        adapter = CodexQuestionSetDesignLlm(transport)

        result = adapter.generate_confirmation_points("TypeScript", "TS基礎", "detail")

        assert result.topic_overview == "TypeScriptのジェネリクスは型安全なコードを書くための重要な機能です。"
        assert len(result.confirmation_points) == 2
        assert result.confirmation_points[0]["id"] == "cp-001"
        assert result.confirmation_points[0]["content"] == "型推論の仕組み"
        assert result.confirmation_points[0]["format"] == "knowledge"
        assert result.confirmation_points[1]["id"] == "cp-002"
        assert result.confirmation_points[1]["content"] == "ジェネリクスの実装"
        assert result.confirmation_points[1]["format"] == "knowledge_and_practice"

    def test_empty_topic_overview_raises(self) -> None:
        """テスト対象: CodexQuestionSetDesignLlm の処理。
        テストケース: 個別条件での処理を検証する。
        期待結果: 想定どおりの処理結果が得られる。"""
        import pytest

        from quiz.application.question_set_design_types import QuestionSetDesignError
        from quiz.infrastructure.codex_llm_adapters import CodexQuestionSetDesignLlm

        canned = json.dumps({
            "topic_overview": "  ",
            "confirmation_points": [
                {"id": "cp-001", "content": "テスト", "format": "knowledge"},
            ],
        })
        transport = FakeTransport(canned)
        adapter = CodexQuestionSetDesignLlm(transport)

        with pytest.raises(QuestionSetDesignError):
            adapter.generate_confirmation_points("Test", "test", "detail")

    def test_prompt_contains_title_and_level(self) -> None:
        """テスト対象: CodexQuestionSetDesignLlm の処理。
        テストケース: 個別条件での処理を検証する。
        期待結果: 想定どおりの処理結果が得られる。"""
        from quiz.infrastructure.codex_llm_adapters import CodexQuestionSetDesignLlm

        transport = FakeTransport(json.dumps({
            "topic_overview": "概要",
            "confirmation_points": [],
        }))
        adapter = CodexQuestionSetDesignLlm(transport)
        adapter.generate_confirmation_points("React Hooks", "Hooks詳細", "middle")

        user_msg = transport.last_messages[-1].content
        assert "React Hooks" in user_msg
        assert "middle" in user_msg


# ---------------------------------------------------------------------------
# CodexQuestionDeliveryLlm
# ---------------------------------------------------------------------------


class TestCodexQuestionDeliveryLlm:
    def test_returns_question_output(self) -> None:
        """テスト対象: CodexQuestionDeliveryLlm の処理。
        テストケース: 個別条件での処理を検証する。
        期待結果: 想定どおりの処理結果が得られる。"""
        from quiz.infrastructure.codex_llm_adapters import CodexQuestionDeliveryLlm

        canned = json.dumps({
            "question_text": "useStateの初期値はどう決まりますか?",
            "answer_type": "textarea",
        })
        transport = FakeTransport(canned)
        adapter = CodexQuestionDeliveryLlm(transport)

        result = adapter.generate_question(
            "React", "React Hooks", "useState", "knowledge", [],
        )

        assert result.question_text == "useStateの初期値はどう決まりますか?"
        assert result.answer_type == "textarea"

    def test_returns_code_type_for_knowledge_and_practice(self) -> None:
        """テスト対象: CodexQuestionDeliveryLlm の処理。
        テストケース: 個別条件での処理を検証する。
        期待結果: 想定どおりの処理結果が得られる。"""
        from quiz.infrastructure.codex_llm_adapters import CodexQuestionDeliveryLlm

        canned = json.dumps({
            "question_text": "TypeGuardを実装してください",
            "answer_type": "code",
        })
        transport = FakeTransport(canned)
        adapter = CodexQuestionDeliveryLlm(transport)

        result = adapter.generate_question(
            "TypeScript", "型ガード", "TypeGuard実装", "knowledge_and_practice", [],
        )

        assert result.question_text == "TypeGuardを実装してください"
        assert result.answer_type == "code"


# ---------------------------------------------------------------------------
# CodexInputClassificationLlm
# ---------------------------------------------------------------------------


class TestCodexInputClassificationLlm:
    def test_returns_input_type(self) -> None:
        """テスト対象: CodexInputClassificationLlm の処理。
        テストケース: 個別条件での処理を検証する。
        期待結果: 想定どおりの処理結果が得られる。"""
        from quiz.infrastructure.codex_llm_adapters import CodexInputClassificationLlm

        canned = json.dumps({"input_type": "answer"})
        transport = FakeTransport(canned)
        adapter = CodexInputClassificationLlm(transport)

        result = adapter.classify_input("問題文", "回答テキスト")

        assert result == "answer"

    def test_classifies_as_question(self) -> None:
        """テスト対象: CodexInputClassificationLlm の処理。
        テストケース: 個別条件での処理を検証する。
        期待結果: 想定どおりの処理結果が得られる。"""
        from quiz.infrastructure.codex_llm_adapters import CodexInputClassificationLlm

        canned = json.dumps({"input_type": "question"})
        transport = FakeTransport(canned)
        adapter = CodexInputClassificationLlm(transport)

        result = adapter.classify_input("問題文", "これはどういう意味?")

        assert result == "question"

    def test_classifies_as_explanation_request(self) -> None:
        """テスト対象: CodexInputClassificationLlm の処理。
        テストケース: 個別条件での処理を検証する。
        期待結果: 想定どおりの処理結果が得られる。"""
        from quiz.infrastructure.codex_llm_adapters import CodexInputClassificationLlm

        canned = json.dumps({"input_type": "explanation_request"})
        transport = FakeTransport(canned)
        adapter = CodexInputClassificationLlm(transport)

        result = adapter.classify_input("問題文", "解説してください")

        assert result == "explanation_request"


# ---------------------------------------------------------------------------
# CodexChatResponseLlm
# ---------------------------------------------------------------------------


class TestCodexChatResponseLlm:
    def test_returns_response_text(self) -> None:
        """テスト対象: CodexChatResponseLlm の処理。
        テストケース: 個別条件での処理を検証する。
        期待結果: 想定どおりの処理結果が得られる。"""
        from quiz.infrastructure.codex_llm_adapters import CodexChatResponseLlm

        transport = FakeTransport("useStateは状態管理のためのHookです。")
        adapter = CodexChatResponseLlm(transport)

        result = adapter.generate_chat_response("useState問題", "useStateって何?")

        assert result == "useStateは状態管理のためのHookです。"


# ---------------------------------------------------------------------------
# CodexAnswerEvaluationLlm
# ---------------------------------------------------------------------------


class TestCodexAnswerEvaluationLlm:
    def test_returns_evaluation_output(self) -> None:
        """テスト対象: CodexAnswerEvaluationLlm の処理。
        テストケース: 個別条件での処理を検証する。
        期待結果: 想定どおりの処理結果が得られる。"""
        from quiz.infrastructure.codex_llm_adapters import CodexAnswerEvaluationLlm

        canned = json.dumps({
            "next_action": "next",
            "score": 85,
            "feedback": "正確な理解です",
            "deepdive_points": [],
        })
        transport = FakeTransport(canned)
        adapter = CodexAnswerEvaluationLlm(transport)

        result = adapter.evaluate_answer(
            "問題文", "確認ポイント", "回答テキスト", "textarea", [], 1, [],
        )

        assert result.next_action == "next"
        assert result.score == 85
        assert result.feedback == "正確な理解です"
        assert result.deepdive_points == []

    def test_returns_deepdive_points(self) -> None:
        """テスト対象: CodexAnswerEvaluationLlm の処理。
        テストケース: 個別条件での処理を検証する。
        期待結果: 想定どおりの処理結果が得られる。"""
        from quiz.infrastructure.codex_llm_adapters import CodexAnswerEvaluationLlm

        canned = json.dumps({
            "next_action": "deepdive",
            "score": 50,
            "feedback": "深掘りが必要",
            "deepdive_points": [
                {"content": "型ガード", "format": "knowledge"},
            ],
        })
        transport = FakeTransport(canned)
        adapter = CodexAnswerEvaluationLlm(transport)

        result = adapter.evaluate_answer(
            "問題文", "確認ポイント", "回答", "textarea", [], 1, [],
        )

        assert result.next_action == "deepdive"
        assert result.score == 50
        assert result.feedback == "深掘りが必要"
        assert len(result.deepdive_points) == 1
        assert result.deepdive_points[0]["content"] == "型ガード"
        assert result.deepdive_points[0]["format"] == "knowledge"
        assert "id" not in result.deepdive_points[0]

    def test_returns_complete_action(self) -> None:
        """テスト対象: CodexAnswerEvaluationLlm の処理。
        テストケース: 個別条件での処理を検証する。
        期待結果: 想定どおりの処理結果が得られる。"""
        from quiz.infrastructure.codex_llm_adapters import CodexAnswerEvaluationLlm

        canned = json.dumps({
            "next_action": "complete",
            "score": 90,
            "feedback": "十分な理解です",
            "deepdive_points": [],
        })
        transport = FakeTransport(canned)
        adapter = CodexAnswerEvaluationLlm(transport)

        result = adapter.evaluate_answer(
            "問題文", "確認ポイント", "回答", "textarea", [], 5, [],
        )

        assert result.next_action == "complete"
        assert result.score == 90
        assert result.feedback == "十分な理解です"
        assert result.deepdive_points == []


# ---------------------------------------------------------------------------
# CodexExplanationLlm
# ---------------------------------------------------------------------------


class TestCodexExplanationLlm:
    def test_returns_explanation(self) -> None:
        """テスト対象: CodexExplanationLlm の処理。
        テストケース: 個別条件での処理を検証する。
        期待結果: 想定どおりの処理結果が得られる。"""
        from quiz.infrastructure.codex_llm_adapters import CodexExplanationLlm

        transport = FakeTransport("型推論とは、コンパイラが型を自動判別する仕組みです。")
        adapter = CodexExplanationLlm(transport)

        result = adapter.generate_explanation("問題文", "型推論")

        assert result == "型推論とは、コンパイラが型を自動判別する仕組みです。"


# ---------------------------------------------------------------------------
# CodexProgressUpdateLlm
# ---------------------------------------------------------------------------


class TestCodexProgressUpdateLlm:
    def test_returns_progress_output(self) -> None:
        """テスト対象: CodexProgressUpdateLlm の処理。
        テストケース: 個別条件での処理を検証する。
        期待結果: 想定どおりの処理結果が得られる。"""
        from quiz.infrastructure.codex_llm_adapters import CodexProgressUpdateLlm

        canned = json.dumps({"score": 75, "comment": "全体的に良好"})
        transport = FakeTransport(canned)
        adapter = CodexProgressUpdateLlm(transport)

        result = adapter.evaluate_session("TS", "TypeScript基礎", ["cp1"], [])

        assert result.score == 75
        assert result.comment == "全体的に良好"


# ---------------------------------------------------------------------------
# CodexSummaryTestLlm
# ---------------------------------------------------------------------------


class TestCodexSummaryTestLlm:
    def test_returns_summary_analysis(self) -> None:
        """テスト対象: CodexSummaryTestLlm の処理。
        テストケース: 個別条件での処理を検証する。
        期待結果: 想定どおりの処理結果が得られる。"""
        from quiz.infrastructure.codex_llm_adapters import CodexSummaryTestLlm

        canned = json.dumps({"score": 80, "analysis": "型システムの理解は良好"})
        transport = FakeTransport(canned)
        adapter = CodexSummaryTestLlm(transport)

        result = adapter.analyze_session("TS", "TypeScript基礎", [])

        assert result.score == 80
        assert result.analysis == "型システムの理解は良好"


# ---------------------------------------------------------------------------
# CodexLlmTransport unit test
# ---------------------------------------------------------------------------


class TestCodexLlmTransport:
    def test_parse_json_with_code_fence(self) -> None:
        """テスト対象: CodexLlmTransport の処理。
        テストケース: 個別条件での処理を検証する。
        期待結果: 想定どおりの処理結果が得られる。"""
        from quiz.infrastructure.codex_llm_adapters import _parse_json

        text = '```json\n{"key": "value"}\n```'
        result = _parse_json(text)

        assert result == {"key": "value"}

    def test_parse_json_plain(self) -> None:
        """テスト対象: CodexLlmTransport の処理。
        テストケース: 個別条件での処理を検証する。
        期待結果: 想定どおりの処理結果が得られる。"""
        from quiz.infrastructure.codex_llm_adapters import _parse_json

        text = '{"key": "value"}'
        result = _parse_json(text)

        assert result == {"key": "value"}


# ---------------------------------------------------------------------------
# Convergence rule + validation tests
# ---------------------------------------------------------------------------


class TestDeepdiveEmptyRaises:
    def test_deepdive_with_empty_points_raises(self) -> None:
        """テスト対象: DeepdiveEmptyRaises の処理。
        テストケース: 個別条件での処理を検証する。
        期待結果: 想定どおりの処理結果が得られる。"""
        import pytest

        from quiz.application.answer_evaluation_types import AnswerEvaluationError
        from quiz.infrastructure.codex_llm_adapters import CodexAnswerEvaluationLlm

        canned = json.dumps({
            "next_action": "deepdive",
            "score": 60,
            "feedback": "深掘りが必要",
            "deepdive_points": [],
        })
        transport = FakeTransport(canned)
        adapter = CodexAnswerEvaluationLlm(transport)

        with pytest.raises(AnswerEvaluationError):
            adapter.evaluate_answer(
                "問題文", "確認ポイント", "回答", "textarea", [], 5, [],
            )


class TestInputTypeValidation:
    def test_invalid_input_type_raises(self) -> None:
        """テスト対象: InputTypeValidation の処理。
        テストケース: 個別条件での処理を検証する。
        期待結果: 想定どおりの処理結果が得られる。"""
        import pytest

        from quiz.application.input_classification_types import (
            InputClassificationError,
        )
        from quiz.infrastructure.codex_llm_adapters import CodexInputClassificationLlm

        canned = json.dumps({"input_type": "invalid_value"})
        transport = FakeTransport(canned)
        adapter = CodexInputClassificationLlm(transport)

        with pytest.raises(InputClassificationError):
            adapter.classify_input("問題文", "入力")


class TestAnswerTypeValidation:
    def test_format_knowledge_with_wrong_answer_type_raises(self) -> None:
        """テスト対象: AnswerTypeValidation の処理。
        テストケース: 個別条件での処理を検証する。
        期待結果: 想定どおりの処理結果が得られる。"""
        import pytest

        from quiz.application.question_delivery_types import QuestionDeliveryError
        from quiz.infrastructure.codex_llm_adapters import CodexQuestionDeliveryLlm

        canned = json.dumps({
            "question_text": "問題",
            "answer_type": "code",
        })
        transport = FakeTransport(canned)
        adapter = CodexQuestionDeliveryLlm(transport)

        with pytest.raises(QuestionDeliveryError):
            adapter.generate_question(
                "TS", "TS基礎", "cp内容", "knowledge", [],
            )


class TestErrorWrapping:
    def test_transport_error_wrapped_in_protocol_error(self) -> None:
        """テスト対象: ErrorWrapping の処理。
        テストケース: 個別条件での処理を検証する。
        期待結果: 想定どおりの処理結果が得られる。"""
        import pytest

        from quiz.application.question_set_design_types import QuestionSetDesignError
        from quiz.infrastructure.codex_llm_adapters import CodexQuestionSetDesignLlm

        transport = FakeTransport("not valid json")
        adapter = CodexQuestionSetDesignLlm(transport)

        with pytest.raises(QuestionSetDesignError):
            adapter.generate_confirmation_points("TS", "基礎", "detail")
