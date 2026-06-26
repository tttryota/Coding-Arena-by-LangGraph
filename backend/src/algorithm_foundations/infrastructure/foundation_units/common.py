"""Shared helpers for algorithm foundation unit families."""

from __future__ import annotations

from algorithm_foundations.domain.foundation_types import AlgorithmFoundationExample

type SpecialThemeUnitDef = tuple[str, int, str, str, str]
type ProblemTemplate = dict[str, str | list[AlgorithmFoundationExample]]


def array_template(  # noqa: PLR0913
    *,
    statement: str,
    input_format: str,
    output_format: str,
    constraints: str,
    examples: list[AlgorithmFoundationExample],
    reference_solution: str,
) -> ProblemTemplate:
    return {
        "statement": statement,
        "input_format": input_format,
        "output_format": output_format,
        "constraints": constraints,
        "examples": examples,
        "reference_solution": reference_solution,
    }
