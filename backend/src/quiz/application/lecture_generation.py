"""lecture_generation ノード: 座学コンテンツを生成する。"""

from __future__ import annotations

from typing import TYPE_CHECKING

import structlog

if TYPE_CHECKING:
    from quiz.application.lecture_generation_types import (
        LectureGenerationLlmClient,
    )
    from quiz.domain.coding_session_state import CodingSessionState

logger = structlog.get_logger(__name__)


def generate_lecture(
    state: CodingSessionState,
    *,
    llm: LectureGenerationLlmClient,
) -> dict[str, object]:
    """座学コンテンツを生成し、lecture_phase_active=True を設定する。"""
    title = state["roadmap_item_title"]
    description = state["roadmap_item_description"]

    result = llm.generate_lecture(title, description)

    return {
        "lecture_content": result.lecture_content,
        "lecture_phase_active": True,
    }


__all__ = ["generate_lecture"]
