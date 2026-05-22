from __future__ import annotations

import inspect
from typing import Literal, get_args, get_type_hints, is_typeddict

from quiz.domain import session_state as session_state_module
from quiz.domain.session_state import (
    ConfirmationPoint,
    QuizAnswerRecord,
    SessionState,
)

_SESSION_STATE_KEYS = (
    "session_id",
    "roadmap_item_id",
    "roadmap_item_level",
    "roadmap_item_title",
    "roadmap_item_description",
    "is_resumed",
    "confirmation_points",
    "current_point_index",
    "current_question_text",
    "current_answer_type",
    "user_input",
    "input_source",
    "input_type",
    "next_action",
    "answers",
    "total_questions_asked",
)

_CONFIRMATION_POINT_KEYS = ("id", "content", "format")

_QUIZ_ANSWER_RECORD_KEYS = (
    "question_number",
    "confirmation_point_id",
    "question_text",
    "answer_type",
    "answer_text",
    "score",
    "feedback",
)


def _example_confirmation_points() -> list[ConfirmationPoint]:
    return [
        {
            "id": "cp_001",
            "content": "ジェネリクスの必要性を説明できる",
            "format": "knowledge",
        },
        {
            "id": "cp_002",
            "content": "ジェネリック関数を実装できる",
            "format": "knowledge_and_practice",
        },
    ]


def _example_answer_record() -> QuizAnswerRecord:
    return {
        "question_number": 1,
        "confirmation_point_id": "cp_001",
        "question_text": "なぜジェネリクスが必要なのか説明してください。",
        "answer_type": "textarea",
        "answer_text": "いろいろな型で同じ関数を書けるからです。",
        "score": 62,
        "feedback": "再利用性には触れられていますが、型安全性の説明が不足しています。",
    }


def test_tc_01_session_state_public_contract_and_field_names() -> None:
    # Arrange / Act
    annotations = SessionState.__annotations__

    # Assert
    assert is_typeddict(SessionState)
    assert SessionState.__module__ == "quiz.domain.session_state"
    assert len(annotations) == 16
    assert tuple(annotations) == _SESSION_STATE_KEYS


def test_tc_02_subrecord_field_names_and_types() -> None:
    # Arrange / Act
    confirmation_point_annotations = ConfirmationPoint.__annotations__
    quiz_answer_record_annotations = QuizAnswerRecord.__annotations__
    confirmation_point_hints = get_type_hints(ConfirmationPoint)
    quiz_answer_record_hints = get_type_hints(QuizAnswerRecord)

    # Assert
    assert is_typeddict(ConfirmationPoint)
    assert is_typeddict(QuizAnswerRecord)
    assert ConfirmationPoint.__module__ == "quiz.domain.session_state"
    assert QuizAnswerRecord.__module__ == "quiz.domain.session_state"
    assert len(confirmation_point_annotations) == 3
    assert tuple(confirmation_point_annotations) == _CONFIRMATION_POINT_KEYS
    assert confirmation_point_hints == {
        "id": str,
        "content": str,
        "format": Literal["knowledge", "knowledge_and_practice"],
    }
    assert len(quiz_answer_record_annotations) == 7
    assert tuple(quiz_answer_record_annotations) == _QUIZ_ANSWER_RECORD_KEYS
    assert quiz_answer_record_hints == {
        "question_number": int,
        "confirmation_point_id": str,
        "question_text": str,
        "answer_type": Literal["textarea", "code"],
        "answer_text": str,
        "score": int,
        "feedback": str,
    }


def test_tc_03_literal_value_sets_match_specification_exactly() -> None:
    # Arrange
    session_state_hints = get_type_hints(SessionState)
    confirmation_point_hints = get_type_hints(ConfirmationPoint)
    quiz_answer_record_hints = get_type_hints(QuizAnswerRecord)

    # Act / Assert
    assert set(get_args(session_state_hints["roadmap_item_level"])) == {
        "detail",
        "middle",
        "major",
    }
    assert "micro" not in get_args(session_state_hints["roadmap_item_level"])
    assert set(get_args(session_state_hints["current_answer_type"])) == {
        "textarea",
        "code",
    }
    assert set(get_args(session_state_hints["input_source"])) == {"form", "chat"}
    assert set(get_args(session_state_hints["input_type"])) == {
        "answer",
        "question",
        "explanation_request",
    }
    assert set(get_args(session_state_hints["next_action"])) == {
        "next",
        "deepdive",
        "complete",
    }
    assert "abandoned" not in get_args(session_state_hints["next_action"])
    assert set(get_args(confirmation_point_hints["format"])) == {
        "knowledge",
        "knowledge_and_practice",
    }
    assert "practice_only" not in get_args(confirmation_point_hints["format"])
    assert set(get_args(quiz_answer_record_hints["answer_type"])) == {
        "textarea",
        "code",
    }


