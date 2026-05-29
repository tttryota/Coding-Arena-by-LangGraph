"""coding_problem_set_design ノード: 確認ポイントを設計する。"""

from __future__ import annotations

from typing import TYPE_CHECKING

import structlog

if TYPE_CHECKING:
    from quiz.application.coding_problem_set_design_types import (
        CodingProblemSetDesignLlmClient,
    )
    from quiz.domain.coding_session_state import CodingSessionState

logger = structlog.get_logger(__name__)

_INITIAL_POINT_INDEX = 0


def design_coding_problem_set(
    state: CodingSessionState,
    *,
    llm: CodingProblemSetDesignLlmClient,
) -> dict[str, object]:
    """確認ポイントリストを設計し、lecture_phase_active=False に切り替える。"""
    result = llm.design_problem_set(
        state["roadmap_item_title"],
        state["roadmap_item_description"],
        state["lecture_content"],
    )
    points = [
        {
            "id": cp.id,
            "content": cp.content,
            "start_format": cp.start_format,
            "end_format": cp.end_format,
        }
        for cp in result.confirmation_points
    ]
    return {
        "confirmation_points": points,
        "current_point_index": _INITIAL_POINT_INDEX,
        "lecture_phase_active": False,
        "total_questions_asked": 0,
        "coding_attempts": [],
    }


__all__ = ["design_coding_problem_set"]
