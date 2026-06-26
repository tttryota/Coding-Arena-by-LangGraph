"""Shared helpers for static algorithm foundation banks."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from algorithm_foundations.domain.foundation_types import (
        AlgorithmFoundationExample,
        AlgorithmFoundationProblem,
        AlgorithmFoundationRubricItem,
        AlgorithmFoundationUnitBank,
        AlgorithmFoundationUnitKind,
    )


def default_rubric(unit_kind: AlgorithmFoundationUnitKind) -> list[AlgorithmFoundationRubricItem]:
    if unit_kind == "integration":
        return [
            {"criterion": "方針の選択", "points": 40, "description": "既習2unitまでで素直に解法を立てている"},
            {"criterion": "実装の正しさ", "points": 40, "description": "境界条件を含めて正しく動作する"},
            {"criterion": "整理されたコード", "points": 20, "description": "補助構造の更新順が読み取りやすい"},
        ]
    return [
        {"criterion": "基本方針", "points": 45, "description": "学習単位の中核発想を使えている"},
        {"criterion": "実装の正しさ", "points": 40, "description": "標準的なケースを正しく処理できる"},
        {"criterion": "コードの整理", "points": 15, "description": "変数や処理の流れが追いやすい"},
    ]


def problem(  # noqa: PLR0913
    *,
    problem_id: str,
    title: str,
    problem_statement: str,
    input_format: str,
    output_format: str,
    constraints: str,
    examples: list[AlgorithmFoundationExample],
    canonical_reference_solution: str,
    grading_rubric: list[AlgorithmFoundationRubricItem] | None = None,
    canonical_language: str = "python",
) -> AlgorithmFoundationProblem:
    return {
        "problem_id": problem_id,
        "title": title,
        "problem_statement": problem_statement,
        "input_format": input_format,
        "output_format": output_format,
        "constraints": constraints,
        "examples": examples,
        "canonical_reference_solution": canonical_reference_solution,
        "canonical_language": canonical_language,
        "grading_rubric": grading_rubric or default_rubric("foundation"),
    }


def unit_bank(  # noqa: PLR0913
    *,
    unit_id: str,
    title: str,
    unit_kind: AlgorithmFoundationUnitKind,
    target_skill: str,
    concept_overview: str,
    problem_bank: list[AlgorithmFoundationProblem],
) -> AlgorithmFoundationUnitBank:
    return {
        "unit_id": unit_id,
        "title": title,
        "unit_kind": unit_kind,
        "target_skill": target_skill,
        "concept_overview": concept_overview,
        "problem_bank": problem_bank,
    }
