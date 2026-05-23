from __future__ import annotations

import datetime
from typing import TYPE_CHECKING

import structlog

from quiz.application.progress_update_types import (
    ProgressUpdateError,
    ProgressUpdateLlmClient,
    ProgressUpdateStore,
)

if TYPE_CHECKING:
    from quiz.domain.session_state import SessionState

logger = structlog.get_logger(__name__)

_FAILED_EVENT = "progress_update_failed"


def update_progress(  # noqa: PLR0915
    state: SessionState,
    *,
    llm: ProgressUpdateLlmClient,
    store: ProgressUpdateStore,
) -> dict[str, object]:
    """C7/C8: 全問答から総合評価し score を算出・反映する LangGraph ノード関数。"""
    session_id = state["session_id"]
    answers = state["answers"]

    if len(answers) == 0:
        store.complete_session(session_id)
        return {}

    roadmap_item_title = state["roadmap_item_title"]
    roadmap_item_description = state["roadmap_item_description"]
    confirmation_points = state["confirmation_points"]
    checkpoints = [cp["content"] for cp in confirmation_points]

    try:
        output = llm.evaluate_session(
            roadmap_item_title=roadmap_item_title,
            roadmap_item_description=roadmap_item_description,
            checkpoints=checkpoints,
            answers=answers,
        )
    except ProgressUpdateError as exception:
        logger.exception(
            _FAILED_EVENT,
            error_code=exception.error_code,
            message=exception.message,
        )
        raise

    level = state["roadmap_item_level"]
    item_id = state["roadmap_item_id"]

    if level == "detail":
        store.update_roadmap_item_progress(
            item_id=item_id,
            score=output.score,
            last_quiz_at=datetime.datetime.now(tz=datetime.UTC),
        )
    else:
        store.save_summary_test_result(
            session_id=session_id,
            item_id=item_id,
            score=output.score,
            comment=output.comment,
        )

    store.complete_session(session_id)
    return {}


__all__ = [
    "update_progress",
]
