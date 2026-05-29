"""code_evaluation ノード: コード回答を評価し、次のアクションを決定する。

ルーティングロジック (仕様 B4):
- score >= 70 かつ current_format < end_format → next_step (同CPの次format)
- score >= 70 かつ current_format >= end_format → next_cp or complete
- score < 70 → retry 1回 → それでも < 70 → next_cp or complete
- total_questions_asked >= 20 → complete (収束ルール)
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import structlog

if TYPE_CHECKING:
    from quiz.application.code_evaluation_types import CodeEvaluationLlmClient
    from quiz.domain.coding_session_state import CodingSessionState

logger = structlog.get_logger(__name__)

_FORMAT_ORDER = ("rewrite", "fill_blank", "bug_fix", "extend", "implement")
_MAX_QUESTIONS = 20


def _next_format(current: str, end: str) -> str | None:
    """current_format の次の format を返す。end を超えたら None。"""
    idx = _FORMAT_ORDER.index(current)
    end_idx = _FORMAT_ORDER.index(end)
    if idx >= end_idx:
        return None
    return _FORMAT_ORDER[idx + 1]


def _determine_next_action(  # noqa: PLR0913
    score: int,
    current_format: str,
    end_format: str,
    cp_index: int,
    total_cps: int,
    total_questions: int,
    retry_count: int,
) -> str:
    """仕様に基づいて next_action を決定する。"""
    if total_questions >= _MAX_QUESTIONS:
        return "complete"

    if score >= 70:
        next_fmt = _next_format(current_format, end_format)
        if next_fmt is not None:
            return "next_step"
        if cp_index + 1 < total_cps:
            return "next_cp"
        return "complete"

    if retry_count < 1:
        return "retry"

    if cp_index + 1 < total_cps:
        return "next_cp"
    return "complete"


def evaluate_code(
    state: CodingSessionState,
    *,
    llm: CodeEvaluationLlmClient,
) -> dict[str, object]:
    """コード回答を評価し、ルーティング結果を state に書き戻す。"""
    cp_index = state.get("current_point_index", 0)
    cps = state["confirmation_points"]
    cp = cps[cp_index]
    current_format = state.get("current_format", cp["start_format"])

    result = llm.evaluate_code(
        question_text=state["current_question_text"],
        example_code=state.get("current_example_code", ""),
        user_code=state["user_input"],
        current_format=current_format,
        confirmation_point_content=cp["content"],
    )

    attempts = list(state.get("coding_attempts", []))
    attempts.append({
        "confirmation_point_id": cp["id"],
        "format": current_format,
        "question_text": state["current_question_text"],
        "example_code": state.get("current_example_code", ""),
        "answer_text": state["user_input"],
        "score": result.score,
        "feedback": result.feedback,
    })

    same_format_failures = sum(
        1
        for a in attempts
        if a["confirmation_point_id"] == cp["id"]
        and a["format"] == current_format
        and a["score"] < 70
    )

    total_questions = state.get("total_questions_asked", 0)
    next_action = _determine_next_action(
        score=result.score,
        current_format=current_format,
        end_format=cp["end_format"],
        cp_index=cp_index,
        total_cps=len(cps),
        total_questions=total_questions,
        retry_count=same_format_failures - 1,
    )

    updates: dict[str, object] = {
        "current_score": result.score,
        "current_feedback": result.feedback,
        "next_action": next_action,
        "coding_attempts": attempts,
    }

    _apply_routing_updates(updates, next_action, result.score, current_format, cp, cps, cp_index)
    return updates


def _apply_routing_updates(  # noqa: PLR0913
    updates: dict[str, object],
    next_action: str,
    score: int,
    current_format: str,
    cp: dict[str, object],
    cps: list[dict[str, object]],
    cp_index: int,
) -> None:
    """next_action に応じて state 更新を追加する。"""
    if next_action == "complete":
        updates["current_point_index"] = len(cps)
    elif next_action == "next_step" and score >= 70:
        next_fmt = _next_format(current_format, cp["end_format"])
        if next_fmt:
            updates["current_format"] = next_fmt
    elif next_action == "next_cp":
        updates["current_point_index"] = cp_index + 1
        next_cp_item = cps[cp_index + 1]
        updates["current_format"] = next_cp_item["start_format"]


__all__ = ["evaluate_code"]
