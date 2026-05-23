from __future__ import annotations

from typing import TYPE_CHECKING

import structlog

from quiz.application.question_delivery_types import (
    QuestionDeliveryError,
    QuestionDeliveryLlmClient,
)

if TYPE_CHECKING:
    from quiz.domain.session_state import SessionState

logger = structlog.get_logger(__name__)

_FAILED_EVENT = "question_delivery_failed"
_TOTAL_QUESTIONS_ASKED_STATE_KEY = "total_questions_asked"
_TOTAL_QUESTIONS_ASKED_DEFAULT = 0
_TOTAL_QUESTIONS_ASKED_INCREMENT = 1


def deliver_question(
    state: SessionState,
    *,
    llm: QuestionDeliveryLlmClient,
) -> dict[str, object]:
    confirmation_points = state["confirmation_points"]
    current_point_index = state["current_point_index"]
    if current_point_index >= len(confirmation_points):
        return {}

    confirmation_point = confirmation_points[current_point_index]

    try:
        output = llm.generate_question(
            state["roadmap_item_title"],
            state["roadmap_item_description"],
            confirmation_point["content"],
            confirmation_point["format"],
            state["answers"],
        )
    except QuestionDeliveryError as exception:
        logger.exception(
            _FAILED_EVENT,
            error_code=exception.error_code,
            message=exception.message,
        )
        raise

    if "total_questions_asked" in state:
        total_questions_asked = state["total_questions_asked"]
    else:
        total_questions_asked = _TOTAL_QUESTIONS_ASKED_DEFAULT

    return {
        "current_question_text": output.question_text,
        "current_answer_type": output.answer_type,
        _TOTAL_QUESTIONS_ASKED_STATE_KEY: total_questions_asked
        + _TOTAL_QUESTIONS_ASKED_INCREMENT,
    }


__all__ = [
    "deliver_question",
]
