from __future__ import annotations

from typing import TYPE_CHECKING

import structlog

from quiz.application.answer_evaluation_types import (
    AnswerEvaluationError,
    AnswerEvaluationLlmClient,
)

if TYPE_CHECKING:
    from quiz.domain.session_state import SessionState

logger = structlog.get_logger(__name__)

_FAILED_EVENT = "answer_evaluation_failed"
_ANSWER_INPUT_TYPE = "answer"


def evaluate_answer(
    state: SessionState,
    *,
    llm: AnswerEvaluationLlmClient,
) -> dict[str, object]:
    confirmation_points = state["confirmation_points"]
    current_point_index = state["current_point_index"]
    confirmation_point = confirmation_points[current_point_index]
    answers = state["answers"]

    try:
        output = llm.evaluate_answer(
            question_text=state["current_question_text"],
            confirmation_point_content=confirmation_point["content"],
            answer_text=state["user_input"],
            answer_type=state["current_answer_type"],
            past_answers=answers,
            total_questions_asked=state["total_questions_asked"],
        )
    except AnswerEvaluationError as exception:
        logger.exception(
            _FAILED_EVENT,
            error_code=exception.error_code,
        )
        raise

    updated_answers = [
        *answers,
        {
            "question_number": len(answers) + 1,
            "confirmation_point_id": confirmation_point["id"],
            "question_text": state["current_question_text"],
            "answer_type": state["current_answer_type"],
            "answer_text": state["user_input"],
            "score": output.score,
            "feedback": output.feedback,
        },
    ]

    next_action = output.next_action
    next_point_index = current_point_index + 1
    updated_confirmation_points = confirmation_points
    if next_action == "deepdive":
        updated_confirmation_points = [*confirmation_points, *output.deepdive_points]
    elif next_action == "complete":
        next_point_index = len(confirmation_points)

    return {
        "next_action": next_action,
        "answers": updated_answers,
        "current_point_index": next_point_index,
        "confirmation_points": updated_confirmation_points,
        "input_type": _ANSWER_INPUT_TYPE,
    }


__all__ = [
    "evaluate_answer",
]
