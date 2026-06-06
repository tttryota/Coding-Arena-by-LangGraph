"""コーディンググラフの統合テスト。

モック LLM でフロー全体を通し、
lecture -> await_lecture -> practice_start -> CP設計 -> 出題 -> await_coding -> 評価 -> END
の一連のフローを検証する。
"""

from __future__ import annotations

from langgraph.checkpoint.memory import MemorySaver

# ---------------------------------------------------------------------------
# Fake dependencies
# ---------------------------------------------------------------------------


class FakeLectureResult:
    lecture_content = "座学テキスト: ジェネリクスの基礎"


class FakeLectureGenerationLlm:
    def generate_lecture(self, title: str, description: str) -> FakeLectureResult:
        return FakeLectureResult()


class FakeLectureChatResponseLlm:
    def generate_chat_response(self, lecture_content: str, user_input: str) -> str:
        return "チャット応答テキスト"


class FakeCPDraft:
    def __init__(self, cp_id: str, content: str, start: str, end: str) -> None:
        self.id = cp_id
        self.content = content
        self.start_format = start
        self.end_format = end


class FakeProblemSetResult:
    def __init__(self) -> None:
        self.confirmation_points = [
            FakeCPDraft("cp-001", "基本型パラメータ", "rewrite", "rewrite"),
        ]


class FakeProblemSetDesignLlm:
    def design_problem_set(
        self, title: str, description: str, lecture_content: str,
    ) -> FakeProblemSetResult:
        return FakeProblemSetResult()


class FakeProblemDeliveryResult:
    question_text = "この関数の戻り値を変更してください"
    example_code = "def greet(): return 'hello'"


class FakeProblemDeliveryLlm:
    def deliver_problem(
        self, title: str, cp_content: str, fmt: str, lecture: str,
    ) -> FakeProblemDeliveryResult:
        return FakeProblemDeliveryResult()


class FakeCodingChatResponseLlm:
    def generate_chat_response(self, lecture_content: str, user_input: str) -> str:
        return "コーディングチャット応答"


class FakeEvalResult:
    def __init__(self) -> None:
        self.score = 85
        self.feedback = "正しく動作しています"


class FakeCodeEvaluationLlm:
    def evaluate_code(self, **_kwargs: object) -> FakeEvalResult:
        return FakeEvalResult()


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------


def _build_graph_and_runner() -> tuple:
    from quiz.application.coding_graph import (
        CodingGraphDependencies,
        CodingGraphRunner,
        build_coding_graph,
    )

    deps = CodingGraphDependencies(
        lecture_generation_llm=FakeLectureGenerationLlm(),
        lecture_chat_response_llm=FakeLectureChatResponseLlm(),
        coding_problem_set_design_llm=FakeProblemSetDesignLlm(),
        coding_problem_delivery_llm=FakeProblemDeliveryLlm(),
        coding_chat_response_llm=FakeCodingChatResponseLlm(),
        code_evaluation_llm=FakeCodeEvaluationLlm(),
    )
    checkpointer = MemorySaver()
    compiled = build_coding_graph(deps, checkpointer=checkpointer)
    runner = CodingGraphRunner(compiled)
    return runner, compiled


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestCodingGraphFlow:
    def test_lecture_to_practice_to_complete(self) -> None:
        """座学 -> practice開始 -> 出題 -> 回答 -> complete のフルフロー。"""
        runner, _ = _build_graph_and_runner()
        thread_id = "test-coding-001"

        initial_state = {
            "session_id": thread_id,
            "roadmap_item_id": "item-001",
            "roadmap_item_level": "detail",
            "roadmap_item_title": "ジェネリクス",
            "roadmap_item_description": "型パラメータの基礎",
            "is_resumed": False,
        }

        runner.start_graph(initial_state, thread_id=thread_id)

        state = runner.get_state(thread_id=thread_id)
        assert state["lecture_content"] == "座学テキスト: ジェネリクスの基礎"
        assert state["lecture_phase_active"] is True

        runner.resume_graph(
            {"lecture_phase_active": False},
            thread_id=thread_id,
        )

        state = runner.get_state(thread_id=thread_id)
        assert len(state["confirmation_points"]) == 1
        assert state["current_question_text"] == "この関数の戻り値を変更してください"

        runner.resume_graph(
            {"user_input": "def greet(): return 'hi'", "input_source": "form"},
            thread_id=thread_id,
        )

        final_state = runner.get_state(thread_id=thread_id)
        assert final_state["next_action"] == "complete"
        assert final_state["current_score"] == 85
        assert final_state["current_point_index"] == 1

    def test_lecture_chat_loop(self) -> None:
        """座学中にチャットして、座学に戻る。"""
        runner, _ = _build_graph_and_runner()
        thread_id = "test-coding-002"

        initial_state = {
            "session_id": thread_id,
            "roadmap_item_id": "item-001",
            "roadmap_item_level": "detail",
            "roadmap_item_title": "ジェネリクス",
            "roadmap_item_description": "型パラメータ",
            "is_resumed": False,
        }

        runner.start_graph(initial_state, thread_id=thread_id)

        runner.resume_graph(
            {"user_input": "質問です", "lecture_phase_active": True},
            thread_id=thread_id,
        )

        state = runner.get_state(thread_id=thread_id)
        assert state["chat_response_text"] == "チャット応答テキスト"
        assert state["lecture_phase_active"] is True
