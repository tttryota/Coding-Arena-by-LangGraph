from __future__ import annotations

from typing import Literal, Protocol

_InputType = Literal["answer", "question", "explanation_request"]


class InputClassificationError(Exception):
    def __init__(self, *, error_code: str, message: str) -> None:
        super().__init__(message)
        self.error_code = error_code
        self.message = message


class InputClassificationLlmClient(Protocol):
    def classify_input(
        self,
        question_text: str,
        user_input: str,
    ) -> _InputType: ...


__all__ = [
    "InputClassificationError",
    "InputClassificationLlmClient",
]
