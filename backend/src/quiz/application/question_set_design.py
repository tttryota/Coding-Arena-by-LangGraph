from __future__ import annotations

from typing import TYPE_CHECKING

import structlog

from quiz.application.question_set_design_types import (
    QuestionSetDesignError,
    QuestionSetDesignLlmClient,
)

if TYPE_CHECKING:
    from quiz.domain.session_state import SessionState

logger = structlog.get_logger(__name__)

_FAILED_EVENT = "question_set_design_failed"
_POINT_COUNT_WARNING_EVENT = "question_set_design_confirmation_point_count_warning"
_MIN_CONFIRMATION_POINT_COUNT = 3
_MAX_CONFIRMATION_POINT_COUNT = 5
_INITIAL_POINT_INDEX = 0


def design_question_set(
    state: SessionState,
    *,
    llm_client: QuestionSetDesignLlmClient,
) -> dict[str, object]:
    """C2: 確認ポイントリストを設計する LangGraph ノード関数。"""
    title = state["roadmap_item_title"]
    description = state["roadmap_item_description"]
    level = state["roadmap_item_level"]

    try:
        result = llm_client.generate_confirmation_points(
            title,
            description,
            level,
        )
    except QuestionSetDesignError as exception:
        logger.exception(
            _FAILED_EVENT,
            error_code=exception.error_code,
            message=exception.message,
            roadmap_item_title=title,
            roadmap_item_level=level,
            roadmap_item_description=description,
        )
        raise

    if (
        not _MIN_CONFIRMATION_POINT_COUNT
        <= len(result.confirmation_points)
        <= (_MAX_CONFIRMATION_POINT_COUNT)
    ):
        logger.warning(
            _POINT_COUNT_WARNING_EVENT,
            confirmation_point_count=len(result.confirmation_points),
        )

    return {
        "topic_overview": result.topic_overview,
        "confirmation_points": result.confirmation_points,
        "current_point_index": _INITIAL_POINT_INDEX,
    }


__all__ = [
    "design_question_set",
]
