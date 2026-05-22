from __future__ import annotations

from typing import TYPE_CHECKING, cast

import pytest
from structlog.testing import capture_logs

from quiz.application.question_set_design import design_question_set
from quiz.application.question_set_design_types import QuestionSetDesignError
from shared.log_assertions import assert_single_log_event as _assert_single_log_event
from shared.log_assertions import find_log_events

if TYPE_CHECKING:
    from collections.abc import MutableMapping

    from quiz.domain.session_state import (
        ConfirmationPoint,
        ConfirmationPointFormat,
        RoadmapItemLevel,
        SessionState,
    )


_FAILED_EVENT = "question_set_design_failed"


class _RecordingQuestionSetDesignLlm:
    def __init__(
        self,
        *,
        confirmation_points: list[ConfirmationPoint] | None = None,
        error: QuestionSetDesignError | None = None,
    ) -> None:
        self._confirmation_points = confirmation_points
        self._error = error
        self.calls: list[tuple[str, str, str]] = []

    def generate_confirmation_points(
        self,
        title: str,
        description: str,
        level: str,
    ) -> list[ConfirmationPoint]:
        self.calls.append((title, description, level))
        if self._error is not None:
            raise self._error
        assert self._confirmation_points is not None
        return list(self._confirmation_points)


def _state(
    *,
    title: str = "TypeScript ジェネリクス",
    description: str = "型パラメータと型推論の理解を確認する",
    level: RoadmapItemLevel = "detail",
) -> SessionState:
    return {
        "roadmap_item_title": title,
        "roadmap_item_description": description,
        "roadmap_item_level": level,
    }


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


def _question_set_design_error(
    *,
    error_code: str,
    message: str,
    cause: Exception,
) -> QuestionSetDesignError:
    error = QuestionSetDesignError(error_code=error_code, message=message)
    error.__cause__ = cause
    return error


def _assert_single_failure_log(
    log_output: list[MutableMapping[str, object]],
    *,
    error_code: str,
    roadmap_item_title: str = "TypeScript ジェネリクス",
    roadmap_item_level: str = "detail",
    roadmap_item_description: str = "型パラメータと型推論の理解を確認する",
) -> None:
    assert len(log_output) == 1
    _assert_single_log_event(
        log_output,
        _FAILED_EVENT,
        {
            "error_code": error_code,
            "roadmap_item_title": roadmap_item_title,
            "roadmap_item_level": roadmap_item_level,
            "roadmap_item_description": roadmap_item_description,
        },
    )


def _result_confirmation_points(
    result: dict[str, object],
) -> list[ConfirmationPoint]:
    return cast("list[ConfirmationPoint]", result["confirmation_points"])


def _assert_current_point_index_is_zero(result: dict[str, object]) -> None:
    assert result["current_point_index"] == 0


def _assert_result_confirmation_points_match(
    result: dict[str, object],
    expected_confirmation_points: list[ConfirmationPoint],
) -> list[ConfirmationPoint]:
    returned_points = _result_confirmation_points(result)
    assert returned_points == expected_confirmation_points
    _assert_current_point_index_is_zero(result)
    return returned_points


def _assert_confirmation_point_ids_are_unique(
    confirmation_points: list[ConfirmationPoint],
) -> None:
    ids = [point["id"] for point in confirmation_points]
    assert len(ids) == len(set(ids))


def test_tc_01_design_question_set_reads_required_state_and_returns_base_shape() -> (
    None
):
    # Arrange
    state = _state()
    confirmation_points = _confirmation_points(
        "knowledge",
        "knowledge_and_practice",
        "knowledge",
    )
    llm_client = _RecordingQuestionSetDesignLlm(
        confirmation_points=confirmation_points,
    )

    # Act
    result = design_question_set(state, llm_client=llm_client)

    # Assert
    assert llm_client.calls == [
        (
            "TypeScript ジェネリクス",
            "型パラメータと型推論の理解を確認する",
            "detail",
        ),
    ]
    assert result == {
        "confirmation_points": confirmation_points,
        "current_point_index": 0,
    }


def test_tc_02_confirmation_points_are_returned_as_confirmation_point_dtos() -> None:
    # Arrange
    confirmation_points = _confirmation_points(
        "knowledge",
        "knowledge_and_practice",
        "knowledge",
    )
    llm_client = _RecordingQuestionSetDesignLlm(
        confirmation_points=confirmation_points,
    )

    # Act
    result = design_question_set(_state(), llm_client=llm_client)

    # Assert
    returned_points = _assert_result_confirmation_points_match(
        result,
        confirmation_points,
    )
    assert isinstance(returned_points, list)
    assert len(returned_points) == 3
    _assert_confirmation_point_ids_are_unique(returned_points)
    for point in returned_points:
        assert point.keys() == {"id", "content", "format"}
        assert isinstance(point["id"], str)
        assert point["id"] != ""
        assert isinstance(point["content"], str)
        assert point["content"] != ""
        assert point["format"] in {"knowledge", "knowledge_and_practice"}


