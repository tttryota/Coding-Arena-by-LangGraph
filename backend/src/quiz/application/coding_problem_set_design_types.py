"""coding_problem_set_design ノードの Protocol 定義。"""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from collections.abc import Sequence

    from quiz.domain.coding_session_state import CodingDifficulty


class CodingConfirmationPointDraftLike(Protocol):
    @property
    def id(self) -> str: ...

    @property
    def content(self) -> str: ...

    @property
    def start_format(self) -> CodingDifficulty: ...

    @property
    def end_format(self) -> CodingDifficulty: ...


class CodingProblemSetDesignResultLike(Protocol):
    @property
    def confirmation_points(self) -> Sequence[CodingConfirmationPointDraftLike]: ...


class CodingProblemSetDesignLlmClient(Protocol):
    def design_problem_set(
        self,
        title: str,
        description: str,
        lecture_content: str,
    ) -> CodingProblemSetDesignResultLike: ...


__all__ = [
    "CodingProblemSetDesignLlmClient",
    "CodingProblemSetDesignResultLike",
]
