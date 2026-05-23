from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from structlog.testing import capture_logs

from quiz.application.chat_response import respond_to_chat
from quiz.application.chat_response_types import ChatResponseError
from shared.log_assertions import find_log_events

if TYPE_CHECKING:
    from quiz.domain.session_state import SessionState

_FAILED_EVENT = "chat_response_failed"


class _RecordingChatResponseLlm:
    def __init__(
        self,
        response: str = "LLM の回答テキスト",
        *,
        error: ChatResponseError | None = None,
    ) -> None:
        self._response = response
        self._error = error
        self.calls: list[tuple[str, str]] = []

    def generate_chat_response(
        self,
        question_text: str,
        user_input: str,
    ) -> str:
        self.calls.append((question_text, user_input))
        if self._error is not None:
            raise self._error
        return self._response


def _state(
    *,
    question_text: str = "ジェネリクスとは何か説明してください",
    user_input: str = "型パラメータってどういう意味ですか?",
) -> SessionState:
    return {
        "current_question_text": question_text,
        "user_input": user_input,
        "input_type": "question",
    }


def test_tc_01_respond_to_chat_returns_response_text_and_calls_llm_once() -> None:
    llm = _RecordingChatResponseLlm(response="型パラメータとは...")
    state = _state()

    with capture_logs() as log_output:
        result = respond_to_chat(state, llm=llm)

    assert result == {"chat_response_text": "型パラメータとは..."}
    assert len(llm.calls) == 1
    assert llm.calls[0] == (
        "ジェネリクスとは何か説明してください",
        "型パラメータってどういう意味ですか?",
    )
    assert find_log_events(log_output, _FAILED_EVENT) == []


def test_tc_02_respond_to_chat_does_not_modify_question_context() -> None:
    llm = _RecordingChatResponseLlm()
    state = _state()

    result = respond_to_chat(state, llm=llm)

    assert set(result.keys()) == {"chat_response_text"}
    assert "current_point_index" not in result
    assert "confirmation_points" not in result
    assert "answers" not in result
    assert "total_questions_asked" not in result
    assert "next_action" not in result


def test_tc_10_empty_user_input_is_passed_through() -> None:
    llm = _RecordingChatResponseLlm(response="何か質問があればどうぞ")
    state = _state(user_input="")

    result = respond_to_chat(state, llm=llm)

    assert result["chat_response_text"] == "何か質問があればどうぞ"
    assert llm.calls[0][1] == ""


def test_tc_30_llm_request_failure_is_logged_once_and_reraised() -> None:
    cause = ConnectionError("LLM unreachable")
    error = ChatResponseError(
        error_code="llm_request_failed",
        message="chat response llm request failed",
    )
    error.__cause__ = cause
    llm = _RecordingChatResponseLlm(error=error)

    with capture_logs() as log_output, pytest.raises(ChatResponseError) as exc_info:
        respond_to_chat(_state(), llm=llm)

    assert exc_info.value is error
    assert exc_info.value.error_code == "llm_request_failed"
    assert exc_info.value.message == "chat response llm request failed"
    assert exc_info.value.__cause__ is cause
    assert len(llm.calls) == 1
    assert len(find_log_events(log_output, _FAILED_EVENT)) == 1


def test_tc_31_llm_response_parse_failure_is_logged_once_and_reraised() -> None:
    cause = ValueError("cannot parse response")
    error = ChatResponseError(
        error_code="llm_response_parse_failed",
        message="chat response llm response parse failed",
    )
    error.__cause__ = cause
    llm = _RecordingChatResponseLlm(error=error)

    with capture_logs() as log_output, pytest.raises(ChatResponseError) as exc_info:
        respond_to_chat(_state(), llm=llm)

    assert exc_info.value is error
    assert exc_info.value.error_code == "llm_response_parse_failed"
    assert exc_info.value.__cause__ is cause
    assert len(llm.calls) == 1
    assert len(find_log_events(log_output, _FAILED_EVENT)) == 1
