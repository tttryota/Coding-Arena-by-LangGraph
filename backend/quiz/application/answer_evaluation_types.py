from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Literal, Protocol

if TYPE_CHECKING:
    from quiz.domain.session_state import (
        ConfirmationPoint,
        QuizAnswerRecord,
        QuizAnswerType,
    )

_NextAction = Literal["next", "deepdive", "complete"]


class AnswerEvaluationError(Exception):
    error_code: str
    message: str

    def __init__(self, *, error_code: str, message: str) -> None:
        super().__init__(message)
        self.error_code = error_code
        self.message = message


@dataclass(frozen=True)
class EvaluationOutput:
    next_action: _NextAction
    score: int
    feedback: str
    deepdive_points: list[ConfirmationPoint]


class AnswerEvaluationLlmClient(Protocol):
    def evaluate_answer(  # noqa: PLR0913
        self,
        question_text: str,
        confirmation_point_content: str,
        answer_text: str,
        answer_type: QuizAnswerType,
        past_answers: list[QuizAnswerRecord],
        total_questions_asked: int,
    ) -> EvaluationOutput: ...


__all__ = [
    "AnswerEvaluationError",
    "AnswerEvaluationLlmClient",
    "EvaluationOutput",
]
