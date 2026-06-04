from __future__ import annotations

# mypy: disable-error-code=import-not-found
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


class _RecordingExplanationRagClient:
    def __init__(
        self,
        *,
        chunks: list[str] | None = None,
        error: ExplanationGenerationError | None = None,
        call_trace: list[str] | None = None,
    ) -> None:
        self._chunks = [] if chunks is None else chunks
        self._error = error
        self._call_trace = call_trace
        self.calls: list[str] = []

    def search_related_chunks(self, query: str) -> list[str]:
        self.calls.append(query)
        if self._call_trace is not None:
            self._call_trace.append("rag")
        if self._error is not None:
            raise self._error
        return list(self._chunks)


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
        self.calls: list[tuple[str, str, list[str]]] = []

    def generate_explanation(
        self,
        question_text: str,
        confirmation_point_content: str,
        note_chunks: list[str],
    ) -> str:
        self.calls.append(
            (
                question_text,
                confirmation_point_content,
                note_chunks,
            ),
        )
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


def test_tc_01_generate_explanation_public_return_contract_and_dependency_mapping() -> (
    None
):
    # Arrange
    """テスト対象: generate_explanation 関数。
    テストケース: 個別条件での処理を検証する。
    期待結果: 想定どおりの処理結果が得られる。"""
    state = _state()
    note_chunks = [
        "TypeScript入門.md: 型パラメータは関数に型の柔軟性を持たせる",
        "TypeScript入門.md: any ではなく具体型を保ったまま再利用できる",
    ]
    explanation_text = (
        "あなたのノートには『型パラメータは関数に型の柔軟性を持たせる』と"
        "あります。補足すると、呼び出しごとに具体型を変えても型安全を保てます。"
    )
    call_trace: list[str] = []
    rag_client = _RecordingExplanationRagClient(
        chunks=note_chunks,
        call_trace=call_trace,
    )
    llm_client = _RecordingExplanationLlmClient(
        explanation_text=explanation_text,
        call_trace=call_trace,
    )

    # Act
    result = generate_explanation(state, rag=rag_client, llm=llm_client)

    # Assert
    assert call_trace == ["rag", "llm"]
    assert rag_client.calls == [
        "ジェネリクスの型パラメータとは何か説明してください\n"
        "ジェネリクスの型パラメータの役割を説明できる",
    ]
    assert llm_client.calls == [
        (
            "ジェネリクスの型パラメータとは何か説明してください",
            "ジェネリクスの型パラメータの役割を説明できる",
            note_chunks,
        ),
    ]
    assert set(result) == {"explanation_text"}
    assert result == {"explanation_text": explanation_text}


def test_tc_02_generate_explanation_keeps_current_confirmation_point_unchanged() -> (
    None
):
    # Arrange
    """テスト対象: generate_explanation 関数。
    テストケース: 個別条件での処理を検証する。
    期待結果: 想定どおりの処理結果が得られる。"""
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
    rag_client = _RecordingExplanationRagClient(
        chunks=["TypeScript入門.md: 型引数は意図を明示できる"],
    )
    llm_client = _RecordingExplanationLlmClient(
        explanation_text="型引数を明示すると、推論結果に頼らず意図を固定できます。",
    )

    # Act
    result = generate_explanation(state, rag=rag_client, llm=llm_client)

    # Assert
    assert result == {
        "explanation_text": "型引数を明示すると、推論結果に頼らず意図を固定できます。",
    }
    assert "current_point_index" not in result
    assert "confirmation_points" not in result
    assert "answers" not in result
    assert "total_questions_asked" not in result
    assert "score" not in result
    assert state["current_point_index"] == 1
    assert state["confirmation_points"] == original_confirmation_points


def test_tc_10_note_chunks_are_passed_in_order_and_explanation_text_is_returned() -> (
    None
):
    # Arrange
    """テスト対象: generate_explanation 関数。
    テストケース: 個別条件での処理を検証する。
    期待結果: 想定どおりの処理結果が得られる。"""
    note_chunks = [
        "TypeScript入門.md: 型パラメータは関数に型の柔軟性を持たせる",
        "TypeScript入門.md: any ではなく具体型を保ったまま再利用できる",
    ]
    explanation_text = (
        "あなたのノートには『型パラメータは関数に型の柔軟性を持たせる』"
        "『any ではなく具体型を保ったまま再利用できる』と書いてあります。"
        "補足すると、呼び出し側ごとに型推論が働くため、再利用性と型安全性を両立できます。"
    )
    rag_client = _RecordingExplanationRagClient(chunks=note_chunks)
    llm_client = _RecordingExplanationLlmClient(explanation_text=explanation_text)

    # Act
    result = generate_explanation(_state(), rag=rag_client, llm=llm_client)

    # Assert
    assert llm_client.calls == [
        (
            "ジェネリクスの型パラメータとは何か説明してください",
            "ジェネリクスの型パラメータの役割を説明できる",
            note_chunks,
        ),
    ]
    assert result["explanation_text"] == explanation_text
    assert "あなたのノートには" in result["explanation_text"]
    assert "補足すると" in result["explanation_text"]


