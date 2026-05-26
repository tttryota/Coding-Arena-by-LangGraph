from __future__ import annotations

from typing import Literal, get_args, get_type_hints, is_typeddict

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
    "topic_overview",
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
    "explanation_text",
    "chat_response_text",
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
    assert len(annotations) == 19
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


def test_tc_10_session_state_is_partial_typeddict() -> None:
    # Arrange / Act
    required_keys = SessionState.__required_keys__
    optional_keys = SessionState.__optional_keys__

    # Assert
    assert required_keys == frozenset()
    assert len(optional_keys) == 19
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


def test_explanation_text_type_is_str() -> None:
    hints = get_type_hints(SessionState)
    assert hints["explanation_text"] is str


def test_chat_response_text_type_is_str() -> None:
    hints = get_type_hints(SessionState)
    assert hints["chat_response_text"] is str


def test_explanation_text_only_partial_state() -> None:
    state: SessionState = {
        "session_id": "sess_001",
        "explanation_text": "解説テキスト",
    }
    assert state["explanation_text"] == "解説テキスト"
    assert "chat_response_text" not in state


def test_chat_response_text_only_partial_state() -> None:
    state: SessionState = {
        "session_id": "sess_001",
        "chat_response_text": "チャット応答",
    }
    assert state["chat_response_text"] == "チャット応答"
    assert "explanation_text" not in state


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
