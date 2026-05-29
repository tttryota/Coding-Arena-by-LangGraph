"""problem_generation ノードのテスト。"""

from __future__ import annotations

import pytest

from competitive.domain.competitive_types import ProblemGenerationError


class FakeProblemResult:
    def __init__(self) -> None:
        self.programming_language = "python"
        self.problem_statement = "二分探索で値を見つけよ"
        self.input_format = "入力形式"
        self.output_format = "出力形式"
        self.constraints = "1 <= N <= 100000"
        self.examples = [
            {"input": "5\n1 3 5 7 9\n5", "output": "2"},
            {"input": "3\n1 2 3\n4", "output": "-1"},
        ]
        self.reference_solution = "def solve(): pass"
        self.grading_rubric = [
            {"criterion": "正しさ", "points": 50, "description": "ok"},
            {"criterion": "効率性", "points": 30, "description": "ok"},
            {"criterion": "可読性", "points": 20, "description": "ok"},
        ]


class FakeProblemGenerationLlm:
    def __init__(self, *, should_fail: bool = False) -> None:
        self._should_fail = should_fail

    def generate_problem(
        self, theme_label: str, theme_category: str,
    ) -> FakeProblemResult:
        if self._should_fail:
            raise ProblemGenerationError(
                error_code="llm_request_failed",
                message="fake failure",
            )
        return FakeProblemResult()


class TestGenerateProblem:
    def test_returns_problem_fields(self) -> None:
        from competitive.application.problem_generation import generate_problem

        state = {
            "algo_theme_label": "二分探索",
            "algo_theme_category": "探索",
        }
        result = generate_problem(state, llm=FakeProblemGenerationLlm())

        assert result["programming_language"] == "python"
        assert result["problem_statement"] == "二分探索で値を見つけよ"
        assert len(result["examples"]) == 2
        assert len(result["grading_rubric"]) == 3
        assert result["reference_solution"] == "def solve(): pass"

    def test_llm_failure_raises(self) -> None:
        from competitive.application.problem_generation import generate_problem

        state = {
            "algo_theme_label": "テスト",
            "algo_theme_category": "テスト",
        }

        with pytest.raises(ProblemGenerationError):
            generate_problem(
                state, llm=FakeProblemGenerationLlm(should_fail=True),
            )
