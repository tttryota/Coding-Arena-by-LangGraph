"""コーディングセッション用 LLM アダプタの Codex app-server concrete 実装。

5つのアダプタを提供する:
- CodexLectureGenerationLlm: 座学コンテンツ生成
- CodexLectureChatResponseLlm: 座学中チャット応答
- CodexCodingProblemSetDesignLlm: 確認ポイント設計
- CodexCodingProblemDeliveryLlm: format別コーディング問題生成
- CodexCodeEvaluationLlm: コード評価+ルーティング
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import TYPE_CHECKING, cast

import structlog

from infrastructure.llm.codex_transport import (
    CodexLlmTransport,
    CodexMessage,
    CodexTransportHttpError,
    CodexTransportResponseError,
)

if TYPE_CHECKING:
    from quiz.domain.coding_session_state import CodingDifficulty

logger = structlog.get_logger(__name__)

_JSON_INSTRUCTION = "必ず JSON のみで回答してください。JSON の外にテキストを含めないでください。"
_CODING_MODEL = "gpt-5.3-codex-spark"

_VALID_FORMATS = frozenset({
    "rewrite", "fill_blank", "bug_fix", "extend", "implement",
})
_FORMAT_ORDER = ("rewrite", "fill_blank", "bug_fix", "extend", "implement")
type JsonObject = dict[str, object]


def _parse_json_object(text: str) -> JsonObject:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        lines = cleaned.split("\n")
        lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        cleaned = "\n".join(lines)
    parsed = json.loads(cleaned)
    if not isinstance(parsed, dict):
        msg = f"expected JSON object, got {type(parsed).__name__}"
        raise TypeError(msg)
    return cast("JsonObject", parsed)


def _validate_str(value: object, field: str) -> str:
    if not isinstance(value, str):
        msg = f"{field} must be str, got {type(value).__name__}"
        raise TypeError(msg)
    return value


def _validate_int(value: object, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        msg = f"{field} must be int, got {type(value).__name__}"
        raise TypeError(msg)
    return value


def _validate_score(value: object, field: str) -> int:
    score = _validate_int(value, field)
    if score < 0 or score > 100:
        msg = f"{field} must be 0-100, got {score}"
        raise ValueError(msg)
    return score


def _validate_format(value: object, field: str) -> CodingDifficulty:
    fmt = _validate_str(value, field)
    if fmt not in _VALID_FORMATS:
        msg = f"invalid {field}: {fmt}"
        raise ValueError(msg)
    return cast("CodingDifficulty", fmt)


def _error_code_for(exc: Exception) -> str:
    if isinstance(exc, CodexTransportHttpError):
        return "llm_request_failed"
    if isinstance(exc, (CodexTransportResponseError, json.JSONDecodeError, KeyError)):
        return "llm_response_parse_failed"
    if isinstance(exc, (TypeError, ValueError)):
        return "llm_response_parse_failed"
    return "llm_request_failed"


# ---------------------------------------------------------------------------
# Error types
# ---------------------------------------------------------------------------


class LectureGenerationError(Exception):
    def __init__(self, *, error_code: str, message: str) -> None:
        self.error_code = error_code
        super().__init__(message)


class LectureChatResponseError(Exception):
    def __init__(self, *, error_code: str, message: str) -> None:
        self.error_code = error_code
        super().__init__(message)


class CodingProblemSetDesignError(Exception):
    def __init__(self, *, error_code: str, message: str) -> None:
        self.error_code = error_code
        super().__init__(message)


class CodingProblemDeliveryError(Exception):
    def __init__(self, *, error_code: str, message: str) -> None:
        self.error_code = error_code
        super().__init__(message)


class CodeEvaluationError(Exception):
    def __init__(self, *, error_code: str, message: str) -> None:
        self.error_code = error_code
        super().__init__(message)


# ---------------------------------------------------------------------------
# Result types
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class LectureGenerationResult:
    lecture_content: str


@dataclass(frozen=True)
class CodingConfirmationPointDraft:
    id: str
    content: str
    start_format: CodingDifficulty
    end_format: CodingDifficulty


@dataclass(frozen=True)
class CodingProblemSetDesignResult:
    confirmation_points: list[CodingConfirmationPointDraft]


@dataclass(frozen=True)
class CodingProblemDeliveryResult:
    question_text: str
    example_code: str


@dataclass(frozen=True)
class CodeEvaluationResult:
    score: int
    feedback: str


# ---------------------------------------------------------------------------
# 1. CodexLectureGenerationLlm
# ---------------------------------------------------------------------------


class CodexLectureGenerationLlm:
    """ロードマップ項目から座学コンテンツを生成する。"""

    def __init__(self, transport: CodexLlmTransport) -> None:
        self._transport = transport

    def generate_lecture(
        self, title: str, description: str,
    ) -> LectureGenerationResult:
        system = (
            "あなたは学習支援AIです。与えられたトピックについて、"
            "学習者がコーディング練習に取り組む前に知っておくべき概念を説明してください。\n\n"
            "ルール:\n"
            "- 3〜5段落で構成してください\n"
            "- 用語の定義、仕組み、なぜ重要かを含めてください\n"
            "- コード例を1〜2個含めてください(```で囲む)\n"
            "- 学習者がこの後のコーディング問題に取り組める程度の知識を提供してください\n"
            f"{_JSON_INSTRUCTION}\n"
            '形式: {"lecture_content": "座学テキスト"}'
        )
        user = f"タイトル: {title}\n説明: {description}"
        try:
            raw = self._transport.call(
                model=_CODING_MODEL,
                operation="coding.lecture_generation",
                messages=[
                    CodexMessage(role="system", content=system),
                    CodexMessage(role="user", content=user),
                ],
            )
            data = _parse_json_object(raw)
            content = _validate_str(data["lecture_content"], "lecture_content")
            if not content.strip():
                msg = "lecture_content is empty"
                raise ValueError(msg)
            return LectureGenerationResult(lecture_content=content)
        except LectureGenerationError:
            raise
        except Exception as exc:
            raise LectureGenerationError(
                error_code=_error_code_for(exc),
                message=f"lecture generation failed: {exc}",
            ) from exc


# ---------------------------------------------------------------------------
# 2. CodexLectureChatResponseLlm
# ---------------------------------------------------------------------------


class CodexLectureChatResponseLlm:
    """座学中のユーザー質問に回答する。"""

    def __init__(self, transport: CodexLlmTransport) -> None:
        self._transport = transport

    def generate_chat_response(
        self, lecture_content: str, user_input: str,
    ) -> str:
        system = (
            "あなたは学習支援AIです。"
            "座学コンテンツの範囲内でユーザーの質問に丁寧に回答してください。"
        )
        user = f"座学コンテンツ:\n{lecture_content}\n\nユーザーの質問: {user_input}"
        try:
            return self._transport.call(
                model=_CODING_MODEL,
                operation="coding.lecture_chat_response",
                messages=[
                    CodexMessage(role="system", content=system),
                    CodexMessage(role="user", content=user),
                ],
            )
        except Exception as exc:
            raise LectureChatResponseError(
                error_code=_error_code_for(exc),
                message=f"lecture chat response failed: {exc}",
            ) from exc


# ---------------------------------------------------------------------------
# 3. CodexCodingProblemSetDesignLlm
# ---------------------------------------------------------------------------


class CodexCodingProblemSetDesignLlm:
    """確認ポイントを設計する。各CPに start_format/end_format を設定する。"""

    def __init__(self, transport: CodexLlmTransport) -> None:
        self._transport = transport

    def design_problem_set(  # noqa: PLR0915
        self,
        title: str,
        description: str,
        lecture_content: str,
    ) -> CodingProblemSetDesignResult:
        system = (
            "あなたは学習支援AIです。座学コンテンツに基づいて、"
            "コーディング練習の確認ポイントを設計してください。\n\n"
            "確認ポイント設計ルール:\n"
            "- 確認ポイントはトピックの広さに応じて適切な件数にしてください(最大20件)\n"
            "- 基礎→応用の順に並べてください\n"
            "- 1つの確認ポイントには1つの観点だけを含めてください\n"
            "- 各CPに start_format と end_format を設定してください:\n"
            "  rewrite(書き換え) → fill_blank(穴埋め) → bug_fix(バグ修正) "
            "→ extend(機能追加) → implement(自力実装)\n"
            "  start_format は end_format 以前の段階でなければなりません\n"
            "- 簡単なCPは rewrite〜fill_blank、難しいCPは bug_fix〜implement のように調整\n\n"
            f"{_JSON_INSTRUCTION}\n"
            "形式:\n"
            '{"confirmation_points": [{"id": "cp-001", "content": "確認内容", '
            '"start_format": "rewrite", "end_format": "implement"}]}'
        )
        user = (
            f"タイトル: {title}\n説明: {description}\n"
            f"座学コンテンツ:\n{lecture_content}"
        )
        try:
            raw = self._transport.call(
                model=_CODING_MODEL,
                operation="coding.problem_set_design",
                messages=[
                    CodexMessage(role="system", content=system),
                    CodexMessage(role="user", content=user),
                ],
            )
            data = _parse_json_object(raw)
            raw_points = data.get("confirmation_points", [])
            if not isinstance(raw_points, list):
                msg = "confirmation_points must be a list"
                raise TypeError(msg)
            points = []
            for item in raw_points:
                if not isinstance(item, dict):
                    msg = f"confirmation point must be dict, got {type(item).__name__}"
                    raise TypeError(msg)
                cp_id = _validate_str(item["id"], "id")
                content = _validate_str(item["content"], "content")
                start_fmt = _validate_format(item["start_format"], "start_format")
                end_fmt = _validate_format(item["end_format"], "end_format")
                if _FORMAT_ORDER.index(start_fmt) > _FORMAT_ORDER.index(end_fmt):
                    msg = f"start_format ({start_fmt}) must be <= end_format ({end_fmt})"
                    raise ValueError(msg)
                points.append(CodingConfirmationPointDraft(
                    id=cp_id, content=content,
                    start_format=start_fmt, end_format=end_fmt,
                ))
            if not points:
                msg = "confirmation_points must not be empty"
                raise ValueError(msg)
            if len(points) > 20:
                msg = f"Too many confirmation points: {len(points)} (max 20)"
                raise ValueError(msg)
            return CodingProblemSetDesignResult(confirmation_points=points)
        except CodingProblemSetDesignError:
            raise
        except Exception as exc:
            raise CodingProblemSetDesignError(
                error_code=_error_code_for(exc),
                message=f"coding problem set design failed: {exc}",
            ) from exc


# ---------------------------------------------------------------------------
# 4. CodexCodingProblemDeliveryLlm
# ---------------------------------------------------------------------------


class CodexCodingProblemDeliveryLlm:
    """format に応じたコーディング問題を生成する。"""

    def __init__(self, transport: CodexLlmTransport) -> None:
        self._transport = transport

    def deliver_problem(
        self,
        title: str,
        confirmation_point_content: str,
        current_format: CodingDifficulty,
        lecture_content: str,
    ) -> CodingProblemDeliveryResult:
        format_instructions = {
            "rewrite": "例示コードの一部を書き換える問題を出してください。変更箇所を明示してください。",
            "fill_blank": "穴あきコードを提示し、空欄を埋める問題を出してください。",
            "bug_fix": "バグのあるコードを提示し、修正する問題を出してください。",
            "extend": "動作するコードに新機能を追加する問題を出してください。",
            "implement": "シグネチャと入出力例のみ提示し、自力で実装する問題を出してください。",
        }
        instruction = format_instructions.get(
            current_format, "コーディング問題を出してください。",
        )
        system = (
            "あなたは学習支援AIです。以下のルールに従ってコーディング問題を1つ出してください。\n\n"
            f"出題形式: {current_format}\n"
            f"出題ルール: {instruction}\n\n"
            "- question_text: 問題文(概念説明 + 問い)\n"
            "- example_code: 提示するサンプルコード(implement の場合はシグネチャのみ)\n\n"
            f"{_JSON_INSTRUCTION}\n"
            '形式: {"question_text": "問題文", "example_code": "コード"}'
        )
        user = (
            f"タイトル: {title}\n確認ポイント: {confirmation_point_content}\n"
            f"座学コンテンツ:\n{lecture_content}"
        )
        try:
            raw = self._transport.call(
                model=_CODING_MODEL,
                operation="coding.problem_delivery",
                messages=[
                    CodexMessage(role="system", content=system),
                    CodexMessage(role="user", content=user),
                ],
            )
            data = _parse_json_object(raw)
            return CodingProblemDeliveryResult(
                question_text=_validate_str(data["question_text"], "question_text"),
                example_code=_validate_str(data["example_code"], "example_code"),
            )
        except CodingProblemDeliveryError:
            raise
        except Exception as exc:
            raise CodingProblemDeliveryError(
                error_code=_error_code_for(exc),
                message=f"coding problem delivery failed: {exc}",
            ) from exc


# ---------------------------------------------------------------------------
# 5. CodexCodeEvaluationLlm
# ---------------------------------------------------------------------------


class CodexCodeEvaluationLlm:
    """ユーザーのコード回答を評価し、次のアクションを決定する。"""

    def __init__(self, transport: CodexLlmTransport) -> None:
        self._transport = transport

    def evaluate_code(  # noqa: PLR0913
        self,
        question_text: str,
        example_code: str,
        user_code: str,
        current_format: CodingDifficulty,
        confirmation_point_content: str,
    ) -> CodeEvaluationResult:
        system = (
            "あなたは学習支援AIです。ユーザーのコード回答を評価してください。\n\n"
            "スコア基準:\n"
            "- 0-30: 的外れまたは核心的な誤解\n"
            "- 30-50: 方向性は合っているが不足\n"
            "- 50-70: 部分的に正しい\n"
            "- 70-85: 正しく動作する\n"
            "- 85-100: 優れた解答\n\n"
            f"{_JSON_INSTRUCTION}\n"
            '形式: {"score": 0-100, "feedback": "フィードバック"}'
        )
        user = (
            f"問題: {question_text}\nサンプルコード:\n{example_code}\n"
            f"確認ポイント: {confirmation_point_content}\n"
            f"出題形式: {current_format}\n"
            f"ユーザーの回答:\n{user_code}"
        )
        try:
            raw = self._transport.call(
                model=_CODING_MODEL,
                operation="coding.code_evaluation",
                messages=[
                    CodexMessage(role="system", content=system),
                    CodexMessage(role="user", content=user),
                ],
            )
            data = _parse_json_object(raw)
            return CodeEvaluationResult(
                score=_validate_score(data["score"], "score"),
                feedback=_validate_str(data["feedback"], "feedback"),
            )
        except CodeEvaluationError:
            raise
        except Exception as exc:
            raise CodeEvaluationError(
                error_code=_error_code_for(exc),
                message=f"code evaluation failed: {exc}",
            ) from exc


__all__ = [
    "CodeEvaluationError",
    "CodeEvaluationResult",
    "CodexCodeEvaluationLlm",
    "CodexCodingProblemDeliveryLlm",
    "CodexCodingProblemSetDesignLlm",
    "CodexLectureChatResponseLlm",
    "CodexLectureGenerationLlm",
    "CodingConfirmationPointDraft",
    "CodingProblemDeliveryError",
    "CodingProblemDeliveryResult",
    "CodingProblemSetDesignError",
    "CodingProblemSetDesignResult",
    "LectureChatResponseError",
    "LectureGenerationError",
    "LectureGenerationResult",
]
