"""Quiz LLM Protocol 群の Codex app-server concrete 実装。

全アダプタが CodexLlmTransport を共有し、
プロンプト構築 → API 呼び出し → JSON パース → バリデーションの同一パターンで実装する。
各アダプタは Protocol 固有の Error 型に変換して例外を伝搬する。
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

import structlog

from infrastructure.llm.codex_transport import (
    CodexLlmTransport,
    CodexMessage,
    CodexTransportHttpError,
    CodexTransportResponseError,
)

if TYPE_CHECKING:
    from quiz.application.answer_evaluation_types import EvaluationOutput
    from quiz.application.progress_update_types import ProgressOutput
    from quiz.application.question_delivery_types import QuestionOutput
    from quiz.application.summary_test_record_types import SummaryAnalysis
    from quiz.domain.session_state import (
        ConfirmationPoint,
        QuizAnswerRecord,
        QuizAnswerType,
        RoadmapItemLevel,
    )

logger = structlog.get_logger(__name__)

_JSON_INSTRUCTION = "必ず JSON のみで回答してください。JSON の外にテキストを含めないでください。"

_VALID_INPUT_TYPES = frozenset({"answer", "question", "explanation_request"})
_VALID_NEXT_ACTIONS = frozenset({"next", "deepdive", "complete"})
_VALID_ANSWER_TYPES = frozenset({"textarea", "code"})
_VALID_CP_FORMATS = frozenset({"knowledge", "knowledge_and_practice"})
_FORMAT_TO_ANSWER_TYPE = {"knowledge": "textarea", "knowledge_and_practice": "code"}


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


def _error_code_for(exc: Exception) -> str:
    if isinstance(exc, CodexTransportHttpError):
        return "llm_request_failed"
    if isinstance(exc, (CodexTransportResponseError, json.JSONDecodeError, KeyError)):
        return "llm_response_parse_failed"
    if isinstance(exc, (TypeError, ValueError)):
        return "llm_response_parse_failed"
    return "llm_request_failed"


def _validate_confirmation_point(item: object) -> dict[str, str]:
    if not isinstance(item, dict):
        msg = f"confirmation point must be dict, got {type(item).__name__}"
        raise TypeError(msg)
    cp_id = _validate_str(item.get("id"), "id")
    content = _validate_str(item.get("content"), "content")
    fmt = _validate_str(item.get("format"), "format")
    if fmt not in _VALID_CP_FORMATS:
        msg = f"invalid confirmation point format: {fmt}"
        raise ValueError(msg)
    return {"id": cp_id, "content": content, "format": fmt}


def _validate_deepdive_point(item: object) -> dict[str, str]:
    if not isinstance(item, dict):
        msg = f"deepdive point must be dict, got {type(item).__name__}"
        raise TypeError(msg)
    content = _validate_str(item.get("content"), "content")
    if not content.strip():
        msg = "deepdive point content must not be empty"
        raise ValueError(msg)
    fmt = _validate_str(item.get("format"), "format")
    if fmt not in _VALID_CP_FORMATS:
        msg = f"invalid deepdive point format: {fmt}"
        raise ValueError(msg)
    return {"content": content, "format": fmt}


def _parse_json(text: str) -> dict | list:
    """LLM レスポンスから JSON を抽出してパースする。"""
    cleaned = text.strip()
    if cleaned.startswith("```"):
        lines = cleaned.split("\n")
        lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        cleaned = "\n".join(lines)
    return json.loads(cleaned)


def _answers_to_text(answers: list[QuizAnswerRecord]) -> str:
    if not answers:
        return "(過去の回答なし)"
    parts = []
    for a in answers:
        parts.append(
            f"Q{a['question_number']}: {a['question_text']}\n"
            f"A: {a['answer_text']}\n"
            f"Score: {a['score']}, Feedback: {a['feedback']}",
        )
    return "\n---\n".join(parts)


# ---------------------------------------------------------------------------
# QuestionSetDesignLlmClient
# ---------------------------------------------------------------------------


class CodexQuestionSetDesignLlm:
    def __init__(self, transport: CodexLlmTransport) -> None:
        self._transport = transport

    def generate_confirmation_points(
        self,
        title: str,
        description: str,
        level: RoadmapItemLevel,
    ) -> list[ConfirmationPoint]:
        from quiz.application.question_set_design_types import QuestionSetDesignError

        system = (
            "あなたは学習支援AIです。与えられたトピックの理解度を確認するための"
            "確認ポイントリストを設計してください。\n\n"
            "設計ルール:\n"
            "- 確認ポイントは必ず3〜5件にしてください。それ以上は不要です。\n"
            "- 基礎→応用の順に並べてください。最初のポイントはそのトピックの最も基本的な概念にしてください。\n"
            "- 1つの確認ポイントには1つの観点だけを含めてください。複数の概念を1つにまとめないでください。\n"
            "- 「〜を説明し、さらに〜も述べてください」のような複合的な確認ポイントは禁止です。\n"
            "- レベルに応じた粒度にしてください:\n"
            "  - detail: 具体的な1つの概念や操作に絞る\n"
            "  - middle: 複数の概念の関連性を問う（ただし1ポイント1観点は維持）\n"
            "  - major: 設計判断や全体像を問う（ただし1ポイント1観点は維持）\n"
            f"{_JSON_INSTRUCTION}\n"
            '形式: [{"id": "cp-001", "content": "確認内容", '
            '"format": "knowledge" | "knowledge_and_practice"}]'
        )
        user = f"タイトル: {title}\n説明: {description}\nレベル: {level}"
        try:
            raw = self._transport.call([
                CodexMessage(role="system", content=system),
                CodexMessage(role="user", content=user),
            ])
            data = _parse_json(raw)
            return [_validate_confirmation_point(item) for item in data]
        except Exception as exc:
            raise QuestionSetDesignError(
                error_code=_error_code_for(exc),
                message=f"confirmation points generation failed: {exc}",
            ) from exc


# ---------------------------------------------------------------------------
# QuestionDeliveryLlmClient
# ---------------------------------------------------------------------------


class CodexQuestionDeliveryLlm:
    def __init__(self, transport: CodexLlmTransport) -> None:
        self._transport = transport

    def generate_question(  # noqa: PLR0913, PLR0915
        self,
        title: str,
        description: str,
        confirmation_point_content: str,
        confirmation_point_format: str,
        past_answers: list[QuizAnswerRecord],
    ) -> QuestionOutput:
        from quiz.application.question_delivery_types import (
            QuestionDeliveryError,
            QuestionOutput,
        )

        if confirmation_point_format not in _VALID_CP_FORMATS:
            msg = f"invalid confirmation_point_format: {confirmation_point_format}"
            raise QuestionDeliveryError(
                error_code="invalid_format", message=msg,
            )

        expected_answer_type = _FORMAT_TO_ANSWER_TYPE[confirmation_point_format]
        system = (
            "あなたは学習支援AIです。確認ポイントに基づいて1問を出題してください。\n\n"
            "出題ルール:\n"
            "- 問題文は1つの問いに絞ってください。「〜を説明し、さらに〜も述べてください」のような複合問は禁止です。\n"
            "- 回答の目安は3〜5文程度で済む分量にしてください。\n"
            "- 過去の回答がない（初問の）場合は、そのトピックの入門レベルの問いにしてください。\n"
            "- 過去の回答がある場合は、それまでの理解度に応じて難易度を調整してください。\n"
            f"answer_type は必ず \"{expected_answer_type}\" にしてください。\n"
            f"{_JSON_INSTRUCTION}\n"
            '形式: {"question_text": "問題文", "answer_type": "textarea" | "code"}'
        )
        try:
            user = (
                f"タイトル: {title}\n説明: {description}\n"
                f"確認ポイント: {confirmation_point_content}\n"
                f"形式: {confirmation_point_format}\n"
                f"過去の回答:\n{_answers_to_text(past_answers)}"
            )
            raw = self._transport.call([
                CodexMessage(role="system", content=system),
                CodexMessage(role="user", content=user),
            ])
            data = _parse_json(raw)
            question_text = _validate_str(data["question_text"], "question_text")
            answer_type = _validate_str(data["answer_type"], "answer_type")

            expected = _FORMAT_TO_ANSWER_TYPE[confirmation_point_format]
            if answer_type != expected:
                msg = (
                    f"answer_type mismatch: format={confirmation_point_format} "
                    f"expects {expected}, LLM returned {answer_type}"
                )
                raise QuestionDeliveryError(
                    error_code="answer_type_mismatch", message=msg,
                )

            return QuestionOutput(question_text=question_text, answer_type=answer_type)
        except QuestionDeliveryError:
            raise
        except Exception as exc:
            raise QuestionDeliveryError(
                error_code=_error_code_for(exc),
                message=f"question generation failed: {exc}",
            ) from exc


# ---------------------------------------------------------------------------
# InputClassificationLlmClient
# ---------------------------------------------------------------------------


class CodexInputClassificationLlm:
    def __init__(self, transport: CodexLlmTransport) -> None:
        self._transport = transport

    def classify_input(
        self,
        question_text: str,
        user_input: str,
    ) -> str:
        from quiz.application.input_classification_types import (
            InputClassificationError,
        )

        system = (
            "ユーザー入力を分類してください。\n"
            "- answer: 問題への回答\n"
            "- question: 出題内容への質問\n"
            "- explanation_request: 解説依頼\n"
            "判断に迷う場合や入力が曖昧・短い場合は、必ず answer に分類してください。\n"
            f"{_JSON_INSTRUCTION}\n"
            '形式: {"input_type": "answer" | "question" | "explanation_request"}'
        )
        user = f"出題: {question_text}\nユーザー入力: {user_input}"
        try:
            raw = self._transport.call([
                CodexMessage(role="system", content=system),
                CodexMessage(role="user", content=user),
            ])
            data = _parse_json(raw)
            input_type = data["input_type"]
            if input_type not in _VALID_INPUT_TYPES:
                msg = f"invalid input_type from LLM: {input_type}"
                raise InputClassificationError(error_code="invalid_input_type", message=msg)
            return input_type
        except InputClassificationError:
            raise
        except Exception as exc:
            raise InputClassificationError(
                error_code=_error_code_for(exc),
                message=f"input classification failed: {exc}",
            ) from exc


# ---------------------------------------------------------------------------
# ChatResponseLlmClient
# ---------------------------------------------------------------------------


class CodexChatResponseLlm:
    def __init__(self, transport: CodexLlmTransport) -> None:
        self._transport = transport

    def generate_chat_response(
        self,
        question_text: str,
        user_input: str,
    ) -> str:
        from quiz.application.chat_response_types import ChatResponseError

        system = "あなたは学習支援AIです。ユーザーの質問に丁寧に回答してください。"
        user = f"出題中の問題: {question_text}\nユーザーの質問: {user_input}"
        try:
            return self._transport.call([
                CodexMessage(role="system", content=system),
                CodexMessage(role="user", content=user),
            ])
        except Exception as exc:
            raise ChatResponseError(
                error_code=_error_code_for(exc),
                message=f"chat response generation failed: {exc}",
            ) from exc


# ---------------------------------------------------------------------------
# AnswerEvaluationLlmClient
# ---------------------------------------------------------------------------


class CodexAnswerEvaluationLlm:
    def __init__(self, transport: CodexLlmTransport) -> None:
        self._transport = transport

    def evaluate_answer(  # noqa: PLR0913, PLR0915
        self,
        question_text: str,
        confirmation_point_content: str,
        answer_text: str,
        answer_type: QuizAnswerType,
        past_answers: list[QuizAnswerRecord],
        total_questions_asked: int,
        remaining_points: list[tuple[str, str]],
    ) -> EvaluationOutput:
        from quiz.application.answer_evaluation_types import (
            AnswerEvaluationError,
            DeepdivePointDraft,
            EvaluationOutput,
        )

        remaining_text = (
            "\n".join(f"- [{fmt}] {content}" for content, fmt in remaining_points)
            if remaining_points
            else "(なし)"
        )

        system = (
            "回答を評価してください。\n"
            "ルール:\n"
            "- 回答が空の場合: score=0, next_action=\"next\", deepdive_points=[] とし、"
            "回答を促すfeedbackを返してください。deepdiveしないでください。\n"
            "- 出題総数が20以上の場合: next_action は \"next\" か \"complete\" のみにし、"
            "\"deepdive\" は選ばないでください(収束ルール)。\n"
            "- deepdive_points は最大2件までにしてください。\n"
            "- deepdive_points の format ルール:\n"
            "  - knowledge: 概念・比較・理由をテキストで説明するもの\n"
            "  - knowledge_and_practice: コードを書いて動作を示すもの\n"
            "- 以下の出題予定ポイントと重複する内容を deepdive_points に含めないでください:\n"
            f"{remaining_text}\n"
            f"{_JSON_INSTRUCTION}\n"
            '形式: {"next_action": "next"|"deepdive"|"complete", '
            '"score": 0-100, "feedback": "フィードバック", '
            '"deepdive_points": [{"content": "...", '
            '"format": "knowledge"|"knowledge_and_practice"}]}'
        )
        try:
            user = (
                f"問題: {question_text}\n確認ポイント: {confirmation_point_content}\n"
                f"回答形式: {answer_type}\n回答: {answer_text}\n"
                f"出題総数: {total_questions_asked}\n"
                f"過去の回答:\n{_answers_to_text(past_answers)}"
            )
            raw = self._transport.call([
                CodexMessage(role="system", content=system),
                CodexMessage(role="user", content=user),
            ])
            data = _parse_json(raw)
            next_action = _validate_str(data["next_action"], "next_action")
            score = _validate_score(data["score"], "score")
            feedback = _validate_str(data["feedback"], "feedback")

            if next_action not in _VALID_NEXT_ACTIONS:
                msg = f"invalid next_action from LLM: {next_action}"
                raise AnswerEvaluationError(error_code="invalid_next_action", message=msg)

            deepdive_points: list[DeepdivePointDraft] = []
            if next_action == "deepdive":
                raw_points = data.get("deepdive_points", [])
                deepdive_points = [_validate_deepdive_point(dp) for dp in raw_points]
                if not deepdive_points:
                    msg = "LLM returned deepdive with empty deepdive_points"
                    raise AnswerEvaluationError(
                        error_code="invalid_deepdive_points", message=msg,
                    )

            return EvaluationOutput(
                next_action=next_action,
                score=score,
                feedback=feedback,
                deepdive_points=deepdive_points,
            )
        except AnswerEvaluationError:
            raise
        except Exception as exc:
            raise AnswerEvaluationError(
                error_code=_error_code_for(exc),
                message=f"answer evaluation failed: {exc}",
            ) from exc


# ---------------------------------------------------------------------------
# ExplanationLlmClient
# ---------------------------------------------------------------------------


class CodexExplanationLlm:
    def __init__(self, transport: CodexLlmTransport) -> None:
        self._transport = transport

    def generate_explanation(
        self,
        question_text: str,
        confirmation_point_content: str,
        note_chunks: list[str],
    ) -> str:
        from quiz.application.explanation_generation_types import (
            ExplanationGenerationError,
        )

        chunks_text = "\n---\n".join(note_chunks) if note_chunks else "(関連ノートなし)"
        system = "あなたは学習支援AIです。問題の解説を生成してください。ノートの内容を参照して説明します。"
        user = (
            f"問題: {question_text}\n確認ポイント: {confirmation_point_content}\n"
            f"関連ノート:\n{chunks_text}"
        )
        try:
            return self._transport.call([
                CodexMessage(role="system", content=system),
                CodexMessage(role="user", content=user),
            ])
        except Exception as exc:
            raise ExplanationGenerationError(
                error_code=_error_code_for(exc),
                message=f"explanation generation failed: {exc}",
            ) from exc


# ---------------------------------------------------------------------------
# ProgressUpdateLlmClient
# ---------------------------------------------------------------------------


class CodexProgressUpdateLlm:
    def __init__(self, transport: CodexLlmTransport) -> None:
        self._transport = transport

    def evaluate_session(
        self,
        roadmap_item_title: str,
        roadmap_item_description: str,
        checkpoints: list[str],
        answers: list[QuizAnswerRecord],
    ) -> ProgressOutput:
        from quiz.application.progress_update_types import (
            ProgressOutput,
            ProgressUpdateError,
        )

        system = (
            "セッション全体を評価して総合スコアとコメントを返してください。\n"
            f"{_JSON_INSTRUCTION}\n"
            '形式: {"score": 0-100, "comment": "総合コメント"}'
        )
        try:
            checkpoints_text = "\n".join(f"- {cp}" for cp in checkpoints)
            user = (
                f"タイトル: {roadmap_item_title}\n説明: {roadmap_item_description}\n"
                f"確認ポイント:\n{checkpoints_text}\n"
                f"回答履歴:\n{_answers_to_text(answers)}"
            )
            raw = self._transport.call([
                CodexMessage(role="system", content=system),
                CodexMessage(role="user", content=user),
            ])
            data = _parse_json(raw)
            return ProgressOutput(
                score=_validate_score(data["score"], "score"),
                comment=_validate_str(data["comment"], "comment"),
            )
        except Exception as exc:
            raise ProgressUpdateError(
                error_code=_error_code_for(exc),
                message=f"session evaluation failed: {exc}",
            ) from exc


# ---------------------------------------------------------------------------
# SummaryTestLlmClient
# ---------------------------------------------------------------------------


class CodexSummaryTestLlm:
    def __init__(self, transport: CodexLlmTransport) -> None:
        self._transport = transport

    def analyze_session(
        self,
        title: str,
        description: str,
        answers: list[QuizAnswerRecord],
    ) -> SummaryAnalysis:
        from quiz.application.summary_test_record_types import (
            SummaryAnalysis,
            SummaryTestRecordError,
        )

        system = (
            "セッションの定性分析を行い、スコアと分析コメントを返してください。\n"
            f"{_JSON_INSTRUCTION}\n"
            '形式: {"score": 0-100, "analysis": "分析コメント"}'
        )
        try:
            user = (
                f"タイトル: {title}\n説明: {description}\n"
                f"回答履歴:\n{_answers_to_text(answers)}"
            )
            raw = self._transport.call([
                CodexMessage(role="system", content=system),
                CodexMessage(role="user", content=user),
            ])
            data = _parse_json(raw)
            return SummaryAnalysis(
                score=_validate_score(data["score"], "score"),
                analysis=_validate_str(data["analysis"], "analysis"),
            )
        except Exception as exc:
            raise SummaryTestRecordError(
                error_code=_error_code_for(exc),
                message=f"session analysis failed: {exc}",
            ) from exc


__all__ = [
    "CodexAnswerEvaluationLlm",
    "CodexChatResponseLlm",
    "CodexExplanationLlm",
    "CodexInputClassificationLlm",
    "CodexProgressUpdateLlm",
    "CodexQuestionDeliveryLlm",
    "CodexQuestionSetDesignLlm",
    "CodexSummaryTestLlm",
]
