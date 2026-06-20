"""SQL道場のドメイン型定義。"""

from __future__ import annotations

from typing import Literal, TypedDict

SqlDojoDifficulty = Literal["beginner", "intermediate", "advanced"]
SqlDojoDialect = Literal["postgresql"]
SqlDojoSessionStatus = Literal["in_progress", "completed"]


class SqlDojoTopicSummary(TypedDict):
    """トピック概要。"""

    topic_id: str
    topic_title: str
    family: str
    difficulty: SqlDojoDifficulty
    business_domain: str
    target_skill: str
    attempt_count: int
    best_score: int | None
    last_attempted_at: str | None


class SqlDojoThemeSummary(TypedDict):
    """テーマ概要。"""

    family: str
    difficulty: SqlDojoDifficulty
    business_domain: str
    target_skill: str
    title: str
    variant_count: int
    attempt_count: int
    best_score: int | None
    last_attempted_at: str | None
    topics: list[SqlDojoTopicSummary]


class SqlDojoCatalog(TypedDict):
    """公開カタログ。"""

    difficulties: list[SqlDojoDifficulty]
    themes: list[SqlDojoThemeSummary]


class SqlDojoGradingRule(TypedDict, total=False):
    """静的採点ルール。"""

    name: str
    weight: int
    message: str
    passed: bool
    rule_type: str
    expected: object


class SqlDojoJoinRequirement(TypedDict):
    """JOIN 条件。"""

    left: str
    right: str
    join_type: str


class SqlDojoAggregateRequirement(TypedDict):
    """集約関数条件。"""

    function: str
    column: str


class SqlDojoOrderRequirement(TypedDict, total=False):
    """ORDER BY 条件。"""

    column: str
    direction: str


class SqlDojoIndexRequirement(TypedDict, total=False):
    """インデックス条件。"""

    table: str
    columns: list[str]
    orders: dict[str, str]


class SqlDojoGradingContract(TypedDict, total=False):
    """採点契約。"""

    statement_kind: str
    required_tables: list[str]
    required_joins: list[SqlDojoJoinRequirement]
    required_predicate_columns: list[str]
    required_group_by_columns: list[str]
    required_aggregates: list[SqlDojoAggregateRequirement]
    required_order_by: list[SqlDojoOrderRequirement]
    required_limit: int
    required_window_functions: list[str]
    required_cte_names: list[str]
    require_explain: bool
    required_explain_options: list[str]
    required_index: SqlDojoIndexRequirement
    prohibited_patterns: list[str]


class SqlDojoProblem(TypedDict):
    """出題済み問題。"""

    family: str
    topic_id: str
    topic_title: str
    difficulty: SqlDojoDifficulty
    dialect: SqlDojoDialect
    business_domain: str
    target_skill: str
    theme_title: str
    problem_statement: str
    schema_markdown: str
    sample_data_json: str
    expected_focus: str
    reference_sql: str
    grading_contract: SqlDojoGradingContract


class SqlDojoEvaluation(TypedDict):
    """採点結果。"""

    score: int
    feedback: str
    rule_breakdown_json: str
    improvement_suggestions: str


class SqlDojoError(Exception):
    """SQL道場の基底例外。"""

    def __init__(self, *, error_code: str, message: str) -> None:
        self.error_code = error_code
        super().__init__(message)


class SqlDojoGenerationError(SqlDojoError):
    """問題生成の失敗。"""


class SqlDojoEvaluationError(SqlDojoError):
    """採点の失敗。"""


class SqlDojoQuestionError(SqlDojoError):
    """質問応答の失敗。"""


__all__ = [
    "SqlDojoAggregateRequirement",
    "SqlDojoCatalog",
    "SqlDojoDialect",
    "SqlDojoDifficulty",
    "SqlDojoError",
    "SqlDojoEvaluation",
    "SqlDojoEvaluationError",
    "SqlDojoGenerationError",
    "SqlDojoGradingContract",
    "SqlDojoGradingRule",
    "SqlDojoIndexRequirement",
    "SqlDojoJoinRequirement",
    "SqlDojoOrderRequirement",
    "SqlDojoProblem",
    "SqlDojoQuestionError",
    "SqlDojoSessionStatus",
    "SqlDojoThemeSummary",
    "SqlDojoTopicSummary",
]
