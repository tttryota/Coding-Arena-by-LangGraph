from __future__ import annotations

from dataclasses import dataclass
from importlib import import_module
from typing import TYPE_CHECKING, Literal, Protocol

if TYPE_CHECKING:
    from quiz.domain import session_state as session_state_domain
else:
    session_state_domain = import_module("quiz.domain.session_state")

_NextAction = Literal["next", "deepdive", "complete"]


class AnswerEvaluationError(Exception):
    def __init__(self, *, error_code: str, message: str) -> None:
        super().__init__(message)
        self.error_code = error_code
        self.message = message


@dataclass(frozen=True)
class EvaluationOutput:
    next_action: _NextAction
    score: int
    feedback: str
    deepdive_points: list[session_state_domain.ConfirmationPoint]


class AnswerEvaluationLlmClient(Protocol):
    def evaluate_answer(
        self,
        question_text: str,
        confirmation_point_content: str,
        answer_text: str,
        answer_type: session_state_domain.QuizAnswerType,
        past_answers: list[session_state_domain.QuizAnswerRecord],
        total_questions_asked: int,
    ) -> EvaluationOutput: ...


__all__ = [
    "AnswerEvaluationError",
    "AnswerEvaluationLlmClient",
    "EvaluationOutput",
]
