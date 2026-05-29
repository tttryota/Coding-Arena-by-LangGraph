"""コーディングセッションのドメイン型定義。

座学 → コーディング練習の新しいセッションフローで使用する TypedDict。
既存の SessionState とは独立した定義。
"""

from __future__ import annotations

from typing import Literal, TypedDict

from quiz.domain.session_state import RoadmapItemLevel  # noqa: TC001

CodingDifficulty = Literal[
    "rewrite", "fill_blank", "bug_fix", "extend", "implement",
]


class CodingConfirmationPoint(TypedDict):
    """コーディング確認ポイント。

    start_format: この CP の開始難易度
    end_format: この CP の最終難易度
    coding_problem_set_design が CP の性質に応じて設定する。
    """

    id: str
    content: str
    start_format: CodingDifficulty
    end_format: CodingDifficulty


class CodingProblemAttempt(TypedDict):
    """コーディング問題への回答記録。"""

    confirmation_point_id: str
    format: CodingDifficulty
    question_text: str
    example_code: str
    answer_text: str
    score: int
    feedback: str


class CodingSessionState(TypedDict, total=False):
    """コーディングセッションの状態。

    LangGraph の StateGraph で使用する TypedDict。

    フィールドの初期化責務:
    - session_init (グラフ外): session_id, roadmap_item_id, roadmap_item_level,
      roadmap_item_title, roadmap_item_description, is_resumed
    - lecture_generation: lecture_content, lecture_phase_active(True)
    - practice_start: lecture_phase_active(False)
    - coding_problem_set_design: confirmation_points, current_point_index
    - coding_problem_delivery: current_question_text, current_example_code,
      current_format, total_questions_asked
    - await_coding_input の resume: user_input, input_source
    - code_evaluation: next_action, current_score, current_feedback,
      coding_attempts (append)
    - coding_chat_response / lecture_chat_response: chat_response_text
    """

    # セッション識別
    session_id: str
    roadmap_item_id: str
    roadmap_item_level: RoadmapItemLevel
    roadmap_item_title: str
    roadmap_item_description: str
    is_resumed: bool

    # 座学フェーズ
    lecture_content: str
    lecture_phase_active: bool

    # 確認ポイント
    confirmation_points: list[CodingConfirmationPoint]
    current_point_index: int

    # コーディング問題
    current_question_text: str
    current_example_code: str
    current_format: CodingDifficulty
    total_questions_asked: int
    coding_attempts: list[CodingProblemAttempt]

    # ユーザー入力
    user_input: str
    input_source: Literal["form", "chat"]

    # 評価結果
    next_action: Literal["next_step", "next_cp", "complete"]
    current_score: int
    current_feedback: str

    # チャット
    chat_response_text: str


__all__ = [
    "CodingConfirmationPoint",
    "CodingDifficulty",
    "CodingProblemAttempt",
    "CodingSessionState",
]
