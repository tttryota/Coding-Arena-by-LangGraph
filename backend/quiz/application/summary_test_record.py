from __future__ import annotations

from typing import TYPE_CHECKING

import structlog

from quiz.application.summary_test_record_types import (
    SummaryTestLlmClient,
    SummaryTestRecordError,
    SummaryTestStore,
)

if TYPE_CHECKING:
    from quiz.domain.session_state import SessionState

logger = structlog.get_logger(__name__)

_FAILED_EVENT = "summary_test_record_failed"


def record_summary_test(
    state: SessionState,
    *,
    llm: SummaryTestLlmClient,
    store: SummaryTestStore,
) -> None:
    level = state["roadmap_item_level"]

    if level == "detail":
        return

    try:
        analysis = llm.analyze_session(
            title=state["roadmap_item_title"],
            description=state["roadmap_item_description"],
            answers=state["answers"],
        )
    except SummaryTestRecordError as exception:
        logger.exception(
            _FAILED_EVENT,
            error_code=exception.error_code,
            message=exception.message,
        )
        raise

    try:
        store.save_result(
            session_id=state["session_id"],
            roadmap_item_id=state["roadmap_item_id"],
            score=analysis.score,
            analysis=analysis.analysis,
        )
    except SummaryTestRecordError as exception:
        logger.exception(
            _FAILED_EVENT,
            error_code=exception.error_code,
            message=exception.message,
        )
        raise


__all__ = [
    "record_summary_test",
]
