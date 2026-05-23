from __future__ import annotations

from typing import TYPE_CHECKING

import structlog

from quiz.application.input_classification_types import (
    InputClassificationError,
    InputClassificationLlmClient,
)

if TYPE_CHECKING:
    from quiz.domain.session_state import SessionState

logger = structlog.get_logger(__name__)

_FAILED_EVENT = "input_classification_failed"


def classify_input(
    state: SessionState,
    *,
    llm: InputClassificationLlmClient,
) -> dict[str, object]:
    try:
        input_type = llm.classify_input(
            question_text=state["current_question_text"],
            user_input=state["user_input"],
        )
    except InputClassificationError as exception:
        logger.exception(
            _FAILED_EVENT,
            error_code=exception.error_code,
            message=exception.message,
        )
        raise

    return {
        "input_type": input_type,
    }


__all__ = [
    "classify_input",
]
