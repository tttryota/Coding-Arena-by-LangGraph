"""solution_evaluation ノードの Protocol 定義。"""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from collections.abc import Sequence

    from competitive.domain.competitive_types import (
        ProblemExample,
        ProgrammingLanguage,
        RubricItem,
    )


class RubricScoreItemLike(Protocol):
    """rubric 項目別得点のインターフェース。"""

    @property
    def criterion(self) -> str: ...

    @property
    def points_awarded(self) -> int: ...

    @property
    def points_max(self) -> int: ...


class SolutionEvaluationResult(Protocol):
    """採点結果のインターフェース。"""

    @property
    def score(self) -> int: ...

    @property
    def feedback(self) -> str: ...

    @property
    def time_complexity(self) -> str: ...

    @property
    def space_complexity(self) -> str: ...

    @property
    def improvement_suggestions(self) -> str: ...

    @property
    def rubric_scores(self) -> Sequence[RubricScoreItemLike]: ...


class SolutionEvaluationLlmClient(Protocol):
    """保存済み rubric ベース採点のインターフェース。"""

    def evaluate_solution(  # noqa: PLR0913
        self,
        *,
        problem_statement: str,
        input_format: str,
        output_format: str,
        constraints: str,
        examples: list[ProblemExample],
        reference_solution: str,
        grading_rubric: list[RubricItem],
        user_code: str,
        programming_language: ProgrammingLanguage,
        allowed_knowledge: list[str] | None = None,
        forbidden_knowledge: list[str] | None = None,
    ) -> SolutionEvaluationResult: ...


__all__ = [
    "SolutionEvaluationLlmClient",
    "SolutionEvaluationResult",
]
