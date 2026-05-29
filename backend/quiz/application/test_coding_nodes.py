"""コーディングセッション用グラフノードの単体テスト。"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# Fake LLM clients
# ---------------------------------------------------------------------------


class FakeLectureResult:
    lecture_content = "ジェネリクスの座学テキスト"


class FakeLectureGenerationLlm:
    def generate_lecture(self, title: str, description: str) -> FakeLectureResult:
        return FakeLectureResult()


class FakeLectureChatResponseLlm:
    def generate_chat_response(self, lecture_content: str, user_input: str) -> str:
        return "型パラメータについて説明します。"


class FakeCPDraft:
    def __init__(self, cp_id: str, content: str, start: str, end: str) -> None:
        self.id = cp_id
        self.content = content
        self.start_format = start
        self.end_format = end


class FakeProblemSetResult:
    def __init__(self) -> None:
        self.confirmation_points = [
            FakeCPDraft("cp-001", "基本型パラメータ", "rewrite", "fill_blank"),
            FakeCPDraft("cp-002", "制約付きジェネリクス", "fill_blank", "implement"),
            FakeCPDraft("cp-003", "実用パターン", "bug_fix", "implement"),
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


class FakeEvalResult:
    def __init__(self, score: int = 80) -> None:
        self.score = score
        self.feedback = "良い解答です"


class FakeCodeEvaluationLlm:
    def __init__(self, score: int = 80) -> None:
        self._score = score

    def evaluate_code(self, **_kwargs: object) -> FakeEvalResult:
        return FakeEvalResult(self._score)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestLectureGeneration:
    def test_returns_lecture_content(self) -> None:
        from quiz.application.lecture_generation import generate_lecture

        state = {
            "roadmap_item_title": "ジェネリクス",
            "roadmap_item_description": "型パラメータの基礎",
        }
        result = generate_lecture(state, llm=FakeLectureGenerationLlm())
        assert result["lecture_content"] == "ジェネリクスの座学テキスト"
        assert result["lecture_phase_active"] is True


class TestLectureChatResponse:
    def test_returns_chat_response(self) -> None:
        from quiz.application.lecture_chat_response import (
            respond_to_lecture_chat,
        )

        state = {
            "lecture_content": "座学テキスト",
            "user_input": "質問",
        }
        result = respond_to_lecture_chat(
            state, llm=FakeLectureChatResponseLlm(),
        )
        assert "型パラメータ" in result["chat_response_text"]


class TestCodingProblemSetDesign:
    def test_returns_confirmation_points(self) -> None:
        from quiz.application.coding_problem_set_design import (
            design_coding_problem_set,
        )

        state = {
            "roadmap_item_title": "ジェネリクス",
            "roadmap_item_description": "型パラメータ",
            "lecture_content": "座学テキスト",
        }
        result = design_coding_problem_set(
            state, llm=FakeProblemSetDesignLlm(),
        )
        assert len(result["confirmation_points"]) == 3
        assert result["current_point_index"] == 0
        assert result["total_questions_asked"] == 0
        assert result["coding_attempts"] == []


class TestCodingProblemDelivery:
    def test_returns_question_and_code(self) -> None:
        from quiz.application.coding_problem_delivery import (
            deliver_coding_problem,
        )

        state = {
            "roadmap_item_title": "ジェネリクス",
            "lecture_content": "座学",
            "confirmation_points": [
                {
                    "id": "cp-001",
                    "content": "基本",
                    "start_format": "rewrite",
                    "end_format": "fill_blank",
                },
            ],
            "current_point_index": 0,
            "total_questions_asked": 0,
        }
        result = deliver_coding_problem(
            state, llm=FakeProblemDeliveryLlm(),
        )
        assert result["current_question_text"] == "この関数の戻り値を変更してください"
        assert result["current_example_code"] == "def greet(): return 'hello'"
        assert result["total_questions_asked"] == 1


class TestCodeEvaluation:
    def test_next_step_on_high_score(self) -> None:
        from quiz.application.code_evaluation import evaluate_code

        state = {
            "confirmation_points": [
                {
                    "id": "cp-001",
                    "content": "基本",
                    "start_format": "rewrite",
                    "end_format": "implement",
                },
            ],
            "current_point_index": 0,
            "current_format": "rewrite",
            "current_question_text": "問題",
            "current_example_code": "コード",
            "user_input": "回答",
            "total_questions_asked": 1,
        }
        result = evaluate_code(state, llm=FakeCodeEvaluationLlm(score=80))
        assert result["next_action"] == "next_step"
        assert result["current_score"] == 80
        assert result["current_format"] == "fill_blank"

    def test_next_cp_when_end_format_reached(self) -> None:
        from quiz.application.code_evaluation import evaluate_code

        state = {
            "confirmation_points": [
                {
                    "id": "cp-001",
                    "content": "基本",
                    "start_format": "rewrite",
                    "end_format": "rewrite",
                },
                {
                    "id": "cp-002",
                    "content": "応用",
                    "start_format": "fill_blank",
                    "end_format": "implement",
                },
            ],
            "current_point_index": 0,
            "current_format": "rewrite",
            "current_question_text": "問題",
            "user_input": "回答",
            "total_questions_asked": 1,
        }
        result = evaluate_code(state, llm=FakeCodeEvaluationLlm(score=80))
        assert result["next_action"] == "next_cp"
        assert result["current_point_index"] == 1
        assert result["current_format"] == "fill_blank"

    def test_complete_when_last_cp(self) -> None:
        from quiz.application.code_evaluation import evaluate_code

        state = {
            "confirmation_points": [
                {
                    "id": "cp-001",
                    "content": "唯一のCP",
                    "start_format": "rewrite",
                    "end_format": "rewrite",
                },
            ],
            "current_point_index": 0,
            "current_format": "rewrite",
            "current_question_text": "問題",
            "user_input": "回答",
            "total_questions_asked": 1,
        }
        result = evaluate_code(state, llm=FakeCodeEvaluationLlm(score=80))
        assert result["next_action"] == "complete"

    def test_convergence_rule_at_20_questions(self) -> None:
        from quiz.application.code_evaluation import evaluate_code

        state = {
            "confirmation_points": [
                {
                    "id": "cp-001",
                    "content": "基本",
                    "start_format": "rewrite",
                    "end_format": "implement",
                },
            ],
            "current_point_index": 0,
            "current_format": "rewrite",
            "current_question_text": "問題",
            "user_input": "回答",
            "total_questions_asked": 20,
        }
        result = evaluate_code(state, llm=FakeCodeEvaluationLlm(score=80))
        assert result["next_action"] == "complete"

    def test_retry_on_low_score(self) -> None:
        from quiz.application.code_evaluation import evaluate_code

        state = {
            "confirmation_points": [
                {
                    "id": "cp-001",
                    "content": "基本",
                    "start_format": "rewrite",
                    "end_format": "implement",
                },
            ],
            "current_point_index": 0,
            "current_format": "rewrite",
            "current_question_text": "問題",
            "user_input": "回答",
            "total_questions_asked": 1,
            "coding_attempts": [],
        }
        result = evaluate_code(state, llm=FakeCodeEvaluationLlm(score=40))
        assert result["next_action"] == "retry"
