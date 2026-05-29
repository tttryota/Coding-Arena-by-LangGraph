"""coding_session_state の型整合性テスト。"""

from __future__ import annotations

from typing import get_args, get_type_hints, is_typeddict

from quiz.domain.coding_session_state import (
    CodingConfirmationPoint,
    CodingDifficulty,
    CodingProblemAttempt,
    CodingSessionState,
)

_CODING_SESSION_STATE_KEYS = (
    "session_id",
    "roadmap_item_id",
    "roadmap_item_level",
    "roadmap_item_title",
    "roadmap_item_description",
    "is_resumed",
    "lecture_content",
    "lecture_phase_active",
    "confirmation_points",
    "current_point_index",
    "current_question_text",
    "current_example_code",
    "current_format",
    "total_questions_asked",
    "coding_attempts",
    "user_input",
    "input_source",
    "next_action",
    "current_score",
    "current_feedback",
    "chat_response_text",
)

_CODING_CONFIRMATION_POINT_KEYS = ("id", "content", "start_format", "end_format")
_CODING_PROBLEM_ATTEMPT_KEYS = (
    "confirmation_point_id",
    "format",
    "question_text",
    "example_code",
    "answer_text",
    "score",
    "feedback",
)


def test_coding_session_state_is_typeddict_with_expected_keys() -> None:
    assert is_typeddict(CodingSessionState)
    hints = get_type_hints(CodingSessionState)
    assert tuple(hints.keys()) == _CODING_SESSION_STATE_KEYS


def test_coding_session_state_is_total_false() -> None:
    assert not CodingSessionState.__total__


def test_coding_confirmation_point_is_typeddict() -> None:
    assert is_typeddict(CodingConfirmationPoint)
    hints = get_type_hints(CodingConfirmationPoint)
    assert tuple(hints.keys()) == _CODING_CONFIRMATION_POINT_KEYS
    assert hints["id"] is str
    assert hints["content"] is str
    assert "Literal" in str(hints["start_format"])
    assert "Literal" in str(hints["end_format"])


def test_coding_problem_attempt_is_typeddict() -> None:
    assert is_typeddict(CodingProblemAttempt)
    hints = get_type_hints(CodingProblemAttempt)
    assert tuple(hints.keys()) == _CODING_PROBLEM_ATTEMPT_KEYS
    assert hints["score"] is int
    assert hints["question_text"] is str
    assert hints["example_code"] is str
    assert hints["answer_text"] is str
    assert hints["feedback"] is str
    assert "Literal" in str(hints["format"])


def test_coding_session_state_field_types() -> None:
    """CodingSessionState の各フィールドの型が仕様と一致すること。"""
    hints = get_type_hints(CodingSessionState)
    assert hints["session_id"] is str
    assert hints["roadmap_item_id"] is str
    assert hints["is_resumed"] is bool
    assert hints["lecture_content"] is str
    assert hints["lecture_phase_active"] is bool
    assert hints["current_point_index"] is int
    assert hints["current_question_text"] is str
    assert hints["current_example_code"] is str
    assert hints["total_questions_asked"] is int
    assert hints["current_score"] is int
    assert hints["current_feedback"] is str
    assert hints["chat_response_text"] is str
    assert "Literal" in str(hints["current_format"])
    assert "CodingConfirmationPoint" in str(hints["confirmation_points"])
    assert "CodingProblemAttempt" in str(hints["coding_attempts"])


def test_coding_difficulty_literal_values() -> None:
    assert get_args(CodingDifficulty) == (
        "rewrite",
        "fill_blank",
        "bug_fix",
        "extend",
        "implement",
    )


def test_next_action_values() -> None:
    hints = get_type_hints(CodingSessionState)
    next_action_type = hints["next_action"]
    assert get_args(next_action_type) == ("next_step", "next_cp", "complete")


def test_input_source_values() -> None:
    hints = get_type_hints(CodingSessionState)
    input_source_type = hints["input_source"]
    assert get_args(input_source_type) == ("form", "chat")
