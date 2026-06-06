"""theme_selection ノード: 学習順または指定テーマを選択する。"""

from __future__ import annotations

from typing import TYPE_CHECKING

import structlog

from competitive.domain.competitive_types import ThemeSelectionError

if TYPE_CHECKING:
    from competitive.application.theme_selection_types import ThemeReaderClient
    from competitive.domain.competitive_types import CompetitiveSessionState

logger = structlog.get_logger(__name__)


def select_theme(
    state: CompetitiveSessionState,
    *,
    reader: ThemeReaderClient,
) -> dict[str, object]:
    """テーマを選択し、セッション初期状態を返す。

    state に algo_theme_id が指定されていればそれを使い、
    未指定なら学習順で次のテーマを選択する。
    """
    theme_id = state.get("algo_theme_id")
    try:
        theme = reader.get_by_id(theme_id) if theme_id else reader.pick_next()
    except ThemeSelectionError:
        logger.exception("theme selection failed")
        raise

    session_id = state.get("session_id")
    if not session_id:
        msg = "session_id must be provided in state"
        raise ValueError(msg)

    return {
        "session_id": session_id,
        "status": "in_progress",
        "algo_theme_id": theme["id"],
        "algo_theme_label": theme["label"],
        "algo_theme_category": theme["category"],
    }


__all__ = ["select_theme"]