def test_tc_10_detail_items_keep_3_to_5_confirmation_points_without_warning() -> None:
    # Arrange
    confirmation_points = _confirmation_points(
        "knowledge",
        "knowledge_and_practice",
        "knowledge",
        "knowledge_and_practice",
    )
    llm_client = _RecordingQuestionSetDesignLlm(
        confirmation_points=confirmation_points,
    )

    # Act / Assert
    with capture_logs() as log_output:
        result = design_question_set(
            _state(level="detail"),
            llm_client=llm_client,
        )

    returned_points = _assert_result_confirmation_points_match(
        result,
        confirmation_points,
    )
    assert len(returned_points) == 4
    assert [entry for entry in log_output if entry.get("log_level") == "warning"] == []


def test_tc_11_formats_are_preserved_as_public_contract_values() -> None:
    # Arrange
    confirmation_points = _confirmation_points(
        "knowledge_and_practice",
        "knowledge",
        "knowledge_and_practice",
    )
    llm_client = _RecordingQuestionSetDesignLlm(
        confirmation_points=confirmation_points,
    )

    # Act
    result = design_question_set(_state(), llm_client=llm_client)

    # Assert
    returned_points = _assert_result_confirmation_points_match(
        result,
        confirmation_points,
    )
    assert [point["format"] for point in returned_points] == [
        point["format"] for point in confirmation_points
    ]
    assert "practice_only" not in [point["format"] for point in returned_points]


def test_tc_12_middle_summary_uses_only_title_description_and_level_inputs() -> None:
    # Arrange
    state = cast(
        "SessionState",
        {
            "roadmap_item_title": "Web セキュリティの基礎",
            "roadmap_item_description": "主要な脆弱性と防御策をまとめて確認する",
            "roadmap_item_level": "middle",
            "session_id": "session-unused-by-question-set-design",
            "roadmap_item_id": "roadmap-unused-by-question-set-design",
            "is_resumed": True,
            "confirmation_points": [
                {
                    "id": "state_cp_001",
                    "content": "state 側の既存 confirmation point は参照しない",
                    "format": "knowledge",
                },
            ],
            "current_point_index": 99,
            "current_question_text": "state 側の既存 question は参照しない",
            "current_answer_type": "code",
            "user_input": "state 側の user_input は参照しない",
            "input_source": "chat",
            "input_type": "explanation_request",
            "next_action": "deepdive",
            "answers": [
                {
                    "question_number": 7,
                    "confirmation_point_id": "state_cp_001",
                    "question_text": "state 側の answers は参照しない",
                    "answer_type": "textarea",
                    "answer_text": "unused answer",
                    "score": 1,
                    "feedback": "unused feedback",
                },
            ],
            "total_questions_asked": 13,
        },
    )
    confirmation_points = _confirmation_points(
        "knowledge",
        "knowledge",
        "knowledge_and_practice",
    )
    llm_client = _RecordingQuestionSetDesignLlm(
        confirmation_points=confirmation_points,
    )

    # Act
    result = design_question_set(state, llm_client=llm_client)

    # Assert
    assert llm_client.calls == [
        (
            "Web セキュリティの基礎",
            "主要な脆弱性と防御策をまとめて確認する",
            "middle",
        ),
    ]
    _assert_result_confirmation_points_match(result, confirmation_points)


def test_tc_20_empty_description_is_passed_through_and_title_only_can_drive_design() -> (
    None
):
    # Arrange
    state = _state(
        title="再帰関数の基本",
        description="",
        level="detail",
    )
    confirmation_points = _confirmation_points(
        "knowledge",
        "knowledge_and_practice",
        "knowledge",
    )
    llm_client = _RecordingQuestionSetDesignLlm(
        confirmation_points=confirmation_points,
    )

    # Act
    result = design_question_set(state, llm_client=llm_client)

    # Assert
    assert llm_client.calls == [("再帰関数の基本", "", "detail")]
    _assert_result_confirmation_points_match(result, confirmation_points)


