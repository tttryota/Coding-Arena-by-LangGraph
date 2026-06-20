"""problem_generation ノードの Protocol 定義。"""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from competitive.domain.competitive_types import ProblemExample, RubricItem


class ProblemGenerationResult(Protocol):
    """問題生成結果のインターフェース。"""

    @property
    def programming_language(self) -> str: ...

    @property
    def problem_statement(self) -> str: ...

    @property
    def input_format(self) -> str: ...

    @property
    def output_format(self) -> str: ...

    @property
    def constraints(self) -> str: ...

    @property
    def examples(self) -> list[ProblemExample]: ...

    @property
    def reference_solution(self) -> str: ...

    @property
    def grading_rubric(self) -> list[RubricItem]: ...


class ProblemGenerationLlmClient(Protocol):
    """問題 + 模範解答 + rubric 同時生成のインターフェース。"""

    def generate_problem(
        self,
        theme_label: str,
        theme_category: str,
        programming_language: str,
    ) -> ProblemGenerationResult: ...


__all__ = ["ProblemGenerationLlmClient", "ProblemGenerationResult"]