def test_tc_11_generate_explanation_succeeds_with_empty_note_chunks() -> None:
    # Arrange
    """テスト対象: generate_explanation 関数。
    テストケース: 個別条件での処理を検証する。
    期待結果: 想定どおりの処理結果が得られる。"""
    rag_client = _RecordingExplanationRagClient(chunks=[])
    llm_client = _RecordingExplanationLlmClient(
        explanation_text="型パラメータは処理の形を保ったまま具体型だけ差し替えるために使います。",
    )

    # Act
    result = generate_explanation(_state(), rag=rag_client, llm=llm_client)

    # Assert
    assert rag_client.calls == [
        "ジェネリクスの型パラメータとは何か説明してください\n"
        "ジェネリクスの型パラメータの役割を説明できる",
    ]
    assert llm_client.calls == [
        (
            "ジェネリクスの型パラメータとは何か説明してください",
            "ジェネリクスの型パラメータの役割を説明できる",
            [],
        ),
    ]
    assert result == {
        "explanation_text": "型パラメータは処理の形を保ったまま具体型だけ差し替えるために使います。",
    }


def test_tc_20_same_confirmation_point_can_be_explained_multiple_times() -> None:
    # Arrange
    """テスト対象: generate_explanation 関数。
    テストケース: 個別条件での処理を検証する。
    期待結果: 想定どおりの処理結果が得られる。"""
    state = _state(include_optional_fields=True)
    original_state = deepcopy(state)
    rag_client = _RecordingExplanationRagClient(
        chunks=["TypeScript入門.md: 型パラメータは呼び出しごとに具体化される"],
    )
    llm_client = _RecordingExplanationLlmClient(
        explanation_text="型パラメータは使うたびに具体型へ置き換えられるため、共通の処理を安全に再利用できます。",
    )

    # Act
    first_result = generate_explanation(state, rag=rag_client, llm=llm_client)
    second_result = generate_explanation(state, rag=rag_client, llm=llm_client)

    # Assert
    assert set(first_result) == {"explanation_text"}
    assert isinstance(first_result["explanation_text"], str)
    assert set(second_result) == {"explanation_text"}
    assert isinstance(second_result["explanation_text"], str)
    assert len(rag_client.calls) == 2
    assert len(llm_client.calls) == 2
    assert state == original_state


def test_tc_21_alternate_question_text_can_be_explained_without_advancing_state() -> (
    None
):
    # Arrange
    """テスト対象: generate_explanation 関数。
    テストケース: 個別条件での処理を検証する。
    期待結果: 想定どおりの処理結果が得られる。"""
    question_text = (
        "では、<T>を使わずにany型で書いた場合と比べて、"
        "型パラメータを使うメリットは何でしょうか?"
    )
    state = _state(
        current_question_text=question_text,
        include_optional_fields=True,
    )
    original_confirmation_points = deepcopy(state["confirmation_points"])
    rag_client = _RecordingExplanationRagClient(
        chunks=["TypeScript入門.md: any だと戻り値の型情報が失われる"],
    )
    llm_client = _RecordingExplanationLlmClient(
        explanation_text="型パラメータを使うと、入力と出力の対応関係を保ったまま再利用できます。",
    )

    # Act
    result = generate_explanation(state, rag=rag_client, llm=llm_client)

    # Assert
    assert rag_client.calls == [
        "では、<T>を使わずにany型で書いた場合と比べて、"
        "型パラメータを使うメリットは何でしょうか?\n"
        "ジェネリクスの型パラメータの役割を説明できる",
    ]
    assert result == {
        "explanation_text": "型パラメータを使うと、入力と出力の対応関係を保ったまま再利用できます。",
    }
    assert state["current_point_index"] == 0
    assert state["confirmation_points"] == original_confirmation_points