def test_tc_04_session_state_contract_docstring_covers_lifecycle_and_transitions() -> None:
    # Arrange / Act
    docstring = inspect.getdoc(SessionState)

    # Assert
    assert docstring is not None
    assert "shared downstream contract" in docstring.lower()
    assert "not only a shape" in docstring.lower()
    assert "C2" in docstring
    assert "initialize" in docstring
    assert "confirmation_points" in docstring
    assert "current_point_index" in docstring
    assert "answers" in docstring
    assert "append-only" in docstring
    assert "deepdive" in docstring
    assert "tail" in docstring
    assert "total_questions_asked" in docstring
    assert "C3" in docstring
    assert "next_action" in docstring
    assert "next confirmation point" in docstring
    assert "same confirmation point" in docstring
    assert "completion boundary" in docstring
    assert "total_questions_asked == 20" in docstring
    assert "valid state" in docstring
    assert "convergence" in docstring.lower()


def test_tc_05_session_state_contract_docstring_declares_non_provided_boundary() -> None:
    # Arrange / Act
    docstring = inspect.getdoc(SessionState)

    # Assert
    assert docstring is not None
    assert "input_source" in docstring
    assert "input_type" in docstring
    assert "next_action" in docstring
    assert "current_point_index" in docstring
    assert "confirmation_points" in docstring
    assert "downstream node contracts" in docstring
    assert "phase-specific TypedDicts" in docstring
    assert "Unions" in docstring
    assert "runtime validators" in docstring
    assert "factory/helper constructors" in docstring


def test_tc_06_public_exports_remain_contract_documentation_surface_only() -> None:
    # Arrange / Act
    public_exports = session_state_module.__all__

    # Assert
    assert public_exports == [
        "ConfirmationPoint",
        "ConfirmationPointFormat",
        "InputSource",
        "InputType",
        "NextAction",
        "QuizAnswerRecord",
        "QuizAnswerType",
        "RoadmapItemLevel",
        "SessionState",
    ]
    assert "SessionStatePhase" not in public_exports
    assert "SessionStateValidator" not in public_exports
    assert "build_session_state" not in public_exports


def test_tc_10_session_state_is_partial_typeddict() -> None:
    # Arrange / Act
    required_keys = SessionState.__required_keys__
    optional_keys = SessionState.__optional_keys__

    # Assert
    assert required_keys == frozenset()
    assert optional_keys == frozenset(_SESSION_STATE_KEYS)


def test_tc_11_c2_partial_state_is_a_valid_session_state() -> None:
    # Arrange
    state: SessionState = {
        "session_id": "sess_001",
        "roadmap_item_id": "ri_generics_01",
        "roadmap_item_level": "middle",
        "roadmap_item_title": "TypeScript ジェネリクス",
        "roadmap_item_description": "型パラメータと推論の理解を確認する",
        "is_resumed": False,
        "confirmation_points": _example_confirmation_points(),
        "current_point_index": 0,
    }

    # Act / Assert
    assert state == {
        "session_id": "sess_001",
        "roadmap_item_id": "ri_generics_01",
        "roadmap_item_level": "middle",
        "roadmap_item_title": "TypeScript ジェネリクス",
        "roadmap_item_description": "型パラメータと推論の理解を確認する",
        "is_resumed": False,
        "confirmation_points": _example_confirmation_points(),
        "current_point_index": 0,
    }
    assert "current_question_text" not in state
    assert "current_answer_type" not in state
    assert "user_input" not in state
    assert "input_source" not in state
    assert "input_type" not in state
    assert "next_action" not in state
    assert "answers" not in state
    assert "total_questions_asked" not in state


def test_tc_12_confirmation_point_is_complete_record() -> None:
    # Arrange / Act
    required_keys = ConfirmationPoint.__required_keys__
    optional_keys = ConfirmationPoint.__optional_keys__

    # Assert
    assert required_keys == frozenset(_CONFIRMATION_POINT_KEYS)
    assert optional_keys == frozenset()


