"""競プロ LLM アダプタのテスト。

FakeTransport で canned response を返し、
プロンプト構築とレスポンスパースの正当性を検証する。
"""

from __future__ import annotations

import json
from dataclasses import dataclass

import pytest

from competitive.domain.competitive_types import (
    ProblemGenerationError,
    QuestionResponseError,
    SolutionEvaluationError,
)


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
# CodexCompetitiveProblemGenerationLlm
# ---------------------------------------------------------------------------

_VALID_PROBLEM_RESPONSE = json.dumps(
    {
        "problem_statement": "N個の整数から二分探索で値を見つけよ",
        "input_format": "1行目にN、2行目にN個の整数、3行目に探索値",
        "output_format": "見つかった場合はインデックス、なければ-1",
        "constraints": "1 <= N <= 100000",
        "examples": [
            {"input": "5\n1 3 5 7 9\n5", "output": "2"},
            {"input": "3\n1 2 3\n4", "output": "-1"},
        ],
        "reference_solution": "def solve():\n    pass",
        "grading_rubric": [
            {"criterion": "正しさ", "points": 50, "description": "正しい結果を返す"},
            {"criterion": "効率性", "points": 30, "description": "O(log N)"},
            {"criterion": "可読性", "points": 20, "description": "変数名など"},
        ],
    },
)


class TestCodexCompetitiveProblemGenerationLlm:
    def test_returns_problem_generation_result(self) -> None:
        from competitive.infrastructure.codex_competitive_llm import (
            CodexCompetitiveProblemGenerationLlm,
        )

        transport = FakeTransport(_VALID_PROBLEM_RESPONSE)
        adapter = CodexCompetitiveProblemGenerationLlm(transport)

        result = adapter.generate_problem("二分探索", "探索", "python")

        assert result.programming_language == "python"
        assert result.problem_statement == "N個の整数から二分探索で値を見つけよ"
        assert len(result.examples) == 2
        assert result.examples[0]["input"] == "5\n1 3 5 7 9\n5"
        assert len(result.grading_rubric) == 3
        assert result.grading_rubric[0]["points"] == 50

    def test_prompt_contains_theme_and_language(self) -> None:
        from competitive.infrastructure.codex_competitive_llm import (
            CodexCompetitiveProblemGenerationLlm,
        )

        transport = FakeTransport(_VALID_PROBLEM_RESPONSE)
        adapter = CodexCompetitiveProblemGenerationLlm(transport)

        adapter.generate_problem("ダイクストラ法", "グラフ", "typescript")

        user_msg = transport.last_messages[-1].content
        assert "ダイクストラ法" in user_msg
        assert "グラフ" in user_msg
        assert "typescript" in user_msg

    def test_insufficient_examples_raises(self) -> None:
        from competitive.infrastructure.codex_competitive_llm import (
            CodexCompetitiveProblemGenerationLlm,
        )

        bad_response = json.dumps(
            {
                "problem_statement": "問題",
                "input_format": "入力",
                "output_format": "出力",
                "constraints": "制約",
                "examples": [{"input": "1", "output": "2"}],
                "reference_solution": "code",
                "grading_rubric": [
                    {"criterion": "正しさ", "points": 40, "description": "ok"},
                    {"criterion": "効率性", "points": 30, "description": "ok"},
                    {"criterion": "可読性", "points": 30, "description": "ok"},
                ],
            },
        )
        transport = FakeTransport(bad_response)
        adapter = CodexCompetitiveProblemGenerationLlm(transport)

        with pytest.raises(ProblemGenerationError) as exc_info:
            adapter.generate_problem("テスト", "テスト", "python")
        assert exc_info.value.error_code == "llm_response_parse_failed"

    def test_insufficient_rubric_raises(self) -> None:
        from competitive.infrastructure.codex_competitive_llm import (
            CodexCompetitiveProblemGenerationLlm,
        )

        bad_response = json.dumps(
            {
                "problem_statement": "問題",
                "input_format": "入力",
                "output_format": "出力",
                "constraints": "制約",
                "examples": [
                    {"input": "1", "output": "2"},
                    {"input": "3", "output": "4"},
                ],
                "reference_solution": "code",
                "grading_rubric": [
                    {"criterion": "正しさ", "points": 50, "description": "ok"},
                    {"criterion": "効率性", "points": 50, "description": "ok"},
                ],
            },
        )
        transport = FakeTransport(bad_response)
        adapter = CodexCompetitiveProblemGenerationLlm(transport)

        with pytest.raises(ProblemGenerationError) as exc_info:
            adapter.generate_problem("テスト", "テスト", "python")
        assert exc_info.value.error_code == "llm_response_parse_failed"

    def test_invalid_json_raises(self) -> None:
        from competitive.infrastructure.codex_competitive_llm import (
            CodexCompetitiveProblemGenerationLlm,
        )

        transport = FakeTransport("not json")
        adapter = CodexCompetitiveProblemGenerationLlm(transport)

        with pytest.raises(ProblemGenerationError) as exc_info:
            adapter.generate_problem("テスト", "テスト", "python")
        assert exc_info.value.error_code == "llm_response_parse_failed"

    def test_rubric_points_not_100_raises(self) -> None:
        from competitive.infrastructure.codex_competitive_llm import (
            CodexCompetitiveProblemGenerationLlm,
        )

        bad_response = json.dumps(
            {
                "problem_statement": "問題",
                "input_format": "入力",
                "output_format": "出力",
                "constraints": "制約",
                "examples": [
                    {"input": "1", "output": "2"},
                    {"input": "3", "output": "4"},
                ],
                "reference_solution": "code",
                "grading_rubric": [
                    {"criterion": "正しさ", "points": 30, "description": "ok"},
                    {"criterion": "効率性", "points": 30, "description": "ok"},
                    {"criterion": "可読性", "points": 30, "description": "ok"},
                ],
            },
        )
        transport = FakeTransport(bad_response)
        adapter = CodexCompetitiveProblemGenerationLlm(transport)

        with pytest.raises(ProblemGenerationError) as exc_info:
            adapter.generate_problem("テスト", "テスト", "python")
        assert exc_info.value.error_code == "llm_response_parse_failed"

    def test_markdown_wrapped_json_is_parsed(self) -> None:
        from competitive.infrastructure.codex_competitive_llm import (
            CodexCompetitiveProblemGenerationLlm,
        )

        wrapped = f"```json\n{_VALID_PROBLEM_RESPONSE}\n```"
        transport = FakeTransport(wrapped)
        adapter = CodexCompetitiveProblemGenerationLlm(transport)

        result = adapter.generate_problem("二分探索", "探索", "python")

        assert result.problem_statement == "N個の整数から二分探索で値を見つけよ"


