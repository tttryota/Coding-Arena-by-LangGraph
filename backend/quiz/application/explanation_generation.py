from __future__ import annotations

from typing import TYPE_CHECKING

import structlog

from quiz.application.explanation_generation_types import (
    ExplanationGenerationError,
    ExplanationLlmClient,
    ExplanationRagClient,
)

if TYPE_CHECKING:
    from quiz.domain.session_state import SessionState

logger = structlog.get_logger(__name__)

_FAILED_EVENT = "explanation_generation_failed"


def generate_explanation(
    state: SessionState,
    *,
    rag: ExplanationRagClient,
    llm: ExplanationLlmClient,
) -> dict[str, object]:
    question_text = state["current_question_text"]
    confirmation_points = state["confirmation_points"]
    current_point_index = state["current_point_index"]
    confirmation_point_content = confirmation_points[current_point_index]["content"]

    query = question_text + "\n" + confirmation_point_content

    try:
        note_chunks = rag.search_related_chunks(query)
    except ExplanationGenerationError as exception:
        logger.exception(
            _FAILED_EVENT,
            error_code=exception.error_code,
            message=exception.message,
        )
        raise

    try:
        explanation_text = llm.generate_explanation(
            question_text=question_text,
            confirmation_point_content=confirmation_point_content,
            note_chunks=note_chunks,
        )
    except ExplanationGenerationError as exception:
        logger.exception(
            _FAILED_EVENT,
            error_code=exception.error_code,
            message=exception.message,
        )
        raise

    return {
        "explanation_text": explanation_text,
    }


__all__ = [
    "generate_explanation",
]
