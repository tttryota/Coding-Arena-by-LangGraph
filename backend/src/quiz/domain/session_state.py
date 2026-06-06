from __future__ import annotations

from typing import Literal, TypedDict

RoadmapItemLevel = Literal["detail", "middle", "major"]
ConfirmationPointFormat = Literal["knowledge", "knowledge_and_practice"]
QuizAnswerType = Literal["textarea", "code"]
InputSource = Literal["form", "chat"]
InputType = Literal["answer", "question", "explanation_request"]
NextAction = Literal["next", "deepdive", "complete"]


class ConfirmationPoint(TypedDict):
    id: str
    content: str
    format: ConfirmationPointFormat


class QuizAnswerRecord(TypedDict):
    question_number: int
    confirmation_point_id: str
    question_text: str
    answer_type: QuizAnswerType
    answer_text: str
    score: int
    feedback: str


class SessionState(TypedDict, total=False):
    """Shared downstream contract for quiz session state, not only a shape.

    Initialize and first-write responsibilities for all 19 keys:
    - C1 initialize/first write ``session_id``, ``roadmap_item_id``,
      ``roadmap_item_level``, ``roadmap_item_title``,
      ``roadmap_item_description``, and ``is_resumed``.
    - C2 initialize/first write ``confirmation_points``,
      ``current_point_index``, and ``topic_overview``.
    - C3 initialize/first write ``current_question_text``,
      ``current_answer_type``, and ``total_questions_asked``.
    - External input acceptance initialize/first write ``user_input`` and
      ``input_source``.
    - External input acceptance on the ``input_source="chat"`` path also
      initialize/first write ``input_type``.
    - C4 initialize/first write ``next_action`` and ``answers``.
    - C4 initialize/first write ``input_type`` on the
      ``input_source="form"`` path by normalizing it to ``"answer"`` by the
      end of C4.
    - ``explanation_generation`` node initialize/first write
      ``explanation_text``.
    - ``chat_response`` node initialize/first write
      ``chat_response_text``.

    Lifecycle rules after first write:
    - After C4 first writes ``answers``, it is append-only.
    - After C2 first writes ``confirmation_points``, it is append-only only at
      the tail during ``deepdive`` updates.
    - ``total_questions_asked`` increases on every C3 question cycle.

    Transition rules for ``next_action`` and convergence:
    - ``next`` updates the state to move ``current_point_index`` to the next confirmation point.
    - ``deepdive`` consumes the current question cycle, advances
      ``current_point_index`` by 1, appends a deepdive confirmation point at
      the tail of ``confirmation_points``, and does not mean repeating the
      same confirmation point in place; any already-pending confirmation point
      ahead of the previous index is asked before that appended point.
    - ``complete`` transitions to the completion boundary where
      ``current_point_index == len(confirmation_points)`` and no further
      question cycle remains.
    - 20-question convergence rule: once ``total_questions_asked == 20``, the
      only valid ``next_action`` values are ``"next"`` and ``"complete"``.
    - In that same convergence rule, ``deepdive`` is no longer a valid state
      or transition.
    - In that same convergence rule, the deepdive-only tail append to
      ``confirmation_points`` is allowed only while
      ``total_questions_asked < 20``; the evaluation that reaches
      ``total_questions_asked == 20`` must not append a new deepdive
      confirmation point.

    Index boundary rule:
    - In non-complete states, ``current_point_index`` always points to the next
      unconsumed confirmation point.
    - The equality ``current_point_index == len(confirmation_points)`` is valid
      only for the completion boundary.

    Boundary of this module:
    - ``input_source="form"`` may omit ``input_type`` before C4 starts.
    - By the end of C4 for ``input_source="form"``, ``input_type`` must be
      normalized to ``"answer"``.
    - For evaluated ``input_source="form"`` state, ``input_type="question"``
      and ``input_type="explanation_request"`` are invalid.
    - Other conditional combinations across ``input_source``, ``input_type``,
      ``next_action``, ``current_point_index``, and ``confirmation_points``
      remain documented as downstream node contracts.
    - This module intentionally does not provide phase-specific TypedDicts,
      Unions, runtime validators, or factory/helper constructors.
    """

    session_id: str
    roadmap_item_id: str
    roadmap_item_level: RoadmapItemLevel
    roadmap_item_title: str
    roadmap_item_description: str
    is_resumed: bool
    topic_overview: str
    confirmation_points: list[ConfirmationPoint]
    current_point_index: int
    current_question_text: str
    current_answer_type: QuizAnswerType
    user_input: str
    input_source: InputSource
    input_type: InputType
    next_action: NextAction
    answers: list[QuizAnswerRecord]
    total_questions_asked: int
    explanation_text: str
    chat_response_text: str


__all__ = [
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
