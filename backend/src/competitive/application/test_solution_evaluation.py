"""solution_evaluation ノードのテスト。"""

from __future__ import annotations

import json

import pytest

from competitive.domain.competitive_types import SolutionEvaluationError


class FakeEvaluationResult:
    def __init__(self) -> None:
        self.score = 85
        self.feedback = "良い解答です"
        self.time_complexity = "O(log N)"
        self.space_complexity = "O(1)"
        self.improvement_suggestions = "特になし"
        self.rubric_scores = [
            {"criterion": "正しさ", "points_awarded": 45, "points_max": 50},
            {"criterion": "効率性", "points_awarded": 25, "points_max": 30},
            {"criterion": "可読性", "points_awarded": 15, "points_max": 20},
        ]


class FakeSolutionEvaluationLlm:
    def __init__(self, *, should_fail: bool = False) -> None:
        self._should_fail = should_fail

    def evaluate_solution(self, **_kwargs: object) -> FakeEvaluationResult:
        if self._should_fail:
            raise SolutionEvaluationError(
                error_code="llm_request_failed",
                message="fake failure",
            )
        return FakeEvaluationResult()


_SAMPLE_STATE = {
    "problem_statement": "問題文",
    "input_format": "入力",
    "output_format": "出力",
    "constraints": "制約",
    "examples": [{"input": "1", "output": "2"}],
    "reference_solution": "解答",
    "grading_rubric": [
        {"criterion": "正しさ", "points": 50, "description": "ok"},
    ],
    "user_code": "def solve(): pass",
    "programming_language": "python",
}


class TestEvaluateSolution:
    def test_returns_evaluation_fields(self) -> None:
        from competitive.application.solution_evaluation import (
            evaluate_solution,
        )

        result = evaluate_solution(
            _SAMPLE_STATE, llm=FakeSolutionEvaluationLlm(),
        )

        assert result["status"] == "completed"
        assert result["score"] == 85
        assert result["feedback"] == "良い解答です"
        assert result["time_complexity"] == "O(log N)"
        rubric_scores = json.loads(result["rubric_scores_json"])
        assert len(rubric_scores) == 3
        assert rubric_scores[0]["points_awarded"] == 45

    def test_llm_failure_raises(self) -> None:
        from competitive.application.solution_evaluation import (
            evaluate_solution,
        )

        with pytest.raises(SolutionEvaluationError):
            evaluate_solution(
                _SAMPLE_STATE,
                llm=FakeSolutionEvaluationLlm(should_fail=True),
            )
