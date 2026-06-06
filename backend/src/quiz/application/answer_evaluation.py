from __future__ import annotations

import re
from typing import TYPE_CHECKING

import structlog

from quiz.application.answer_evaluation_types import (
    AnswerEvaluationError,
    AnswerEvaluationLlmClient,
)

if TYPE_CHECKING:
    from quiz.application.answer_evaluation_types import DeepdivePointDraft
    from quiz.domain.session_state import ConfirmationPoint, SessionState

logger = structlog.get_logger(__name__)

_FAILED_EVENT = "answer_evaluation_failed"
_ANSWER_INPUT_TYPE = "answer"
_MAX_DEEPDIVE_POINTS = 2
_MAX_QUESTIONS = 20
_DEEPDIVE_BUDGET_CEILING = 30


def _normalize_content(text: str) -> str:
    """strip + 連続空白を1つに圧縮。"""
    return re.sub(r"\s+", " ", text.strip())


def _dedupe_deepdive_points(
    drafts: list[DeepdivePointDraft],
    all_confirmation_points: list[ConfirmationPoint],
) -> list[DeepdivePointDraft]:
    """既存 CP と重複する deepdive ポイントを除去。順序は維持。"""
    existing: set[tuple[str, str]] = {
        (_normalize_content(cp["content"]), cp["format"])
        for cp in all_confirmation_points
    }
    result: list[DeepdivePointDraft] = []
    for draft in drafts:
        normalized = _normalize_content(draft["content"])
        if not normalized:
            continue
        key = (normalized, draft["format"])
        if key not in existing:
            existing.add(key)
            result.append(draft)
    return result


def _assign_ids(
    drafts: list[DeepdivePointDraft],
    parent_cp_id: str,
) -> list[ConfirmationPoint]:
    """DeepdivePointDraft に id を採番して ConfirmationPoint に変換。"""
    return [
        {"id": f"{parent_cp_id}_deepdive_{i:02d}", "content": d["content"], "format": d["format"]}
        for i, d in enumerate(drafts)
    ]


def evaluate_answer(  # noqa: PLR0915
    state: SessionState,
    *,
    llm: AnswerEvaluationLlmClient,
) -> dict[str, object]:
    """C4: ユーザー回答を評価し next/deepdive/complete を判断する LangGraph ノード関数。"""
    confirmation_points = state["confirmation_points"]
    current_point_index = state["current_point_index"]
    confirmation_point = confirmation_points[current_point_index]
    answers = state.get("answers", [])
    total_questions_asked = state["total_questions_asked"]

    remaining_cps = confirmation_points[current_point_index + 1 :]
    remaining_points = [(cp["content"], cp["format"]) for cp in remaining_cps]

    try:
        output = llm.evaluate_answer(
            question_text=state["current_question_text"],
            confirmation_point_content=confirmation_point["content"],
            answer_text=state["user_input"],
            answer_type=state["current_answer_type"],
            past_answers=answers,
            total_questions_asked=total_questions_asked,
            remaining_points=remaining_points,
        )
    except AnswerEvaluationError as exception:
        logger.exception(
            _FAILED_EVENT,
            error_code=exception.error_code,
            message=exception.message,
        )
        raise

    updated_answers = [
        *answers,
        {
            "question_number": len(answers) + 1,
            "confirmation_point_id": confirmation_point["id"],
            "question_text": state["current_question_text"],
            "answer_type": state["current_answer_type"],
            "answer_text": state["user_input"],
            "score": output.score,
            "feedback": output.feedback,
        },
    ]

    next_action = output.next_action
    next_point_index = current_point_index + 1
    updated_confirmation_points = confirmation_points

    if next_action == "deepdive":
        # 1. 重複除去
        unique_drafts = _dedupe_deepdive_points(output.deepdive_points, confirmation_points)
        # 2. budget 制限
        budget = max(0, _DEEPDIVE_BUDGET_CEILING - total_questions_asked - len(remaining_cps))
        allowed = min(budget, _MAX_DEEPDIVE_POINTS)
        capped_drafts = unique_drafts[:allowed]
        # 3. id 採番
        new_cps = _assign_ids(capped_drafts, confirmation_point["id"])
        # 4. 0件判定
        if new_cps:
            updated_confirmation_points = [*confirmation_points, *new_cps]
        elif not remaining_cps:
            next_action = "complete"
            next_point_index = len(confirmation_points)
        else:
            next_action = "next"
    elif next_action == "complete":
        next_point_index = len(confirmation_points)

    return {
        "next_action": next_action,
        "answers": updated_answers,
        "current_point_index": next_point_index,
        "confirmation_points": updated_confirmation_points,
        "input_type": _ANSWER_INPUT_TYPE,
    }


__all__ = [
    "evaluate_answer",
]