def test_tc_30_success_path_calls_dependencies_once_each_and_logs_no_failure() -> None:
    # Arrange
    """テスト対象: generate_explanation 関数。
    テストケース: 個別条件での処理を検証する。
    期待結果: 想定どおりの処理結果が得られる。"""
    rag_client = _RecordingExplanationRagClient(
        chunks=["TypeScript入門.md: 型パラメータは型の対応関係を保つ"],
    )
    llm_client = _RecordingExplanationLlmClient(
        explanation_text="型パラメータは入力と出力の型のつながりを保つために使います。",
    )

    # Act
    with capture_logs() as log_output:
        result = generate_explanation(_state(), rag=rag_client, llm=llm_client)

    # Assert
    assert result == {
        "explanation_text": "型パラメータは入力と出力の型のつながりを保つために使います。",
    }
    assert len(rag_client.calls) == 1
    assert len(llm_client.calls) == 1
    assert find_log_events(log_output, _FAILED_EVENT) == []


def test_tc_31_rag_search_failure_is_logged_once_and_reraised() -> None:
    # Arrange
    """テスト対象: generate_explanation 関数。
    テストケース: 個別条件での処理を検証する。
    期待結果: 想定どおりの処理結果が得られる。"""
    cause = RuntimeError("rag request failed")
    error = _explanation_generation_error(
        error_code="rag_search_failed",
        message="explanation generation rag search failed",
        cause=cause,
    )
    rag_client = _RecordingExplanationRagClient(error=error)
    llm_client = _RecordingExplanationLlmClient(
        explanation_text="should not be used",
    )

    # Act / Assert
    with (
        capture_logs() as log_output,
        pytest.raises(ExplanationGenerationError) as exc_info,
    ):
        generate_explanation(_state(), rag=rag_client, llm=llm_client)

    assert exc_info.value is error
    assert exc_info.value.error_code == "rag_search_failed"
    assert exc_info.value.message == "explanation generation rag search failed"
    assert exc_info.value.__cause__ is cause
    assert len(rag_client.calls) == 1
    assert llm_client.calls == []
    assert len(log_output) == 1
    assert find_log_events(log_output, _FAILED_EVENT) == [log_output[0]]
    assert log_output[0]["event"] == _FAILED_EVENT


def test_tc_32_llm_request_failure_is_logged_once_and_reraised() -> None:
    # Arrange
    """テスト対象: generate_explanation 関数。
    テストケース: 個別条件での処理を検証する。
    期待結果: 想定どおりの処理結果が得られる。"""
    cause = RuntimeError("llm request failed")
    error = _explanation_generation_error(
        error_code="llm_request_failed",
        message="explanation generation llm request failed",
        cause=cause,
    )
    rag_client = _RecordingExplanationRagClient(
        chunks=["TypeScript入門.md: 型パラメータは型情報を保つ"],
    )
    llm_client = _RecordingExplanationLlmClient(error=error)

    # Act / Assert
    with (
        capture_logs() as log_output,
        pytest.raises(ExplanationGenerationError) as exc_info,
    ):
        generate_explanation(_state(), rag=rag_client, llm=llm_client)

    assert exc_info.value is error
    assert exc_info.value.error_code == "llm_request_failed"
    assert exc_info.value.message == "explanation generation llm request failed"
    assert exc_info.value.__cause__ is cause
    assert len(rag_client.calls) == 1
    assert len(llm_client.calls) == 1
    assert len(log_output) == 1
    assert find_log_events(log_output, _FAILED_EVENT) == [log_output[0]]
    assert log_output[0]["event"] == _FAILED_EVENT


def test_tc_33_llm_response_parse_failure_is_logged_once_and_reraised() -> None:
    # Arrange
    """テスト対象: generate_explanation 関数。
    テストケース: 個別条件での処理を検証する。
    期待結果: 想定どおりの処理結果が得られる。"""
    cause = ValueError("parse failed")
    error = _explanation_generation_error(
        error_code="llm_response_parse_failed",
        message="explanation generation llm response parse failed",
        cause=cause,
    )
    rag_client = _RecordingExplanationRagClient(
        chunks=["TypeScript入門.md: 型推論があるため具体型を毎回書かなくてよい"],
    )
    llm_client = _RecordingExplanationLlmClient(error=error)

    # Act / Assert
    with (
        capture_logs() as log_output,
        pytest.raises(ExplanationGenerationError) as exc_info,
    ):
        generate_explanation(_state(), rag=rag_client, llm=llm_client)

    assert exc_info.value is error
    assert exc_info.value.error_code == "llm_response_parse_failed"
    assert exc_info.value.message == "explanation generation llm response parse failed"
    assert exc_info.value.__cause__ is cause
    assert len(rag_client.calls) == 1
    assert len(llm_client.calls) == 1
    assert len(log_output) == 1
    assert find_log_events(log_output, _FAILED_EVENT) == [log_output[0]]
    assert log_output[0]["event"] == _FAILED_EVENT
