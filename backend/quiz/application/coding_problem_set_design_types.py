"""coding_problem_set_design ノードの Protocol 定義。"""

from __future__ import annotations

from typing import Protocol


class CodingConfirmationPointDraftLike(Protocol):
    @property
    def id(self) -> str: ...

    @property
    def content(self) -> str: ...

    @property
    def start_format(self) -> str: ...

    @property
    def end_format(self) -> str: ...


class CodingProblemSetDesignResultLike(Protocol):
    @property
    def confirmation_points(self) -> list[CodingConfirmationPointDraftLike]: ...


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
