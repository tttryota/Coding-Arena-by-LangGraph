from __future__ import annotations

from copy import deepcopy
from typing import TYPE_CHECKING

import pytest
from structlog.testing import capture_logs

from quiz.application.explanation_generation import generate_explanation
from quiz.application.explanation_generation_types import ExplanationGenerationError
from shared.log_assertions import find_log_events

if TYPE_CHECKING:
    from quiz.domain.session_state import ConfirmationPoint, SessionState


_FAILED_EVENT = "explanation_generation_failed"


class _RecordingExplanationLlmClient:
    def __init__(
        self,
        *,
        explanation_text: str | None = None,
        error: ExplanationGenerationError | None = None,
        call_trace: list[str] | None = None,
    ) -> None:
        self._explanation_text = explanation_text
        self._error = error
        self._call_trace = call_trace
        self.calls: list[tuple[str, str]] = []

    def generate_explanation(
        self,
        question_text: str,
        confirmation_point_content: str,
    ) -> str:
        self.calls.append((question_text, confirmation_point_content))
        if self._call_trace is not None:
            self._call_trace.append("llm")
        if self._error is not None:
            raise self._error
        assert self._explanation_text is not None
        return self._explanation_text


def _confirmation_points(*contents: str) -> list[ConfirmationPoint]:
    return [
        {
            "id": f"cp_{index:03d}",
            "content": content,
            "format": "knowledge",
        }
        for index, content in enumerate(contents, start=1)
    ]


def _state(
    *,
    current_question_text: str = "ジェネリクスの型パラメータとは何か説明してください",
    confirmation_points: list[ConfirmationPoint] | None = None,
    current_point_index: int = 0,
    include_optional_fields: bool = False,
) -> SessionState:
    state: SessionState = {
        "current_question_text": current_question_text,
        "confirmation_points": (
            _confirmation_points("ジェネリクスの型パラメータの役割を説明できる")
            if confirmation_points is None
            else confirmation_points
        ),
        "current_point_index": current_point_index,
    }
    if include_optional_fields:
        state["answers"] = []
        state["total_questions_asked"] = 3
        state["input_type"] = "explanation_request"
    return state


def _explanation_generation_error(
    *,
    error_code: str,
    message: str,
    cause: Exception,
) -> ExplanationGenerationError:
    error = ExplanationGenerationError(error_code=error_code, message=message)
    error.__cause__ = cause
    return error


def test_tc_01_generate_explanation_maps_inputs_and_returns_text() -> None:
    state = _state()
    explanation_text = (
        "型パラメータは、関数や型を具体型に依存させず再利用するための仕組みです。"
    )
    call_trace: list[str] = []
    llm_client = _RecordingExplanationLlmClient(
        explanation_text=explanation_text,
        call_trace=call_trace,
    )

    result = generate_explanation(state, llm=llm_client)

    assert call_trace == ["llm"]
    assert llm_client.calls == [
        (
            "ジェネリクスの型パラメータとは何か説明してください",
            "ジェネリクスの型パラメータの役割を説明できる",
        ),
    ]
    assert result == {"explanation_text": explanation_text}


def test_tc_02_keeps_current_confirmation_point_unchanged() -> None:
    confirmation_points = _confirmation_points(
        "ジェネリクスの型パラメータの役割を説明できる",
        "型引数を明示する利点を説明できる",
    )
    state = _state(
        confirmation_points=confirmation_points,
        current_point_index=1,
        include_optional_fields=True,
    )
    original_confirmation_points = deepcopy(state["confirmation_points"])
    llm_client = _RecordingExplanationLlmClient(
        explanation_text="型引数を明示すると、推論結果に頼らず意図を固定できます。",
    )

    result = generate_explanation(state, llm=llm_client)

    assert result == {
        "explanation_text": "型引数を明示すると、推論結果に頼らず意図を固定できます。",
    }
    assert "current_point_index" not in result
    assert "confirmation_points" not in result
    assert state["current_point_index"] == 1
    assert state["confirmation_points"] == original_confirmation_points


def test_tc_20_same_confirmation_point_can_be_explained_multiple_times() -> None:
    state = _state(include_optional_fields=True)
    original_state = deepcopy(state)
    llm_client = _RecordingExplanationLlmClient(
        explanation_text="型パラメータは使うたびに具体型へ置き換えられるため、共通処理を安全に再利用できます。",
    )

    first_result = generate_explanation(state, llm=llm_client)
    second_result = generate_explanation(state, llm=llm_client)

    assert set(first_result) == {"explanation_text"}
    assert set(second_result) == {"explanation_text"}
    assert len(llm_client.calls) == 2
    assert state == original_state


def test_tc_30_success_path_logs_no_failure() -> None:
    llm_client = _RecordingExplanationLlmClient(
        explanation_text="型パラメータは入力と出力の型のつながりを保つために使います。",
    )

    with capture_logs() as log_output:
        result = generate_explanation(_state(), llm=llm_client)

    assert result == {
        "explanation_text": "型パラメータは入力と出力の型のつながりを保つために使います。",
    }
    assert len(llm_client.calls) == 1
    assert find_log_events(log_output, _FAILED_EVENT) == []


def test_tc_31_llm_failure_is_logged_once_and_reraised() -> None:
    cause = RuntimeError("llm request failed")
    error = _explanation_generation_error(
        error_code="llm_request_failed",
        message="explanation generation llm request failed",
        cause=cause,
    )
    llm_client = _RecordingExplanationLlmClient(error=error)

    with (
        capture_logs() as log_output,
        pytest.raises(ExplanationGenerationError) as exc_info,
    ):
        generate_explanation(_state(), llm=llm_client)

    assert exc_info.value is error
    assert exc_info.value.__cause__ is cause
    assert len(llm_client.calls) == 1
    assert len(log_output) == 1
    assert find_log_events(log_output, _FAILED_EVENT) == [log_output[0]]
