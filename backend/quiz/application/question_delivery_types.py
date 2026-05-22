from __future__ import annotations

from dataclasses import dataclass
from importlib import import_module
from typing import TYPE_CHECKING, Literal, Protocol, overload

if TYPE_CHECKING:
    from quiz.domain import session_state as session_state_domain
else:
    session_state_domain = import_module("quiz.domain.session_state")

_KnowledgeConfirmationPointFormat = Literal["knowledge"]
_KnowledgeAndPracticeConfirmationPointFormat = Literal["knowledge_and_practice"]
_ConfirmationPointFormat = Literal["knowledge", "knowledge_and_practice"]
_QuestionAnswerType = Literal["textarea", "code"]


class QuestionDeliveryError(Exception):
    def __init__(self, *, error_code: str, message: str) -> None:
        super().__init__(message)
        self.error_code = error_code
        self.message = message


@dataclass(frozen=True)
class QuestionOutput:
    question_text: str
    answer_type: _QuestionAnswerType


@dataclass(frozen=True)
class KnowledgeQuestionOutput(QuestionOutput):
    answer_type: Literal["textarea"]


@dataclass(frozen=True)
class KnowledgeAndPracticeQuestionOutput(QuestionOutput):
    answer_type: Literal["code"]


class QuestionDeliveryLlmClient(Protocol):
    @overload
    def generate_question(
        self,
        title: str,
        description: str,
        confirmation_point_content: str,
        confirmation_point_format: _KnowledgeConfirmationPointFormat,
        past_answers: list[session_state_domain.QuizAnswerRecord],
    ) -> QuestionOutput: ...

    @overload
    def generate_question(
        self,
        title: str,
        description: str,
        confirmation_point_content: str,
        confirmation_point_format: _KnowledgeAndPracticeConfirmationPointFormat,
        past_answers: list[session_state_domain.QuizAnswerRecord],
    ) -> QuestionOutput: ...

    @overload
    def generate_question(
        self,
        title: str,
        description: str,
        confirmation_point_content: str,
        confirmation_point_format: _ConfirmationPointFormat,
        past_answers: list[session_state_domain.QuizAnswerRecord],
    ) -> QuestionOutput: ...

    def generate_question(  # noqa: PLR0913
        self,
        title: str,
        description: str,
        confirmation_point_content: str,
        confirmation_point_format: _ConfirmationPointFormat,
        past_answers: list[session_state_domain.QuizAnswerRecord],
    ) -> QuestionOutput: ...


__all__ = [
    "QuestionDeliveryError",
    "QuestionDeliveryLlmClient",
    "QuestionOutput",
]
