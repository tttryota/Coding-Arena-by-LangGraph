from __future__ import annotations

from typing import Protocol


class ChatResponseError(Exception):
    error_code: str
    message: str

    def __init__(self, *, error_code: str, message: str) -> None:
        super().__init__(message)
        self.error_code = error_code
        self.message = message


class ChatResponseLlmClient(Protocol):
    def generate_chat_response(
        self,
        question_text: str,
        user_input: str,
    ) -> str: ...


__all__ = [
    "ChatResponseError",
    "ChatResponseLlmClient",
]
