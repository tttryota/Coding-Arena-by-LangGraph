"""coding_problem_delivery ノード: format に応じたコーディング問題を出題する。"""

from __future__ import annotations

from typing import TYPE_CHECKING

import structlog

if TYPE_CHECKING:
    from quiz.application.coding_problem_delivery_types import (
        CodingProblemDeliveryLlmClient,
    )
    from quiz.domain.coding_session_state import CodingSessionState

logger = structlog.get_logger(__name__)

_FORMAT_ORDER = ("rewrite", "fill_blank", "bug_fix", "extend", "implement")


def deliver_coding_problem(
    state: CodingSessionState,
    *,
    llm: CodingProblemDeliveryLlmClient,
) -> dict[str, object]:
    """現在の CP と format に基づいてコーディング問題を生成する。"""
    cp_index = state.get("current_point_index", 0)
    cps = state["confirmation_points"]
    cp = cps[cp_index]

    current_format = state.get("current_format", cp["start_format"])

    result = llm.deliver_problem(
        state["roadmap_item_title"],
        cp["content"],
        current_format,
        state["lecture_content"],
    )

    total = state.get("total_questions_asked", 0) + 1

    return {
        "current_question_text": result.question_text,
        "current_example_code": result.example_code,
        "current_format": current_format,
        "total_questions_asked": total,
    }


__all__ = ["deliver_coding_problem"]
