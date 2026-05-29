"""競プログラフの統合テスト。

モック LLM でフロー全体を通し、
theme_selection → problem_generation → await_submission → solution_evaluation → END
の一連のフローを検証する。
"""

from __future__ import annotations

from langgraph.checkpoint.memory import MemorySaver

from competitive.domain.competitive_types import ThemeSelectionError

# ---------------------------------------------------------------------------
# Fake dependencies
# ---------------------------------------------------------------------------


class FakeThemeReader:
    def pick_random(self) -> dict[str, str]:
        return {"id": "algo-001", "category": "探索", "label": "二分探索"}

    def get_by_id(self, theme_id: str) -> dict[str, str]:
        if theme_id == "algo-001":
            return {"id": "algo-001", "category": "探索", "label": "二分探索"}
        raise ThemeSelectionError(
            error_code="theme_not_found", message=f"Not found: {theme_id}",
        )


class FakeProblemResult:
    def __init__(self) -> None:
        self.programming_language = "python"
        self.problem_statement = "N個の整数から二分探索で値を見つけよ"
        self.input_format = "1行目にN"
        self.output_format = "インデックス"
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
    def generate_problem(
        self, theme_label: str, theme_category: str,
    ) -> FakeProblemResult:
        return FakeProblemResult()


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
    def evaluate_solution(self, **_kwargs: object) -> FakeEvaluationResult:
        return FakeEvaluationResult()


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def _build_graph_and_runner() -> tuple:
    from competitive.application.competitive_graph import (
        CompetitiveGraphDependencies,
        CompetitiveGraphRunner,
        build_competitive_graph,
    )

    deps = CompetitiveGraphDependencies(
        theme_reader=FakeThemeReader(),
        problem_generation_llm=FakeProblemGenerationLlm(),
        solution_evaluation_llm=FakeSolutionEvaluationLlm(),
    )
    checkpointer = MemorySaver()
    compiled = build_competitive_graph(deps, checkpointer=checkpointer)
    runner = CompetitiveGraphRunner(compiled)
    return runner, compiled


class TestCompetitiveGraphFlow:
    def test_full_flow(self) -> None:
        """theme_selection → problem_generation → interrupt → resume → solution_evaluation → END."""
        runner, _ = _build_graph_and_runner()
        thread_id = "test-session-001"

        runner.start_graph(
            {"session_id": thread_id}, thread_id=thread_id,
        )

        state = runner.get_state(thread_id=thread_id)
        assert state["algo_theme_id"] == "algo-001"
        assert state["problem_statement"] == "N個の整数から二分探索で値を見つけよ"
        assert state["programming_language"] == "python"

        runner.resume_graph(
            {"user_code": "def solve(): return 42"},
            thread_id=thread_id,
        )

        final_state = runner.get_state(thread_id=thread_id)
        assert final_state["status"] == "completed"
        assert final_state["score"] == 85
        assert final_state["feedback"] == "良い解答です"
        assert final_state["time_complexity"] == "O(log N)"

    def test_start_with_specified_theme(self) -> None:
        """テーマ ID を指定して開始。"""
        runner, _ = _build_graph_and_runner()
        thread_id = "test-session-002"

        runner.start_graph(
            {"session_id": thread_id, "algo_theme_id": "algo-001"},
            thread_id=thread_id,
        )

        state = runner.get_state(thread_id=thread_id)
        assert state["algo_theme_id"] == "algo-001"
        assert state["algo_theme_label"] == "二分探索"

    def test_get_state_raises_on_unknown_thread(self) -> None:
        """存在しない thread_id で LookupError が出る。"""
        import pytest

        runner, _ = _build_graph_and_runner()

        with pytest.raises(LookupError):
            runner.get_state(thread_id="nonexistent")

    def test_get_state_raises_on_empty_thread_id(self) -> None:
        """空文字の thread_id で ValueError が出る。"""
        import pytest

        runner, _ = _build_graph_and_runner()

        with pytest.raises(ValueError, match="thread_id must not be empty"):
            runner.get_state(thread_id="")
