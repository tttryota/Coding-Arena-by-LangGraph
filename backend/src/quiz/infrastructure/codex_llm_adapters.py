"""Quiz LLM Protocol 群の Codex app-server concrete 実装。

全アダプタが CodexLlmTransport を共有し、
プロンプト構築 → API 呼び出し → JSON パース → バリデーションの同一パターンで実装する。
各アダプタは Protocol 固有の Error 型に変換して例外を伝搬する。
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Literal, cast

import structlog

from infrastructure.llm.codex_transport import (
    CodexLlmTransport,
    CodexMessage,
    CodexTransportHttpError,
    CodexTransportResponseError,
)
from quiz.application.question_set_design_types import QuestionSetDesignResult

if TYPE_CHECKING:
    from collections.abc import Sequence

    from quiz.application.answer_evaluation_types import (
        DeepdivePointDraft,
        EvaluationOutput,
    )
    from quiz.application.progress_update_types import ProgressOutput
    from quiz.application.question_delivery_types import QuestionOutput
    from quiz.application.summary_test_record_types import SummaryAnalysis
    from quiz.domain.session_state import (
        ConfirmationPoint,
        ConfirmationPointFormat,
        QuizAnswerRecord,
        QuizAnswerType,
        RoadmapItemLevel,
    )

logger = structlog.get_logger(__name__)

_JSON_INSTRUCTION = "必ず JSON のみで回答してください。JSON の外にテキストを含めないでください。"
_QUIZ_MODEL = "gpt-5.3-codex-spark"

_VALID_INPUT_TYPES = frozenset({"answer", "question", "explanation_request"})
_VALID_NEXT_ACTIONS = frozenset({"next", "deepdive", "complete"})
_VALID_ANSWER_TYPES = frozenset({"textarea", "code"})
_VALID_CP_FORMATS = frozenset({"knowledge", "knowledge_and_practice"})
_FORMAT_TO_ANSWER_TYPE = {"knowledge": "textarea", "knowledge_and_practice": "code"}
type JsonObject = dict[str, object]


def _validate_str(value: object, field: str) -> str:
    """LLM 応答の文字列項目を検証する。"""
    if not isinstance(value, str):
        msg = f"{field} must be str, got {type(value).__name__}"
        raise TypeError(msg)
    return value


def _validate_int(value: object, field: str) -> int:
    """LLM 応答の整数項目を検証する。"""
    if isinstance(value, bool) or not isinstance(value, int):
        msg = f"{field} must be int, got {type(value).__name__}"
        raise TypeError(msg)
    return value


def _validate_score(value: object, field: str) -> int:
    """score を 0..100 の契約で検証する。"""
    score = _validate_int(value, field)
    if score < 0 or score > 100:
        msg = f"{field} must be 0-100, got {score}"
        raise ValueError(msg)
    return score


def _error_code_for(exc: Exception) -> str:
    """下位例外を各 Protocol が期待する error_code に畳み込む。"""
    if isinstance(exc, CodexTransportHttpError):
        return "llm_request_failed"
    if isinstance(exc, (CodexTransportResponseError, json.JSONDecodeError, KeyError)):
        return "llm_response_parse_failed"
    if isinstance(exc, (TypeError, ValueError)):
        return "llm_response_parse_failed"
    return "llm_request_failed"


def _validate_confirmation_point(item: object) -> ConfirmationPoint:
    """確認ポイント 1 件分の JSON 形を検証する。"""
    if not isinstance(item, dict):
        msg = f"confirmation point must be dict, got {type(item).__name__}"
        raise TypeError(msg)
    cp_id = _validate_str(item.get("id"), "id")
    content = _validate_str(item.get("content"), "content")
    fmt = _validate_str(item.get("format"), "format")
    if fmt not in _VALID_CP_FORMATS:
        msg = f"invalid confirmation point format: {fmt}"
        raise ValueError(msg)
    return {
        "id": cp_id,
        "content": content,
        "format": cast("ConfirmationPointFormat", fmt),
    }


def _validate_deepdive_point(item: object) -> DeepdivePointDraft:
    """深掘り確認ポイント 1 件分の JSON 形を検証する。"""
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
    return {"content": content, "format": cast("ConfirmationPointFormat", fmt)}


def _parse_json_object(text: str) -> JsonObject:
    """LLM レスポンスから JSON を抽出してパースする。"""
    cleaned = text.strip()
    if cleaned.startswith("```"):
        # モデルが code fence を付けても呼び出し側の契約は壊さない。
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


def _parse_json(text: str) -> JsonObject:
    """JSON object を返す簡易ラッパー。"""
    return _parse_json_object(text)


def _validate_answer_type(value: object) -> Literal["textarea", "code"]:
    """LLM が返した answer_type を許可値で検証する。"""
    answer_type = _validate_str(value, "answer_type")
    if answer_type not in _VALID_ANSWER_TYPES:
        msg = f"invalid answer_type from LLM: {answer_type}"
        raise ValueError(msg)
    return cast("Literal['textarea', 'code']", answer_type)


def _validate_input_type(
    value: object,
) -> Literal["answer", "question", "explanation_request"]:
    """LLM が返した input_type を許可値で検証する。"""
    input_type = _validate_str(value, "input_type")
    if input_type not in _VALID_INPUT_TYPES:
        msg = f"invalid input_type from LLM: {input_type}"
        raise ValueError(msg)
    return cast("Literal['answer', 'question', 'explanation_request']", input_type)


def _validate_next_action(
    value: object,
) -> Literal["next", "deepdive", "complete"]:
    """LLM が返した next_action を許可値で検証する。"""
    next_action = _validate_str(value, "next_action")
    if next_action not in _VALID_NEXT_ACTIONS:
        msg = f"invalid next_action from LLM: {next_action}"
        raise ValueError(msg)
    return cast("Literal['next', 'deepdive', 'complete']", next_action)


def _answers_to_text(answers: list[QuizAnswerRecord]) -> str:
    """過去回答を prompt に埋め込みやすい監査用テキストへ整形する。"""
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
    ) -> QuestionSetDesignResult:
        from quiz.application.question_set_design_types import QuestionSetDesignError

        system = (
            "あなたは学習支援AIです。与えられたトピックについて、"
            "学習概要と確認ポイントリストを設計してください。\n\n"
            "topic_overview ルール:\n"
            "- タイトルと説明の範囲で、学習者が問題に取り組む前に知っておくべき概要を3〜5文で書いてください。\n"
            "- 用語の定義、基本概念、なぜ重要かを含めてください。\n\n"
            "確認ポイント設計ルール:\n"
            "- 確認ポイントは必ず3〜5件にしてください。それ以上は不要です。\n"
            "- 基礎→応用の順に並べてください。最初のポイントはそのトピックの最も基本的な概念にしてください。\n"
            "- 1つの確認ポイントには1つの観点だけを含めてください。複数の概念を1つにまとめないでください。\n"
            "- 「〜を説明し、さらに〜も述べてください」のような複合的な確認ポイントは禁止です。\n"
            "- タイトルと説明の範囲内に厳密に収めてください。隣接トピックや上位概念に踏み込まないでください。\n"
            "- format の使い分け:\n"
            "  - knowledge: 概念・定義・比較・理由を文章で説明させるもの（デフォルト）\n"
            "  - knowledge_and_practice: 実際にコードを書かせて動作を示すもの。\n"
            "    そのトピックにコードで表現できる要素（設定、API呼び出し、簡単な実装例など）があれば積極的に使ってください。\n"
            "    3〜5件のうち少なくとも1件は knowledge_and_practice にすることを目標にしてください。\n"
            "    純粋に概念・歴史・比較のみのトピックで、コードで示す要素がない場合のみ全件 knowledge にしてください。\n"
            "- レベルに応じた粒度にしてください:\n"
            "  - detail: 具体的な1つの概念や操作に絞る\n"
            "  - middle: 複数の概念の関連性を問う（ただし1ポイント1観点は維持）\n"
            "  - major: 設計判断や全体像を問う（ただし1ポイント1観点は維持）\n"
            f"{_JSON_INSTRUCTION}\n"
            '形式: {"topic_overview": "学習概要テキスト", '
            '"confirmation_points": [{"id": "cp-001", "content": "確認内容", '
            '"format": "knowledge" | "knowledge_and_practice"}]}'
        )
        user = f"タイトル: {title}\n説明: {description}\nレベル: {level}"
        try:
            raw = self._transport.call(
                model=_QUIZ_MODEL,
                operation="quiz.question_set_design",
                messages=[
                    CodexMessage(role="system", content=system),
                    CodexMessage(role="user", content=user),
                ],
            )
            data = _parse_json_object(raw)
            topic_overview = _validate_str(
                data.get("topic_overview", ""), "topic_overview",
            )
            if not topic_overview.strip():
                msg = "topic_overview is empty"
                raise ValueError(msg)
            raw_points = data.get("confirmation_points", [])
            if not isinstance(raw_points, list):
                msg = "confirmation_points must be a list"
                raise TypeError(msg)
            points = [_validate_confirmation_point(item) for item in raw_points]
            return QuestionSetDesignResult(
                confirmation_points=points,
                topic_overview=topic_overview,
            )
        except QuestionSetDesignError:
            raise
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
            "あなたは学習支援AIです。確認ポイントに基づいて、学習者の理解を深める問いを1つ作成してください。\n\n"
            "出題の構成:\n"
            "- 問題文は「概念の説明（2〜3文、100字以内）→ 問い（1文、50字以内）」の2部構成にしてください。\n"
            "- 前半: 確認ポイントに関する概念を簡潔に教えてください。\n"
            "  学習者がこの概念を初めて知る前提で、用語の定義と仕組みを含めてください。\n"
            "- 後半: 教えた内容について、1つの疑問詞（なぜ/どう/何）で始まる問いを1つだけ出してください。\n"
            "- 問いは必ず1つの観点だけを問うてください。以下は全て禁止です:\n"
            "  - 「〜、そして〜」「〜、また〜」「〜を踏まえて〜」で複数の問いを接続\n"
            "  - 「〜を説明し、さらに〜も述べてください」\n"
            "  - 1文の中に疑問詞が2つ以上含まれる問い\n"
            "- 問いは、前半の概念説明で教えた内容だけで回答できるものにしてください。\n"
            "  概念説明に含まれていない知識がないと答えられない問いは出さないでください。\n"
            "- 「〜を説明してください」「〜とは何ですか」のような知識の再現を求める問いは避けてください。\n"
            "  代わりに「なぜ」「どういう利点があるか」「どう使い分けるか」のように考えさせてください。\n\n"
            "answer_type が \"code\" の場合の出題スタイル:\n"
            "- 問題文の中にコード例（5〜10行程度）を提示してください。\n"
            "- 学習者にはそのコードの穴埋め、改変、または拡張を求めてください。\n"
            "- ゼロからコードを書かせるのではなく、見せてから変えさせる形にしてください。\n"
            "- 例: 「以下のコードにクエリパラメータを追加するにはどう変更しますか？」\n\n"
            "制約:\n"
            "- 「〜を説明し、さらに〜も述べてください」のような複合問は禁止です。\n"
            "- 回答の目安は3〜5文程度で済む分量にしてください。\n"
            "- 過去の回答がある場合は、それまでの理解度に応じて段階的に深めてください。\n"
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
            raw = self._transport.call(
                model=_QUIZ_MODEL,
                operation="quiz.question_delivery",
                messages=[
                    CodexMessage(role="system", content=system),
                    CodexMessage(role="user", content=user),
                ],
            )
            data = _parse_json_object(raw)
            question_text = _validate_str(data["question_text"], "question_text")
            answer_type = _validate_answer_type(data["answer_type"])

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
    ) -> Literal["answer", "question", "explanation_request"]:
        from quiz.application.input_classification_types import (
            InputClassificationError,
        )

        system = (
            "ユーザー入力を分類してください。この入力はチャット欄から送信されたものです。\n\n"
            "- question: 出題内容やトピックについての質問・疑問（デフォルト）\n"
            "- explanation_request: 解説・説明を求めるリクエスト\n"
            "- answer: 問題に対する直接的な回答\n\n"
            "判断に迷う場合は question に分類してください。\n\n"
            "例:\n"
            '出題: "ASGIとWSGIの違いは何ですか？"\n'
            'ユーザー入力: "非同期って具体的にどういうこと？" → {"input_type": "question"}\n'
            'ユーザー入力: "解説してほしい" → {"input_type": "explanation_request"}\n'
            'ユーザー入力: "ASGIは非同期通信をサポートし、WSGIは同期のみです" → {"input_type": "answer"}\n\n'
            f"{_JSON_INSTRUCTION}\n"
            '形式: {"input_type": "question" | "explanation_request" | "answer"}'
        )
        user = f"出題: {question_text}\nユーザー入力: {user_input}"
        try:
            raw = self._transport.call(
                model=_QUIZ_MODEL,
                operation="quiz.input_classification",
                messages=[
                    CodexMessage(role="system", content=system),
                    CodexMessage(role="user", content=user),
                ],
            )
            data = _parse_json_object(raw)
            return _validate_input_type(data["input_type"])
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
            return self._transport.call(
                model=_QUIZ_MODEL,
                operation="quiz.chat_response",
                messages=[
                    CodexMessage(role="system", content=system),
                    CodexMessage(role="user", content=user),
                ],
            )
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
        remaining_points: Sequence[tuple[str, str]],
    ) -> EvaluationOutput:
        from quiz.application.answer_evaluation_types import (
            AnswerEvaluationError,
            EvaluationOutput,
        )

        remaining_text = (
            "\n".join(f"- [{fmt}] {content}" for content, fmt in remaining_points)
            if remaining_points
            else "(なし)"
        )

        system = (
            "あなたは学習支援AIです。回答を評価し、学習者が理解を深められるフィードバックを返してください。\n\n"
            "スコア基準:\n"
            "- 確認ポイントの核心を理解しているかを最も重視してください。\n"
            "- 問題文に複数の観点が含まれていても、核心を捉えた回答は70点以上にしてください。\n"
            "- 細部や補足的な観点への言及がなくても、大幅な減点はしないでください。\n"
            "- 0-30: 的外れ、または核心的な誤解がある\n"
            "- 30-50: 方向性は合っているが核心に届いていない\n"
            "- 50-70: 核心を部分的に捉えている\n"
            "- 70-85: 核心を正しく捉えている（補足が不足していてもこの範囲）\n"
            "- 85-100: 核心に加え、補足的な観点や具体例も的確\n\n"
            "フィードバックルール:\n"
            "- 回答の良かった点（部分的に正しい場合も認める）\n"
            "- 不足している観点と、その観点が重要な理由の簡潔な説明\n"
            "- スコアが50未満の場合は、正解に必要な核心的知識を1〜2文で教えてください\n\n"
            "制御ルール:\n"
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
            raw = self._transport.call(
                model=_QUIZ_MODEL,
                operation="quiz.answer_evaluation",
                messages=[
                    CodexMessage(role="system", content=system),
                    CodexMessage(role="user", content=user),
                ],
            )
            data = _parse_json_object(raw)
            next_action = _validate_next_action(data["next_action"])
            score = _validate_score(data["score"], "score")
            feedback = _validate_str(data["feedback"], "feedback")

            deepdive_points: list[DeepdivePointDraft] = []
            if next_action == "deepdive":
                raw_points = data.get("deepdive_points", [])
                if not isinstance(raw_points, list):
                    msg = "deepdive_points must be a list"
                    raise TypeError(msg)
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
    ) -> str:
        from quiz.application.explanation_generation_types import (
            ExplanationGenerationError,
        )

        system = (
            "あなたは学習支援AIです。問題の解説を、学習者が概念を理解できるように生成してください。\n\n"
            "解説ルール:\n"
            "- まず概念の定義を簡潔に述べてください\n"
            "- なぜその概念が重要なのか、実務上の意義を1〜2文で説明してください\n"
            "- 具体的な例やユースケースを1つ含めてください\n"
            "- 一般的な知識に基づいて、学習者がつまずきやすい点も補ってください\n"
            "- 全体で5〜10文程度にまとめてください"
        )
        user = (
            f"問題: {question_text}\n確認ポイント: {confirmation_point_content}"
        )
        try:
            return self._transport.call(
                model=_QUIZ_MODEL,
                operation="quiz.explanation_generation",
                messages=[
                    CodexMessage(role="system", content=system),
                    CodexMessage(role="user", content=user),
                ],
            )
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
            raw = self._transport.call(
                model=_QUIZ_MODEL,
                operation="quiz.progress_update",
                messages=[
                    CodexMessage(role="system", content=system),
                    CodexMessage(role="user", content=user),
                ],
            )
            data = _parse_json_object(raw)
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
            raw = self._transport.call(
                model=_QUIZ_MODEL,
                operation="quiz.summary_test_record",
                messages=[
                    CodexMessage(role="system", content=system),
                    CodexMessage(role="user", content=user),
                ],
            )
            data = _parse_json_object(raw)
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
