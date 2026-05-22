from __future__ import annotations

from typing import TYPE_CHECKING, Literal

from quiz.application.answer_evaluation import evaluate_answer
from quiz.application.answer_evaluation_types import EvaluationOutput
from quiz.application.input_classification import classify_input

if TYPE_CHECKING:
    from quiz.domain.session_state import (
        ConfirmationPoint,
        QuizAnswerRecord,
        QuizAnswerType,
        SessionState,
    )


class _RecordingInputClassificationLlm:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str]] = []

    def classify_input(
        self,
        question_text: str,
        user_input: str,
    ) -> Literal["answer", "question", "explanation_request"]:
        self.calls.append((question_text, user_input))
        return "answer"


class _RecordingAnswerEvaluationLlm:
    def __init__(self, *, output: EvaluationOutput) -> None:
        self._output = output
        self.calls: list[
            tuple[str, str, str, QuizAnswerType, list[QuizAnswerRecord], int]
        ] = []

    def evaluate_answer(
        self,
        question_text: str,
        confirmation_point_content: str,
        answer_text: str,
        answer_type: QuizAnswerType,
        past_answers: list[QuizAnswerRecord],
        total_questions_asked: int,
    ) -> EvaluationOutput:
        self.calls.append(
            (
                question_text,
                confirmation_point_content,
                answer_text,
                answer_type,
                past_answers,
                total_questions_asked,
            ),
        )
        return self._output


def _confirmation_points() -> list[ConfirmationPoint]:
    return [
        {
            "id": "cp_001",
            "content": "確認ポイント 1",
            "format": "knowledge",
        },
    ]


def _state(
    *,
    input_source: Literal["chat", "form"],
    input_type: Literal["answer", "question", "explanation_request"] | None = None,
) -> SessionState:
    state: SessionState = {
        "current_question_text": "ジェネリクスが必要な理由を説明してください",
        "current_answer_type": "textarea",
        "user_input": "型安全に共通化するためです",
        "confirmation_points": _confirmation_points(),
        "current_point_index": 0,
        "answers": [],
        "total_questions_asked": 3,
        "input_source": input_source,
    }
    if input_type is not None:
        state["input_type"] = input_type
    return state


def _route_quiz_input(
    state: SessionState,
    *,
    input_classification_llm: _RecordingInputClassificationLlm,
    answer_evaluation_llm: _RecordingAnswerEvaluationLlm,
) -> tuple[str, dict[str, object]]:
    if state["input_source"] == "form":
        return "answer_evaluation", evaluate_answer(state, llm=answer_evaluation_llm)

    classified = classify_input(state, llm=input_classification_llm)
    if classified["input_type"] == "answer":
        evaluated_state: SessionState = {**state}
        evaluated_state["input_type"] = "answer"
        return "answer_evaluation", evaluate_answer(
            evaluated_state,
            llm=answer_evaluation_llm,
        )
    if classified["input_type"] == "question":
        return "chat_response", classified
    return "explanation_generation", classified


def test_tc_02_form_input_routes_directly_to_answer_evaluation_without_classification() -> (
    None
):
    # Arrange
    state = _state(input_source="form", input_type=None)
    input_classification_llm = _RecordingInputClassificationLlm()
    answer_evaluation_llm = _RecordingAnswerEvaluationLlm(
        output=EvaluationOutput(
            next_action="next",
            score=80,
            feedback="十分です。",
            deepdive_points=[],
        ),
    )

    # Act
    destination, result = _route_quiz_input(
        state,
        input_classification_llm=input_classification_llm,
        answer_evaluation_llm=answer_evaluation_llm,
    )

    # Assert
    assert destination == "answer_evaluation"
    assert input_classification_llm.calls == []
    assert len(answer_evaluation_llm.calls) == 1
    assert result["input_type"] == "answer"