# ---------------------------------------------------------------------------
# CodexCompetitiveSolutionEvaluationLlm
# ---------------------------------------------------------------------------

_VALID_EVAL_RESPONSE = json.dumps(
    {
        "score": 85,
        "feedback": "正しく動作していますが、変数名を改善できます",
        "time_complexity": "O(log N)",
        "space_complexity": "O(1)",
        "improvement_suggestions": "変数名をより意味のあるものに",
        "rubric_scores": [
            {"criterion": "正しさ", "points_awarded": 45, "points_max": 50},
            {"criterion": "効率性", "points_awarded": 25, "points_max": 30},
            {"criterion": "可読性", "points_awarded": 15, "points_max": 20},
        ],
    },
)

_SAMPLE_RUBRIC = [
    {"criterion": "正しさ", "points": 50, "description": "正しい結果を返す"},
    {"criterion": "効率性", "points": 30, "description": "O(log N)"},
    {"criterion": "可読性", "points": 20, "description": "変数名など"},
]


class TestCodexCompetitiveSolutionEvaluationLlm:
    def test_returns_evaluation_result(self) -> None:
        from competitive.infrastructure.codex_competitive_llm import (
            CodexCompetitiveSolutionEvaluationLlm,
        )

        transport = FakeTransport(_VALID_EVAL_RESPONSE)
        adapter = CodexCompetitiveSolutionEvaluationLlm(transport)

        result = adapter.evaluate_solution(
            problem_statement="二分探索の問題",
            input_format="入力形式",
            output_format="出力形式",
            constraints="1 <= N <= 100000",
            examples=[{"input": "5\n1 3 5 7 9\n5", "output": "2"}],
            reference_solution="def solve(): pass",
            grading_rubric=_SAMPLE_RUBRIC,
            user_code="def solve(): return -1",
            programming_language="python",
        )

        assert result.score == 85
        assert "正しく動作" in result.feedback
        assert result.time_complexity == "O(log N)"
        assert result.space_complexity == "O(1)"
        assert len(result.rubric_scores) == 3
        assert result.rubric_scores[0]["criterion"] == "正しさ"
        assert result.rubric_scores[0]["points_awarded"] == 45

    def test_prompt_contains_rubric_and_code(self) -> None:
        from competitive.infrastructure.codex_competitive_llm import (
            CodexCompetitiveSolutionEvaluationLlm,
        )

        transport = FakeTransport(_VALID_EVAL_RESPONSE)
        adapter = CodexCompetitiveSolutionEvaluationLlm(transport)

        adapter.evaluate_solution(
            problem_statement="問題文",
            input_format="入力形式",
            output_format="出力形式",
            constraints="制約",
            examples=[{"input": "1", "output": "2"}],
            reference_solution="模範解答",
            grading_rubric=_SAMPLE_RUBRIC,
            user_code="user code here",
            programming_language="typescript",
        )

        system_msg = transport.last_messages[0].content
        assert "正しさ" in system_msg
        assert "50" in system_msg

        user_msg = transport.last_messages[-1].content
        assert "user code here" in user_msg
        assert "typescript" in user_msg
        assert "入力形式" in user_msg
        assert "出力形式" in user_msg
        assert "制約" in user_msg

    def test_score_out_of_range_raises(self) -> None:
        from competitive.infrastructure.codex_competitive_llm import (
            CodexCompetitiveSolutionEvaluationLlm,
        )

        bad_response = json.dumps(
            {
                "score": 150,
                "feedback": "ok",
                "time_complexity": "O(1)",
                "space_complexity": "O(1)",
                "improvement_suggestions": "none",
                "rubric_scores": [
                    {"criterion": "正しさ", "points_awarded": 50, "points_max": 50},
                    {"criterion": "効率性", "points_awarded": 30, "points_max": 30},
                    {"criterion": "可読性", "points_awarded": 20, "points_max": 20},
                ],
            },
        )
        transport = FakeTransport(bad_response)
        adapter = CodexCompetitiveSolutionEvaluationLlm(transport)

        with pytest.raises(SolutionEvaluationError) as exc_info:
            adapter.evaluate_solution(
                problem_statement="問題",
                input_format="入力",
                output_format="出力",
                constraints="制約",
                examples=[{"input": "1", "output": "2"}],
                reference_solution="解答",
                grading_rubric=_SAMPLE_RUBRIC,
                user_code="code",
                programming_language="python",
            )
        assert exc_info.value.error_code == "llm_response_parse_failed"


