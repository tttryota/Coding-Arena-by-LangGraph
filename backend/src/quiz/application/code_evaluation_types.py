"""code_evaluation ノードの Protocol 定義。"""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from quiz.domain.coding_session_state import CodingDifficulty


class CodeEvaluationResultLike(Protocol):
    @property
    def score(self) -> int: ...

    @property
    def feedback(self) -> str: ...


class CodeEvaluationLlmClient(Protocol):
    def evaluate_code(  # noqa: PLR0913
        self,
        question_text: str,
        example_code: str,
        user_code: str,
        current_format: CodingDifficulty,
        confirmation_point_content: str,
    ) -> CodeEvaluationResultLike: ...


__all__ = ["CodeEvaluationLlmClient", "CodeEvaluationResultLike"]
