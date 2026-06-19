"""競プロ質問応答の Protocol 定義。"""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, TypedDict

if TYPE_CHECKING:
    from competitive.domain.competitive_types import (
        ProblemExample,
        ProgrammingLanguage,
    )


class CompetitiveChatMessage(TypedDict):
    """競プロ質問 API が受け取るローカル会話履歴。"""

    role: str
    content: str


class QuestionResponseLlmClient(Protocol):
    """競プロ問題への質問に答える LLM クライアント。"""

    def generate_chat_response(  # noqa: PLR0913
        self,
        *,
        problem_statement: str,
        input_format: str,
        output_format: str,
        constraints: str,
        examples: list[ProblemExample],
        programming_language: ProgrammingLanguage,
        user_input: str,
        history: list[CompetitiveChatMessage],
    ) -> str: ...


__all__ = [
    "CompetitiveChatMessage",
    "QuestionResponseLlmClient",
]
