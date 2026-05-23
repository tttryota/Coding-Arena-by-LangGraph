from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from quiz.domain.session_state import QuizAnswerRecord


class SummaryTestRecordError(Exception):
    error_code: str
    message: str

    def __init__(self, *, error_code: str, message: str) -> None:
        super().__init__(message)
        self.error_code = error_code
        self.message = message


@dataclass(frozen=True)
class SummaryAnalysis:
    score: int
    analysis: str


class SummaryTestLlmClient(Protocol):
    def analyze_session(
        self,
        title: str,
        description: str,
        answers: list[QuizAnswerRecord],
    ) -> SummaryAnalysis: ...


class SummaryTestStore(Protocol):
    def save_result(
        self,
        session_id: str,
        roadmap_item_id: str,
        score: int,
        analysis: str,
    ) -> None: ...


__all__ = [
    "SummaryAnalysis",
    "SummaryTestLlmClient",
    "SummaryTestRecordError",
    "SummaryTestStore",
]