_VALID_QUESTION_RESPONSE = json.dumps(
    {
        "chat_response_text": "制約を見ると O(N log N) 以内を意識するとよいです。",
    },
)


class TestCodexCompetitiveQuestionResponseLlm:
    def test_pre_submit_prompt_blocks_direct_solution(self) -> None:
        from competitive.infrastructure.codex_competitive_llm import (
            CodexCompetitiveQuestionResponseLlm,
        )

        transport = FakeTransport(_VALID_QUESTION_RESPONSE)
        adapter = CodexCompetitiveQuestionResponseLlm(transport)

        result = adapter.generate_chat_response(
            problem_statement="問題文",
            input_format="入力形式",
            output_format="出力形式",
            constraints="制約",
            examples=[{"input": "1", "output": "2"}],
            programming_language="python",
            user_input="どこから考えるべき？",
            history=[{"role": "user", "content": "制約が厳しい？"}],
        )

        assert "O(N log N)" in result
        system_msg = transport.last_messages[0].content
        user_msg = transport.last_messages[-1].content
        assert "正解コード" in system_msg
        assert "避けてください" in system_msg
        assert "模範解答" not in user_msg
        assert "制約が厳しい？" in user_msg

    def test_invalid_json_raises(self) -> None:
        from competitive.infrastructure.codex_competitive_llm import (
            CodexCompetitiveQuestionResponseLlm,
        )

        transport = FakeTransport("not json")
        adapter = CodexCompetitiveQuestionResponseLlm(transport)

        with pytest.raises(QuestionResponseError) as exc_info:
            adapter.generate_chat_response(
                problem_statement="問題文",
                input_format="入力形式",
                output_format="出力形式",
                constraints="制約",
                examples=[{"input": "1", "output": "2"}],
                programming_language="python",
                user_input="ヒントは？",
                history=[],
            )
        assert exc_info.value.error_code == "llm_response_parse_failed"

    def test_missing_field_raises(self) -> None:
        from competitive.infrastructure.codex_competitive_llm import (
            CodexCompetitiveSolutionEvaluationLlm,
        )

        bad_response = json.dumps(
            {
                "score": 50,
                "feedback": "ok",
            },
        )
        transport = FakeTransport(bad_response)
        adapter = CodexCompetitiveSolutionEvaluationLlm(transport)

        with pytest.raises(SolutionEvaluationError) as exc_info:
            adapter.evaluate_solution(
                problem_statement="問題",
                input_format="入力",
                output_format="出力",
                constraints="制約",
                examples=[{"input": "1", "output": "2"}],
                reference_solution="解答",
                grading_rubric=_SAMPLE_RUBRIC,
                user_code="code",
                programming_language="python",
            )
        assert exc_info.value.error_code == "llm_response_parse_failed"
