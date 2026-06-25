"""競プロうさぎのドメイン型定義。"""

from __future__ import annotations

from typing import Literal, TypedDict

AlgorithmFoundationUnitKind = Literal["foundation", "integration"]
AlgorithmFoundationSessionStatus = Literal["in_progress", "completed"]


class AlgorithmFoundationExample(TypedDict):
    input: str
    output: str


class AlgorithmFoundationRubricItem(TypedDict):
    criterion: str
    points: int
    description: str


class AlgorithmFoundationProblem(TypedDict):
    problem_id: str
    title: str
    problem_statement: str
    input_format: str
    output_format: str
    constraints: str
    examples: list[AlgorithmFoundationExample]
    canonical_reference_solution: str
    canonical_language: str
    grading_rubric: list[AlgorithmFoundationRubricItem]


class AlgorithmFoundationUnit(TypedDict):
    unit_id: str
    theme_id: str
    group_id: str
    group_title: str
    title: str
    display_order: int
    prerequisite_unit_ids: list[str]
    prerequisite_titles: list[str]
    allowed_knowledge: list[str]
    forbidden_knowledge: list[str]
    target_skill: str
    unit_kind: AlgorithmFoundationUnitKind
    problem_bank: list[AlgorithmFoundationProblem]


class AlgorithmFoundationUnitSummary(TypedDict):
    unit_id: str
    theme_id: str
    title: str
    display_order: int
    prerequisite_unit_ids: list[str]
    prerequisite_titles: list[str]
    target_skill: str
    unit_kind: AlgorithmFoundationUnitKind
    problem_count: int
    best_score: int | None
    last_attempted_at: str | None
    recommended: bool
    has_unmet_prerequisites: bool


class AlgorithmFoundationProblemSummary(TypedDict):
    problem_id: str
    title: str
    best_score: int | None
    last_attempted_at: str | None


class AlgorithmFoundationGroupSummary(TypedDict):
    group_id: str
    group_title: str
    order: int
    units: list[AlgorithmFoundationUnitSummary]


class AlgorithmFoundationCatalogResponse(TypedDict):
    total_unit_count: int
    total_problem_count: int
    groups: list[AlgorithmFoundationGroupSummary]


class AlgorithmFoundationUnitDetailResponse(TypedDict):
    unit_id: str
    theme_id: str
    group_id: str
    group_title: str
    title: str
    display_order: int
    prerequisite_unit_ids: list[str]
    prerequisite_titles: list[str]
    allowed_knowledge: list[str]
    forbidden_knowledge: list[str]
    target_skill: str
    unit_kind: AlgorithmFoundationUnitKind
    problem_count: int
    best_score: int | None
    last_attempted_at: str | None
    has_unmet_prerequisites: bool
    problems: list[AlgorithmFoundationProblemSummary]


class AlgorithmFoundationStartPayload(TypedDict):
    session_id: str
    unit_id: str
    group_id: str
    group_title: str
    unit_title: str
    target_skill: str
    unit_kind: AlgorithmFoundationUnitKind
    prerequisite_unit_ids: list[str]
    prerequisite_titles: list[str]
    allowed_knowledge: list[str]
    forbidden_knowledge: list[str]
    programming_language: str
    problem_id: str
    problem_title: str
    problem_statement: str
    input_format: str
    output_format: str
    constraints: str
    examples: list[AlgorithmFoundationExample]
    has_unmet_prerequisites: bool
    recommended: bool


class AlgorithmFoundationSessionSummary(TypedDict):
    session_id: str
    unit_id: str
    group_id: str
    group_title: str
    unit_title: str
    target_skill: str
    unit_kind: AlgorithmFoundationUnitKind
    problem_id: str
    problem_title: str
    programming_language: str
    status: AlgorithmFoundationSessionStatus
    created_at: str
    score: int | None


class AlgorithmFoundationAnswerResponse(TypedDict):
    session_id: str
    score: int
    feedback: str
    time_complexity: str
    space_complexity: str
    improvement_suggestions: str
    rubric_scores_json: str
    reference_solution: str


class AlgorithmFoundationError(Exception):
    def __init__(self, *, error_code: str, message: str) -> None:
        self.error_code = error_code
        super().__init__(message)


class AlgorithmFoundationCatalogError(AlgorithmFoundationError):
    """カタログ生成/取得の失敗。"""


class AlgorithmFoundationLanguageAdaptationError(AlgorithmFoundationError):
    """言語適応ステップの失敗。"""


__all__ = [
    "AlgorithmFoundationAnswerResponse",
    "AlgorithmFoundationCatalogError",
    "AlgorithmFoundationCatalogResponse",
    "AlgorithmFoundationError",
    "AlgorithmFoundationExample",
    "AlgorithmFoundationGroupSummary",
    "AlgorithmFoundationLanguageAdaptationError",
    "AlgorithmFoundationProblem",
    "AlgorithmFoundationProblemSummary",
    "AlgorithmFoundationRubricItem",
    "AlgorithmFoundationSessionStatus",
    "AlgorithmFoundationSessionSummary",
    "AlgorithmFoundationStartPayload",
    "AlgorithmFoundationUnit",
    "AlgorithmFoundationUnitDetailResponse",
    "AlgorithmFoundationUnitKind",
    "AlgorithmFoundationUnitSummary",
]
