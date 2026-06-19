"""problem_generation ノード: LLM で問題 + 模範解答 + rubric を同時生成する。"""

from __future__ import annotations

from typing import TYPE_CHECKING

import structlog

from competitive.domain.competitive_types import ProblemGenerationError
from competitive.domain.languages import default_language, is_supported_language

if TYPE_CHECKING:
    from competitive.application.problem_generation_types import (
        ProblemGenerationLlmClient,
    )
    from competitive.domain.competitive_types import CompetitiveSessionState

logger = structlog.get_logger(__name__)


def generate_problem(
    state: CompetitiveSessionState,
    *,
    llm: ProblemGenerationLlmClient,
) -> dict[str, object]:
    """テーマに基づいて問題を生成する。"""
    theme_label = state["algo_theme_label"]
    theme_category = state["algo_theme_category"]
    programming_language = state.get("programming_language", default_language())
    if not is_supported_language(programming_language):
        msg = f"Unsupported programming_language: {programming_language}"
        raise ProblemGenerationError(
            error_code="invalid_language",
            message=msg,
        )

    try:
        result = llm.generate_problem(
            theme_label,
            theme_category,
            programming_language,
        )
    except ProblemGenerationError:
        logger.exception(
            "problem generation failed",
            theme_label=theme_label,
        )
        raise

    if not is_supported_language(result.programming_language):
        msg = (
            f"Invalid programming_language: {result.programming_language}, "
            "expected one of registered languages"
        )
        raise ProblemGenerationError(
            error_code="invalid_language", message=msg,
        )

    return {
        "programming_language": result.programming_language,
        "problem_statement": result.problem_statement,
        "input_format": result.input_format,
        "output_format": result.output_format,
        "constraints": result.constraints,
        "examples": result.examples,
        "reference_solution": result.reference_solution,
        "grading_rubric": result.grading_rubric,
    }


__all__ = ["generate_problem"]
