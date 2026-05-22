from __future__ import annotations

from typing import TYPE_CHECKING, Literal, cast

import pytest
from structlog.testing import capture_logs

from quiz.application.answer_evaluation import evaluate_answer
from quiz.application.answer_evaluation_types import (
    AnswerEvaluationError,
    EvaluationOutput,
)
from shared.log_assertions import find_log_events

if TYPE_CHECKING:
    from quiz.domain.session_state import (
        ConfirmationPoint,
        ConfirmationPointFormat,
        QuizAnswerRecord,
        QuizAnswerType,
        SessionState,
    )


_FAILED_EVENT = "answer_evaluation_failed"


class _RecordingAnswerEvaluationLlm:
    def __init__(
        self,
        *,
        output: EvaluationOutput | None = None,
        error: AnswerEvaluationError | None = None,
    ) -> None:
        self._output = output
        self._error = error
        self.calls: list[
            tuple[
                str,
                str,
                str,
                QuizAnswerType,
                list[QuizAnswerRecord],
                int,
            ]
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
        if self._error is not None:
            raise self._error
        assert self._output is not None
        return self._output


def _confirmation_points(
    *formats: ConfirmationPointFormat,
) -> list[ConfirmationPoint]:
    return [
        {
            "id": f"cp_{index:03d}",
            "content": f"確認ポイント {index}",
            "format": format_name,
        }
        for index, format_name in enumerate(formats, start=1)
    ]


def _answers() -> list[QuizAnswerRecord]:
    return [
        {
            "question_number": 1,
            "confirmation_point_id": "cp_001",
            "question_text": "ジェネリクスが必要な理由を説明してください。",
            "answer_type": "textarea",
            "answer_text": "型安全に再利用するためです。",
            "score": 70,
            "feedback": "型推論への言及があるとより良いです。",
        },
    ]


def _state(
    *,
    confirmation_points: list[ConfirmationPoint],
    current_point_index: int = 0,
    answers: list[QuizAnswerRecord] | None = None,
    total_questions_asked: int = 3,
    input_source: Literal["chat", "form"] = "chat",
    input_type: Literal["answer"] | None = "answer",
) -> SessionState:
    state: SessionState = {
        "current_question_text": "型引数を明示する理由を説明してください。",
        "current_answer_type": "textarea",
        "user_input": "呼び出し側の意図を明確にできるからです。",
        "confirmation_points": confirmation_points,
        "current_point_index": current_point_index,
        "answers": [] if answers is None else answers,
        "total_questions_asked": total_questions_asked,
        "input_source": input_source,
    }
    if input_type is not None:
        state["input_type"] = input_type
    return state


def _answer_evaluation_error(
    *,
    error_code: str,
    message: str,
    cause: Exception,
) -> AnswerEvaluationError:
    error = AnswerEvaluationError(error_code=error_code, message=message)
    error.__cause__ = cause
    return error


def test_tc_01_evaluate_answer_public_return_contract_and_llm_argument_mapping() -> (
    None
):
    # Arrange
    state = _state(confirmation_points=_confirmation_points("knowledge"))
    llm_client = _RecordingAnswerEvaluationLlm(
        output=EvaluationOutput(
            next_action="next",
            score=88,
            feedback="型推論との関係まで触れられるとさらに良いです。",
            deepdive_points=[],
        ),
    )

    # Act
    result = evaluate_answer(state, llm=llm_client)

    # Assert
    assert llm_client.calls == [
        (
            "型引数を明示する理由を説明してください。",
            "確認ポイント 1",
            "呼び出し側の意図を明確にできるからです。",
            "textarea",
            [],
            3,
        ),
    ]
    assert llm_client.calls[0][4] is state["answers"]
    assert set(result) == {
        "next_action",
        "answers",
        "current_point_index",
        "confirmation_points",
        "input_type",
    }
    assert "score" not in result
    assert "feedback" not in result
    assert result["next_action"] == "next"
    assert result["current_point_index"] == 1
    assert result["confirmation_points"] == state["confirmation_points"]
    assert result["input_type"] == "answer"
    recorded_answers = cast("list[QuizAnswerRecord]", result["answers"])
    assert len(recorded_answers) == 1
    latest_answer = recorded_answers[-1]
    assert type(latest_answer["question_number"]) is int
    assert latest_answer["confirmation_point_id"] == "cp_001"
    assert latest_answer["question_text"] == state["current_question_text"]
    assert latest_answer["answer_type"] == state["current_answer_type"]
    assert latest_answer["answer_text"] == state["user_input"]
    assert latest_answer["score"] == 88
    assert latest_answer["feedback"] == "型推論との関係まで触れられるとさらに良いです。"


def test_tc_02_appends_one_quiz_answer_record_without_reordering_existing_answers() -> (
    None
):
    # Arrange
    existing_answers = _answers()
    state = _state(
        confirmation_points=_confirmation_points("knowledge", "knowledge_and_practice"),
        answers=existing_answers,
    )
    llm_client = _RecordingAnswerEvaluationLlm(
        output=EvaluationOutput(
            next_action="next",
            score=91,
            feedback="追加説明が具体的です。",
            deepdive_points=[],
        ),
    )

    # Act
    result = evaluate_answer(state, llm=llm_client)

    # Assert
    recorded_answers = cast("list[QuizAnswerRecord]", result["answers"])
    assert len(recorded_answers) == len(existing_answers) + 1
    assert recorded_answers[:-1] == existing_answers
    assert recorded_answers[-1]["confirmation_point_id"] == "cp_001"
    assert recorded_answers[-1]["question_text"] == state["current_question_text"]
    assert recorded_answers[-1]["answer_type"] == state["current_answer_type"]
    assert recorded_answers[-1]["answer_text"] == state["user_input"]
    assert recorded_answers[-1]["score"] == 91
    assert recorded_answers[-1]["feedback"] == "追加説明が具体的です。"


def test_tc_10_next_action_next_increments_current_point_index_by_one() -> None:
    # Arrange
    confirmation_points = _confirmation_points(
        "knowledge",
        "knowledge_and_practice",
        "knowledge",
    )
    state = _state(
        confirmation_points=confirmation_points,
        current_point_index=1,
    )
    llm_client = _RecordingAnswerEvaluationLlm(
        output=EvaluationOutput(
            next_action="next",
            score=82,
            feedback="十分に説明できています。",
            deepdive_points=[],
        ),
    )

    # Act
    result = evaluate_answer(state, llm=llm_client)

    # Assert
    assert result["next_action"] == "next"
    assert result["current_point_index"] == 2
    assert result["confirmation_points"] == confirmation_points


def test_tc_11_deepdive_appends_points_to_tail_and_increments_index() -> None:
    # Arrange
    confirmation_points = _confirmation_points(
        "knowledge",
        "knowledge_and_practice",
    )
    deepdive_points: list[ConfirmationPoint] = [
        {
            "id": "cp_deepdive_003",
            "content": "深掘り: 制約付きジェネリクス",
            "format": "knowledge",
        },
    ]
    state = _state(
        confirmation_points=confirmation_points,
        current_point_index=0,
    )
    llm_client = _RecordingAnswerEvaluationLlm(
        output=EvaluationOutput(
            next_action="deepdive",
            score=48,
            feedback="制約付きジェネリクスの理解を確認します。",
            deepdive_points=deepdive_points,
        ),
    )

    # Act
    result = evaluate_answer(state, llm=llm_client)

    # Assert
    assert result["next_action"] == "deepdive"
    assert result["current_point_index"] == 1
    assert result["confirmation_points"] == [*confirmation_points, *deepdive_points]


def test_tc_12_complete_sets_current_point_index_to_completion_boundary() -> None:
    # Arrange
    confirmation_points = _confirmation_points(
        "knowledge",
        "knowledge_and_practice",
    )
    state = _state(
        confirmation_points=confirmation_points,
        current_point_index=1,
    )
    llm_client = _RecordingAnswerEvaluationLlm(
        output=EvaluationOutput(
            next_action="complete",
            score=95,
            feedback="全確認ポイントを完了しました。",
            deepdive_points=[],
        ),
    )

    # Act
    result = evaluate_answer(state, llm=llm_client)

    # Assert
    assert result["next_action"] == "complete"
    assert result["confirmation_points"] == confirmation_points
    assert result["current_point_index"] == len(confirmation_points)


def test_tc_13_form_input_is_normalized_to_answer_input_type() -> None:
    # Arrange
    state = _state(
        confirmation_points=_confirmation_points("knowledge"),
        input_source="form",
        input_type=None,
    )
    llm_client = _RecordingAnswerEvaluationLlm(
        output=EvaluationOutput(
            next_action="next",
            score=75,
            feedback="要点は押さえられています。",
            deepdive_points=[],
        ),
    )

    # Act
    result = evaluate_answer(state, llm=llm_client)

    # Assert
    assert "input_type" in result
    assert result["input_type"] == "answer"


def test_tc_20_passes_total_questions_asked_convergence_signal_to_llm() -> None:
    # Arrange
    state = _state(
        confirmation_points=_confirmation_points("knowledge"),
        total_questions_asked=20,
    )
    llm_client = _RecordingAnswerEvaluationLlm(
        output=EvaluationOutput(
            next_action="complete",
            score=84,
            feedback="収束条件に達したので完了します。",
            deepdive_points=[],
        ),
    )

    # Act
    result = evaluate_answer(state, llm=llm_client)

    # Assert
    assert llm_client.calls == [
        (
            "型引数を明示する理由を説明してください。",
            "確認ポイント 1",
            "呼び出し側の意図を明確にできるからです。",
            "textarea",
            [],
            20,
        ),
    ]
    assert result["next_action"] == "complete"


def test_tc_30_llm_request_failure_propagates_answer_evaluation_error() -> None:
    # Arrange
    cause = RuntimeError("request failed")
    error = _answer_evaluation_error(
        error_code="llm_request_failed",
        message="answer evaluation llm request failed",
        cause=cause,
    )
    state = _state(confirmation_points=_confirmation_points("knowledge"))
    llm_client = _RecordingAnswerEvaluationLlm(error=error)

    # Act / Assert
    with (
        capture_logs() as log_output,
        pytest.raises(AnswerEvaluationError) as exc_info,
    ):
        evaluate_answer(state, llm=llm_client)

    assert exc_info.value is error
    assert exc_info.value.error_code == "llm_request_failed"
    assert exc_info.value.message == "answer evaluation llm request failed"
    assert exc_info.value.__cause__ is cause
    assert len(llm_client.calls) == 1
    assert len(log_output) == 1
    assert find_log_events(log_output, _FAILED_EVENT) == [log_output[0]]
    assert log_output[0]["event"] == _FAILED_EVENT


def test_tc_31_llm_response_parse_failure_propagates_answer_evaluation_error() -> None:
    # Arrange
    cause = ValueError("parse failed")
    error = _answer_evaluation_error(
        error_code="llm_response_parse_failed",
        message="answer evaluation llm response parse failed",
        cause=cause,
    )
    state = _state(
        confirmation_points=_confirmation_points("knowledge_and_practice"),
    )
    llm_client = _RecordingAnswerEvaluationLlm(error=error)

    # Act / Assert
    with (
        capture_logs() as log_output,
        pytest.raises(AnswerEvaluationError) as exc_info,
    ):
        evaluate_answer(state, llm=llm_client)

    assert exc_info.value is error
    assert exc_info.value.error_code == "llm_response_parse_failed"
    assert exc_info.value.message == "answer evaluation llm response parse failed"
    assert exc_info.value.__cause__ is cause
    assert len(llm_client.calls) == 1
    assert len(log_output) == 1
    assert find_log_events(log_output, _FAILED_EVENT) == [log_output[0]]
    assert log_output[0]["event"] == _FAILED_EVENT