def test_tc_13_quiz_answer_record_is_complete_record() -> None:
    # Arrange / Act
    required_keys = QuizAnswerRecord.__required_keys__
    optional_keys = QuizAnswerRecord.__optional_keys__

    # Assert
    assert required_keys == frozenset(_QUIZ_ANSWER_RECORD_KEYS)
    assert optional_keys == frozenset()


def test_tc_20_answers_empty_state_before_first_question_is_valid() -> None:
    # Arrange
    state: SessionState = {
        "session_id": "sess_001",
        "roadmap_item_id": "ri_generics_01",
        "roadmap_item_level": "middle",
        "roadmap_item_title": "TypeScript ジェネリクス",
        "roadmap_item_description": "型パラメータと推論の理解を確認する",
        "is_resumed": False,
        "confirmation_points": _example_confirmation_points(),
        "current_point_index": 0,
        "answers": [],
    }

    # Act / Assert
    assert state["answers"] == []
    assert len(state["answers"]) == 0
    assert len(state) == 9


def test_tc_21_completion_boundary_can_be_represented() -> None:
    # Arrange
    state: SessionState = {
        "confirmation_points": _example_confirmation_points(),
        "current_point_index": 2,
    }

    # Act / Assert
    assert state["current_point_index"] == len(state["confirmation_points"])
    assert state["current_point_index"] == 2


def test_tc_22_question_delivery_boundary_can_be_represented() -> None:
    # Arrange
    state: SessionState = {
        "answers": [_example_answer_record()],
        "total_questions_asked": 2,
        "current_question_text": "ジェネリック関数を1つ実装してください。",
        "current_answer_type": "code",
    }

    # Act / Assert
    assert state["total_questions_asked"] == len(state["answers"]) + 1
    assert state["total_questions_asked"] == 2
    assert state["current_question_text"] == "ジェネリック関数を1つ実装してください。"
    assert state["current_answer_type"] == "code"


def test_tc_23_all_keys_set_state_after_c4_completion_is_valid() -> None:
    # Arrange
    state: SessionState = {
        "session_id": "sess_001",
        "roadmap_item_id": "ri_generics_01",
        "roadmap_item_level": "middle",
        "roadmap_item_title": "TypeScript ジェネリクス",
        "roadmap_item_description": "型パラメータと推論の理解を確認する",
        "is_resumed": False,
        "confirmation_points": [
            *_example_confirmation_points(),
            {
                "id": "cp_002_deepdive_01",
                "content": "型推論を使う利点を具体例で説明できる",
                "format": "knowledge",
            },
        ],
        "current_point_index": 1,
        "current_question_text": "なぜジェネリクスが必要なのか説明してください。",
        "current_answer_type": "textarea",
        "user_input": "いろいろな型で同じ関数を書けるからです。",
        "input_source": "form",
        "input_type": "answer",
        "next_action": "deepdive",
        "answers": [_example_answer_record()],
        "total_questions_asked": 1,
    }

    # Act / Assert
    assert len(state) == 16
    assert state == {
        "session_id": "sess_001",
        "roadmap_item_id": "ri_generics_01",
        "roadmap_item_level": "middle",
        "roadmap_item_title": "TypeScript ジェネリクス",
        "roadmap_item_description": "型パラメータと推論の理解を確認する",
        "is_resumed": False,
        "confirmation_points": [
            {
                "id": "cp_001",
                "content": "ジェネリクスの必要性を説明できる",
                "format": "knowledge",
            },
            {
                "id": "cp_002",
                "content": "ジェネリック関数を実装できる",
                "format": "knowledge_and_practice",
            },
            {
                "id": "cp_002_deepdive_01",
                "content": "型推論を使う利点を具体例で説明できる",
                "format": "knowledge",
            },
        ],
        "current_point_index": 1,
        "current_question_text": "なぜジェネリクスが必要なのか説明してください。",
        "current_answer_type": "textarea",
        "user_input": "いろいろな型で同じ関数を書けるからです。",
        "input_source": "form",
        "input_type": "answer",
        "next_action": "deepdive",
        "answers": [
            {
                "question_number": 1,
                "confirmation_point_id": "cp_001",
                "question_text": "なぜジェネリクスが必要なのか説明してください。",
                "answer_type": "textarea",
                "answer_text": "いろいろな型で同じ関数を書けるからです。",
                "score": 62,
                "feedback": "再利用性には触れられていますが、型安全性の説明が不足しています。",
            },
        ],
        "total_questions_asked": 1,
    }