def test_tc_21_conceptual_items_can_return_knowledge_only_confirmation_points() -> None:
    # Arrange
    state = _state(
        title="プログラミングパラダイムの比較",
        description="手続き型、オブジェクト指向、関数型の違いを理解する",
        level="detail",
    )
    confirmation_points = _confirmation_points(
        "knowledge",
        "knowledge",
        "knowledge",
    )
    llm_client = _RecordingQuestionSetDesignLlm(
        confirmation_points=confirmation_points,
    )

    # Act
    result = design_question_set(state, llm_client=llm_client)

    # Assert
    returned_points = _assert_result_confirmation_points_match(
        result,
        confirmation_points,
    )
    assert [point["format"] for point in returned_points] == [
        "knowledge",
        "knowledge",
        "knowledge",
    ]


@pytest.mark.parametrize(
    "formats",
    [
        ("knowledge", "knowledge"),
        (
            "knowledge",
            "knowledge",
            "knowledge",
            "knowledge",
            "knowledge",
            "knowledge",
        ),
    ],
)
def test_tc_22_out_of_range_confirmation_point_count_logs_warning_and_continues(
    formats: tuple[ConfirmationPointFormat, ...],
) -> None:
    # Arrange
    confirmation_points = _confirmation_points(*formats)
    llm_client = _RecordingQuestionSetDesignLlm(
        confirmation_points=confirmation_points,
    )

    # Act
    with capture_logs() as log_output:
        result = design_question_set(_state(), llm_client=llm_client)

    # Assert
    returned_points = _assert_result_confirmation_points_match(
        result,
        confirmation_points,
    )
    assert len(returned_points) == len(formats)
    warning_events = [
        entry for entry in log_output if entry.get("log_level") == "warning"
    ]
    assert len(warning_events) >= 1
    assert find_log_events(log_output, _FAILED_EVENT) == []


def test_tc_30_llm_request_failure_error_is_logged_once_and_re_raised() -> None:
    # Arrange
    cause = RuntimeError("upstream timeout")
    error = _question_set_design_error(
        error_code="llm_request_failed",
        message="question set design llm request failed",
        cause=cause,
    )
    llm_client = _RecordingQuestionSetDesignLlm(error=error)

    # Act / Assert
    with (
        capture_logs() as log_output,
        pytest.raises(QuestionSetDesignError) as exc_info,
    ):
        design_question_set(_state(), llm_client=llm_client)

    assert exc_info.value is error
    assert exc_info.value.error_code == "llm_request_failed"
    assert exc_info.value.message == "question set design llm request failed"
    assert exc_info.value.__cause__ is cause
    assert llm_client.calls == [
        (
            "TypeScript ジェネリクス",
            "型パラメータと型推論の理解を確認する",
            "detail",
        ),
    ]
    _assert_single_failure_log(
        log_output,
        error_code="llm_request_failed",
    )


def test_tc_31_llm_response_parse_failure_error_is_logged_once_and_re_raised() -> None:
    # Arrange
    cause = ValueError("invalid json")
    error = _question_set_design_error(
        error_code="llm_response_parse_failed",
        message="question set design llm response parse failed",
        cause=cause,
    )
    llm_client = _RecordingQuestionSetDesignLlm(error=error)

    # Act / Assert
    with (
        capture_logs() as log_output,
        pytest.raises(QuestionSetDesignError) as exc_info,
    ):
        design_question_set(_state(), llm_client=llm_client)

    assert exc_info.value is error
    assert exc_info.value.error_code == "llm_response_parse_failed"
    assert exc_info.value.message == "question set design llm response parse failed"
    assert exc_info.value.__cause__ is cause
    assert len(llm_client.calls) == 1
    _assert_single_failure_log(
        log_output,
        error_code="llm_response_parse_failed",
    )


def test_tc_32_llm_response_schema_failure_error_is_logged_once_and_re_raised() -> None:
    # Arrange
    cause = TypeError("invalid confirmation point schema")
    error = _question_set_design_error(
        error_code="llm_response_parse_failed",
        message="question set design llm response parse failed",
        cause=cause,
    )
    llm_client = _RecordingQuestionSetDesignLlm(error=error)

    # Act / Assert
    with (
        capture_logs() as log_output,
        pytest.raises(QuestionSetDesignError) as exc_info,
    ):
        design_question_set(_state(), llm_client=llm_client)

    assert exc_info.value is error
    assert exc_info.value.error_code == "llm_response_parse_failed"
    assert exc_info.value.message == "question set design llm response parse failed"
    assert exc_info.value.__cause__ is cause
    assert len(llm_client.calls) == 1
    _assert_single_failure_log(
        log_output,
        error_code="llm_response_parse_failed",
    )
