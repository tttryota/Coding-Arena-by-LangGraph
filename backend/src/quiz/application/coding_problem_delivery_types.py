"""coding_problem_delivery ノードの Protocol 定義。"""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from quiz.domain.coding_session_state import CodingDifficulty


class CodingProblemDeliveryResultLike(Protocol):
    @property
    def question_text(self) -> str: ...

    @property
    def example_code(self) -> str: ...


class CodingProblemDeliveryLlmClient(Protocol):
    def deliver_problem(
        self,
        title: str,
        confirmation_point_content: str,
        current_format: CodingDifficulty,
        lecture_content: str,
    ) -> CodingProblemDeliveryResultLike: ...


__all__ = [
    "CodingProblemDeliveryLlmClient",
    "CodingProblemDeliveryResultLike",
]
