from __future__ import annotations

from typing import TYPE_CHECKING, Literal

import pytest
from structlog.testing import capture_logs

from quiz.application.input_classification import classify_input
from quiz.application.input_classification_types import InputClassificationError
from shared.log_assertions import find_log_events

if TYPE_CHECKING:
    from quiz.domain.session_state import SessionState


_FAILED_EVENT = "input_classification_failed"
_InputType = Literal["answer", "question", "explanation_request"]


class _ContractAwareInputClassificationLlm:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str]] = []

    def classify_input(
        self,
        question_text: str,
        user_input: str,
    ) -> _InputType:
        self.calls.append((question_text, user_input))
        if user_input in {
            "型安全を保ったまま共通化できるからです",
            "たぶん型のため",
            "",
            "?",
            "うー",
        }:
            return "answer"
        if user_input == "ここでいう型安全って何を指していますか?":
            return "question"
        if user_input == "わからないので解説してください":
            return "explanation_request"
        message = f"unexpected user_input: {user_input!r}"
        raise AssertionError(message)


class _ErroringInputClassificationLlm:
    def __init__(self, *, error: InputClassificationError) -> None:
        self._error = error
        self.calls: list[tuple[str, str]] = []

    def classify_input(
        self,
        question_text: str,
        user_input: str,
    ) -> _InputType:
        self.calls.append((question_text, user_input))
        raise self._error


def _state(
    *,
    current_question_text: str = "型引数を明示する理由を説明してください。",
    user_input: str = "呼び出し側の意図を明確にできるからです。",
    input_source: Literal["chat", "form"] = "chat",
) -> SessionState:
    return {
        "current_question_text": current_question_text,
        "user_input": user_input,
        "input_source": input_source,
    }


def _input_classification_error(
    *,
    error_code: str,
    message: str,
    cause: Exception,
) -> InputClassificationError:
    error = InputClassificationError(error_code=error_code, message=message)
    error.__cause__ = cause
    return error


def test_tc_01_classify_input_returns_answer_and_calls_llm_once() -> None:
    # Arrange
    state = _state(
        current_question_text="TypeScript のジェネリクスが必要な理由を説明してください",
        user_input="型安全を保ったまま共通化できるからです",
        input_source="chat",
    )
    llm_client = _ContractAwareInputClassificationLlm()

    # Act
    result = classify_input(state, llm=llm_client)

    # Assert
    assert llm_client.calls == [
        (
            "TypeScript のジェネリクスが必要な理由を説明してください",
            "型安全を保ったまま共通化できるからです",
        ),
    ]
    assert result == {"input_type": "answer"}


def test_tc_10_tc_30_chat_question_classification_returns_question_in_one_llm_call() -> (
    None
):
    # Arrange
    state = _state(
        current_question_text="ジェネリクスが必要な理由を説明してください",
        user_input="ここでいう型安全って何を指していますか?",
        input_source="chat",
    )
    llm_client = _ContractAwareInputClassificationLlm()

    # Act
    result = classify_input(state, llm=llm_client)

    # Assert
    assert llm_client.calls == [
        (
            "ジェネリクスが必要な理由を説明してください",
            "ここでいう型安全って何を指していますか?",
        ),
    ]
    assert result == {"input_type": "question"}


def test_tc_11_chat_explanation_request_returns_explanation_request() -> None:
    # Arrange
    state = _state(
        current_question_text="ジェネリクスが必要な理由を説明してください",
        user_input="わからないので解説してください",
        input_source="chat",
    )
    llm_client = _ContractAwareInputClassificationLlm()

    # Act
    result = classify_input(state, llm=llm_client)

    # Assert
    assert llm_client.calls == [
        (
            "ジェネリクスが必要な理由を説明してください",
            "わからないので解説してください",
        ),
    ]
    assert result == {"input_type": "explanation_request"}


def test_tc_12_ambiguous_chat_input_is_classified_as_answer() -> None:
    # Arrange
    state = _state(
        current_question_text="ジェネリクスが必要な理由を説明してください",
        user_input="たぶん型のため",
        input_source="chat",
    )
    llm_client = _ContractAwareInputClassificationLlm()

    # Act
    result = classify_input(state, llm=llm_client)

    # Assert
    assert result == {"input_type": "answer"}


def test_tc_20_empty_chat_input_is_classified_as_answer() -> None:
    # Arrange
    state = _state(
        current_question_text="ジェネリクスが必要な理由を説明してください",
        user_input="",
        input_source="chat",
    )
    llm_client = _ContractAwareInputClassificationLlm()

    # Act
    result = classify_input(state, llm=llm_client)

    # Assert
    assert result == {"input_type": "answer"}


def test_tc_21_single_character_input_is_classified_as_answer() -> None:
    # Arrange
    state = _state(
        current_question_text="ジェネリクスが必要な理由を説明してください",
        user_input="?",
        input_source="chat",
    )
    llm_client = _ContractAwareInputClassificationLlm()

    # Act
    result = classify_input(state, llm=llm_client)

    # Assert
    assert result == {"input_type": "answer"}


def test_tc_21_two_character_input_is_classified_as_answer() -> None:
    # Arrange
    state = _state(
        current_question_text="ジェネリクスが必要な理由を説明してください",
        user_input="うー",
        input_source="chat",
    )
    llm_client = _ContractAwareInputClassificationLlm()

    # Act
    result = classify_input(state, llm=llm_client)

    # Assert
    assert result == {"input_type": "answer"}


def test_tc_31_llm_request_failure_is_logged_once_and_reraised() -> None:
    # Arrange
    cause = RuntimeError("request failed")
    error = _input_classification_error(
        error_code="llm_request_failed",
        message="input classification llm request failed",
        cause=cause,
    )
    state = _state(user_input="ok")
    llm_client = _ErroringInputClassificationLlm(error=error)

    # Act / Assert
    with (
        capture_logs() as log_output,
        pytest.raises(InputClassificationError) as exc_info,
    ):
        classify_input(state, llm=llm_client)

    assert exc_info.value is error
    assert exc_info.value.error_code == "llm_request_failed"
    assert exc_info.value.message == "input classification llm request failed"
    assert exc_info.value.__cause__ is cause
    assert len(llm_client.calls) == 1
    assert len(log_output) == 1
    assert find_log_events(log_output, _FAILED_EVENT) == [log_output[0]]
    assert log_output[0]["event"] == _FAILED_EVENT


def test_tc_32_llm_response_parse_failure_is_logged_once_and_reraised() -> None:
    # Arrange
    cause = ValueError("parse failed")
    error = _input_classification_error(
        error_code="llm_response_parse_failed",
        message="input classification llm response parse failed",
        cause=cause,
    )
    state = _state(user_input="?")
    llm_client = _ErroringInputClassificationLlm(error=error)

    # Act / Assert
    with (
        capture_logs() as log_output,
        pytest.raises(InputClassificationError) as exc_info,
    ):
        classify_input(state, llm=llm_client)

    assert exc_info.value is error
    assert exc_info.value.error_code == "llm_response_parse_failed"
    assert exc_info.value.message == "input classification llm response parse failed"
    assert exc_info.value.__cause__ is cause
    assert len(llm_client.calls) == 1
    assert len(log_output) == 1
    assert find_log_events(log_output, _FAILED_EVENT) == [log_output[0]]
    assert log_output[0]["event"] == _FAILED_EVENT
