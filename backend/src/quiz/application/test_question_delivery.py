from __future__ import annotations

from typing import TYPE_CHECKING, Literal

import pytest
from structlog.testing import capture_logs

from quiz.application.question_delivery import deliver_question
from quiz.application.question_delivery_types import (
    QuestionDeliveryError,
    QuestionOutput,
)
from shared.log_assertions import find_log_events

if TYPE_CHECKING:
    from quiz.domain.session_state import (
        ConfirmationPoint,
        ConfirmationPointFormat,
        QuizAnswerRecord,
        SessionState,
    )


_FAILED_EVENT = "question_delivery_failed"


class _RecordingQuestionDeliveryLlm:
    def __init__(
        self,
        *,
        output: QuestionOutput | None = None,
        error: QuestionDeliveryError | None = None,
    ) -> None:
        self._output = output
        self._error = error
        self.calls: list[
            tuple[
                str,
                str,
                str,
                Literal["knowledge", "knowledge_and_practice"],
                list[QuizAnswerRecord],
            ]
        ] = []

    def generate_question(
        self,
        title: str,
        description: str,
        confirmation_point_content: str,
        confirmation_point_format: Literal["knowledge", "knowledge_and_practice"],
        past_answers: list[QuizAnswerRecord],
    ) -> QuestionOutput:
        self.calls.append(
            (
                title,
                description,
                confirmation_point_content,
                confirmation_point_format,
                past_answers,
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


def _resumed_answers() -> list[QuizAnswerRecord]:
    return [
        *_answers(),
        {
            "question_number": 2,
            "confirmation_point_id": "cp_999",
            "question_text": "前回の深掘り質問",
            "answer_type": "textarea",
            "answer_text": "前回の回答",
            "score": 55,
            "feedback": "補足が必要です。",
        },
    ]


def _state(
    *,
    confirmation_points: list[ConfirmationPoint],
    current_point_index: int = 0,
    answers: list[QuizAnswerRecord] | None = None,
    total_questions_asked: int | None = None,
) -> SessionState:
    state: SessionState = {
        "roadmap_item_title": "TypeScript ジェネリクス",
        "roadmap_item_description": "型パラメータと型推論の理解を確認する",
        "confirmation_points": confirmation_points,
        "current_point_index": current_point_index,
        "answers": [] if answers is None else answers,
    }
    if total_questions_asked is not None:
        state["total_questions_asked"] = total_questions_asked
    return state


def _question_delivery_error(
    *,
    error_code: str,
    message: str,
    cause: Exception,
) -> QuestionDeliveryError:
    error = QuestionDeliveryError(error_code=error_code, message=message)
    error.__cause__ = cause
    return error


def test_tc_01_deliver_question_public_return_contract_and_llm_mapping() -> None:
    # Arrange
    """テスト対象: deliver_question 関数。
    テストケース: 個別条件での処理を検証する。
    期待結果: 想定どおりの処理結果が得られる。"""
    confirmation_points = _confirmation_points("knowledge", "knowledge_and_practice")
    state = _state(confirmation_points=confirmation_points)
    llm_client = _RecordingQuestionDeliveryLlm(
        output=QuestionOutput(
            question_text="型推論で型引数を省略できる理由を説明してください。",
            answer_type="textarea",
        ),
    )

    # Act
    result = deliver_question(state, llm=llm_client)

    # Assert
    assert llm_client.calls == [
        (
            "TypeScript ジェネリクス",
            "型パラメータと型推論の理解を確認する",
            "確認ポイント 1",
            "knowledge",
            [],
        ),
    ]
    assert result == {
        "current_question_text": "型推論で型引数を省略できる理由を説明してください。",
        "current_answer_type": "textarea",
        "total_questions_asked": 1,
    }


def test_tc_02_second_confirmation_point_returns_llm_output_and_increments_total_questions_asked() -> (
    None
):
    # Arrange
    """テスト対象: deliver_question 関数。
    テストケース: 個別条件での処理を検証する。
    期待結果: 想定どおりの処理結果が得られる。"""
    confirmation_points = _confirmation_points(
        "knowledge",
        "knowledge_and_practice",
    )
    state = _state(
        confirmation_points=confirmation_points,
        current_point_index=1,
        total_questions_asked=9,
    )
    llm_client = _RecordingQuestionDeliveryLlm(
        output=QuestionOutput(
            question_text="ジェネリックな filterBy を実装してください。",
            answer_type="code",
        ),
    )

    # Act
    result = deliver_question(state, llm=llm_client)

    # Assert
    assert llm_client.calls == [
        (
            "TypeScript ジェネリクス",
            "型パラメータと型推論の理解を確認する",
            "確認ポイント 2",
            "knowledge_and_practice",
            [],
        ),
    ]
    assert result == {
        "current_question_text": "ジェネリックな filterBy を実装してください。",
        "current_answer_type": "code",
        "total_questions_asked": 10,
    }


def test_tc_10_knowledge_confirmation_point_returns_textarea() -> None:
    # Arrange
    """テスト対象: deliver_question 関数。
    テストケース: 個別条件での処理を検証する。
    期待結果: 想定どおりの処理結果が得られる。"""
    past_answers = _answers()
    state = _state(
        confirmation_points=_confirmation_points("knowledge"),
        answers=past_answers,
    )
    llm_client = _RecordingQuestionDeliveryLlm(
        output=QuestionOutput(
            question_text="型引数を明示する場面を説明してください。",
            answer_type="textarea",
        ),
    )

    # Act
    result = deliver_question(state, llm=llm_client)

    # Assert
    assert llm_client.calls == [
        (
            "TypeScript ジェネリクス",
            "型パラメータと型推論の理解を確認する",
            "確認ポイント 1",
            "knowledge",
            past_answers,
        ),
    ]
    assert llm_client.calls[0][4] is past_answers
    assert result["current_question_text"] == "型引数を明示する場面を説明してください。"
    assert result["current_answer_type"] == "textarea"


def test_tc_11_knowledge_and_practice_returns_code_and_passes_past_answers() -> None:
    # Arrange
    """テスト対象: deliver_question 関数。
    テストケース: 個別条件での処理を検証する。
    期待結果: 想定どおりの処理結果が得られる。"""
    confirmation_points = _confirmation_points(
        "knowledge",
        "knowledge_and_practice",
    )
    past_answers = _answers()
    state = _state(
        confirmation_points=confirmation_points,
        current_point_index=1,
        answers=past_answers,
    )
    llm_client = _RecordingQuestionDeliveryLlm(
        output=QuestionOutput(
            question_text="ジェネリックな filterBy を実装してください。",
            answer_type="code",
        ),
    )

    # Act
    result = deliver_question(state, llm=llm_client)

    # Assert
    assert llm_client.calls == [
        (
            "TypeScript ジェネリクス",
            "型パラメータと型推論の理解を確認する",
            "確認ポイント 2",
            "knowledge_and_practice",
            past_answers,
        ),
    ]
    assert llm_client.calls[0][4] is past_answers
    assert (
        result["current_question_text"]
        == "ジェネリックな filterBy を実装してください。"
    )
    assert result["current_answer_type"] == "code"


def test_tc_12_resumed_session_continues_from_current_point_index() -> None:
    # Arrange
    """テスト対象: deliver_question 関数。
    テストケース: 個別条件での処理を検証する。
    期待結果: 想定どおりの処理結果が得られる。"""
    confirmation_points = _confirmation_points(
        "knowledge",
        "knowledge_and_practice",
        "knowledge",
    )
    resumed_answers = _resumed_answers()
    state = _state(
        confirmation_points=confirmation_points,
        current_point_index=1,
        answers=resumed_answers,
        total_questions_asked=3,
    )
    llm_client = _RecordingQuestionDeliveryLlm(
        output=QuestionOutput(
            question_text="配列を受け取るジェネリック関数を実装してください。",
            answer_type="code",
        ),
    )

    # Act
    result = deliver_question(state, llm=llm_client)

    # Assert
    assert llm_client.calls == [
        (
            "TypeScript ジェネリクス",
            "型パラメータと型推論の理解を確認する",
            "確認ポイント 2",
            "knowledge_and_practice",
            resumed_answers,
        ),
    ]
    assert llm_client.calls[0][4] is resumed_answers
    assert result == {
        "current_question_text": "配列を受け取るジェネリック関数を実装してください。",
        "current_answer_type": "code",
        "total_questions_asked": 4,
    }


def test_tc_20_returns_empty_update_without_llm_when_all_points_are_consumed() -> None:
    # Arrange
    """テスト対象: deliver_question 関数。
    テストケース: 個別条件での処理を検証する。
    期待結果: 想定どおりの処理結果が得られる。"""
    confirmation_points = _confirmation_points("knowledge", "knowledge_and_practice")
    state = _state(
        confirmation_points=confirmation_points,
        current_point_index=len(confirmation_points),
        answers=_answers(),
        total_questions_asked=2,
    )
    llm_client = _RecordingQuestionDeliveryLlm(
        output=QuestionOutput(
            question_text="unused",
            answer_type="textarea",
        ),
    )

    # Act
    result = deliver_question(state, llm=llm_client)

    # Assert
    assert llm_client.calls == []
    assert result == {}


def test_tc_21_appended_deepdive_confirmation_point_is_delivered() -> None:
    # Arrange
    """テスト対象: deliver_question 関数。
    テストケース: 個別条件での処理を検証する。
    期待結果: 想定どおりの処理結果が得られる。"""
    confirmation_points: list[ConfirmationPoint] = [
        {
            "id": "cp_001",
            "content": "型推論の基本",
            "format": "knowledge",
        },
        {
            "id": "cp_002",
            "content": "ジェネリック関数の実装",
            "format": "knowledge_and_practice",
        },
        {
            "id": "cp_deepdive_003",
            "content": "深掘り: 制約付きジェネリクス",
            "format": "knowledge",
        },
    ]
    state = _state(
        confirmation_points=confirmation_points,
        current_point_index=2,
        answers=_answers(),
        total_questions_asked=6,
    )
    llm_client = _RecordingQuestionDeliveryLlm(
        output=QuestionOutput(
            question_text="さきほどの実装例を踏まえて制約付きジェネリクスを説明してください。",
            answer_type="textarea",
        ),
    )

    # Act
    result = deliver_question(state, llm=llm_client)

    # Assert
    assert llm_client.calls[0][2] == "深掘り: 制約付きジェネリクス"
    assert llm_client.calls[0][3] == "knowledge"
    assert result["current_question_text"] == (
        "さきほどの実装例を踏まえて制約付きジェネリクスを説明してください。"
    )
    assert result["total_questions_asked"] == 7


def test_tc_30_llm_request_failure_is_reraised_as_is() -> None:
    # Arrange
    """テスト対象: deliver_question 関数。
    テストケース: 個別条件での処理を検証する。
    期待結果: 想定どおりの処理結果が得られる。"""
    cause = RuntimeError("request failed")
    error = _question_delivery_error(
        error_code="llm_request_failed",
        message="question delivery llm request failed",
        cause=cause,
    )
    state = _state(confirmation_points=_confirmation_points("knowledge"))
    llm_client = _RecordingQuestionDeliveryLlm(error=error)

    # Act / Assert
    with (
        capture_logs() as log_output,
        pytest.raises(QuestionDeliveryError) as exc_info,
    ):
        deliver_question(state, llm=llm_client)

    assert exc_info.value is error
    assert exc_info.value.error_code == "llm_request_failed"
    assert exc_info.value.message == "question delivery llm request failed"
    assert exc_info.value.__cause__ is cause
    assert len(llm_client.calls) == 1
    assert len(log_output) == 1
    assert find_log_events(log_output, _FAILED_EVENT) == [log_output[0]]
    assert log_output[0]["event"] == _FAILED_EVENT


def test_tc_31_llm_response_parse_failure_is_reraised_as_is() -> None:
    # Arrange
    """テスト対象: deliver_question 関数。
    テストケース: 個別条件での処理を検証する。
    期待結果: 想定どおりの処理結果が得られる。"""
    cause = ValueError("parse failed")
    error = _question_delivery_error(
        error_code="llm_response_parse_failed",
        message="question delivery llm response parse failed",
        cause=cause,
    )
    state = _state(confirmation_points=_confirmation_points("knowledge_and_practice"))
    llm_client = _RecordingQuestionDeliveryLlm(error=error)

    # Act / Assert
    with (
        capture_logs() as log_output,
        pytest.raises(QuestionDeliveryError) as exc_info,
    ):
        deliver_question(state, llm=llm_client)

    assert exc_info.value is error
    assert exc_info.value.error_code == "llm_response_parse_failed"
    assert exc_info.value.message == "question delivery llm response parse failed"
    assert exc_info.value.__cause__ is cause
    assert len(llm_client.calls) == 1
    assert len(log_output) == 1
    assert find_log_events(log_output, _FAILED_EVENT) == [log_output[0]]
    assert log_output[0]["event"] == _FAILED_EVENT
