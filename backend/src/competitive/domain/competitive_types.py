"""競プロアルゴリズムクイズのドメイン型定義。"""

from __future__ import annotations

from typing import Literal, TypedDict


class AlgoTheme(TypedDict):
    """アルゴリズムテーマのプリセットデータ。"""

    id: str
    category: str
    label: str


class AlgoThemeWithHistory(TypedDict):
    """アルゴリズムテーマ + 挑戦履歴。"""

    id: str
    category: str
    label: str
    display_order: int
    attempt_count: int
    best_score: int | None
    last_attempted_at: str | None


class ProblemExample(TypedDict):
    """問題の入出力例。"""

    input: str
    output: str


class RubricItem(TypedDict):
    """採点基準の1項目。"""

    criterion: str
    points: int
    description: str


CompetitiveSessionStatus = Literal["in_progress", "completed"]
ProgrammingLanguage = Literal["python", "typescript"]


class CompetitiveSessionState(TypedDict, total=False):
    """競プロクイズセッションの状態。

    LangGraph の StateGraph で使用する TypedDict。
    problem_generation ノードが問題生成と同時に reference_solution / grading_rubric を
    生成し、solution_evaluation ノードは保存済み rubric に基づいて採点する。

    フィールドの初期化責務:
    - theme_selection が初期化: session_id, status("in_progress"), algo_theme_id,
      algo_theme_label, algo_theme_category
    - problem_generation が初期化: programming_language, problem_statement, input_format, output_format,
      constraints, examples, reference_solution, grading_rubric
    - await_submission の resume で設定: user_code
    - solution_evaluation が初期化: score, feedback, time_complexity,
      space_complexity, improvement_suggestions, rubric_scores_json
    """

    session_id: str
    status: CompetitiveSessionStatus
    algo_theme_id: str
    algo_theme_label: str
    algo_theme_category: str
    programming_language: ProgrammingLanguage
    problem_statement: str
    input_format: str
    output_format: str
    constraints: str
    examples: list[ProblemExample]
    reference_solution: str
    grading_rubric: list[RubricItem]
    user_code: str
    score: int
    feedback: str
    time_complexity: str
    space_complexity: str
    improvement_suggestions: str
    rubric_scores_json: str


class CompetitiveError(Exception):
    """競プロクイズの基底例外。"""

    def __init__(self, *, error_code: str, message: str) -> None:
        self.error_code = error_code
        super().__init__(message)


class ThemeSelectionError(CompetitiveError):
    """テーマ選択の失敗。"""


class ProblemGenerationError(CompetitiveError):
    """問題生成の失敗。"""


class SolutionEvaluationError(CompetitiveError):
    """解答評価の失敗。"""


class QuestionResponseError(CompetitiveError):
    """問題への質問応答生成の失敗。"""


__all__ = [
    "AlgoTheme",
    "CompetitiveError",
    "CompetitiveSessionState",
    "CompetitiveSessionStatus",
    "ProblemExample",
    "ProblemGenerationError",
    "ProgrammingLanguage",
    "QuestionResponseError",
    "RubricItem",
    "SolutionEvaluationError",
    "ThemeSelectionError",
]
