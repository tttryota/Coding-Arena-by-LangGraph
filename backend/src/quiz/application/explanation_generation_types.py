from __future__ import annotations

from typing import Protocol


class ExplanationGenerationError(Exception):
    error_code: str
    message: str

    def __init__(self, *, error_code: str, message: str) -> None:
        super().__init__(message)
        self.error_code = error_code
        self.message = message


class ExplanationRagClient(Protocol):
    def search_related_chunks(self, query: str) -> list[str]: ...


class ExplanationLlmClient(Protocol):
    def generate_explanation(
        self,
        question_text: str,
        confirmation_point_content: str,
        note_chunks: list[str],
    ) -> str: ...


__all__ = [
    "ExplanationGenerationError",
    "ExplanationLlmClient",
    "ExplanationRagClient",
]
