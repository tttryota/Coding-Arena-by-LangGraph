"""solution_evaluation ノード: 保存済み rubric に基づいてユーザーコードを採点する。"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

import structlog

from competitive.domain.competitive_types import SolutionEvaluationError

if TYPE_CHECKING:
    from competitive.application.solution_evaluation_types import (
        SolutionEvaluationLlmClient,
    )
    from competitive.domain.competitive_types import CompetitiveSessionState

logger = structlog.get_logger(__name__)


def evaluate_solution(
    state: CompetitiveSessionState,
    *,
    llm: SolutionEvaluationLlmClient,
) -> dict[str, object]:
    """ユーザーコードを採点し、結果を返す。"""
    try:
        result = llm.evaluate_solution(
            problem_statement=state["problem_statement"],
            input_format=state["input_format"],
            output_format=state["output_format"],
            constraints=state["constraints"],
            examples=state["examples"],
            reference_solution=state["reference_solution"],
            grading_rubric=state["grading_rubric"],
            user_code=state["user_code"],
            programming_language=state["programming_language"],
        )
    except SolutionEvaluationError:
        logger.exception("solution evaluation failed")
        raise

    return {
        "status": "completed",
        "score": result.score,
        "feedback": result.feedback,
        "time_complexity": result.time_complexity,
        "space_complexity": result.space_complexity,
        "improvement_suggestions": result.improvement_suggestions,
        "rubric_scores_json": json.dumps(
            result.rubric_scores, ensure_ascii=False,
        ),
    }


__all__ = ["evaluate_solution"]
