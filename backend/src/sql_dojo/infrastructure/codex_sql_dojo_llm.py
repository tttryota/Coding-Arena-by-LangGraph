"""SQL道場用の LLM アダプタ。"""

from __future__ import annotations

import json
from typing import Any

from infrastructure.llm.codex_transport import (
    CodexLlmTransport,
    CodexMessage,
    CodexTransportHttpError,
    CodexTransportResponseError,
)
from sql_dojo.domain.sql_dojo_types import (
    SqlDojoEvaluationError,
    SqlDojoQuestionError,
)

_SQL_DOJO_MODEL = "gpt-5.6-luna"
_JSON_INSTRUCTION = (
    "必ず JSON のみで回答してください。JSON の外にテキストを含めないでください。"
)


def _error_code_for(exc: Exception) -> str:
    if isinstance(exc, CodexTransportHttpError):
        return "llm_request_failed"
    if isinstance(exc, (CodexTransportResponseError, json.JSONDecodeError, KeyError)):
        return "llm_response_parse_failed"
    if isinstance(exc, (TypeError, ValueError)):
        return "llm_response_parse_failed"
    return "llm_request_failed"


def _parse_json(text: str) -> dict[str, Any]:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        lines = cleaned.split("\n")
        lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        cleaned = "\n".join(lines)
    result = json.loads(cleaned)
    if not isinstance(result, dict):
        msg = f"expected JSON object, got {type(result).__name__}"
        raise TypeError(msg)
    return result


class CodexSqlDojoFeedbackLlm:
    """静的採点結果を人間向け講評に変換する。"""

    def __init__(self, transport: CodexLlmTransport) -> None:
        self._transport = transport

    def generate_feedback(  # noqa: PLR0913
        self,
        *,
        family: str,
        difficulty: str,
        problem_statement: str,
        schema_markdown: str,
        expected_focus: str,
        reference_sql: str,
        user_sql: str,
        rule_breakdown_json: str,
        score: int,
    ) -> dict[str, str]:
        system = (
            "あなたは SQL メンターです。"
            "静的採点結果に基づいて、改善に役立つ日本語フィードバックを返してください。"
            "score はそのまま尊重し、採点結果を変更しないでください。"
            "feedback は良い点と不足点を簡潔に、improvement_suggestions は次に直す点を具体的に書いてください。"
            f"{_JSON_INSTRUCTION}\n"
            "形式:\n"
            "{\n"
            '  "feedback": "講評",\n'
            '  "improvement_suggestions": "改善提案"\n'
            "}"
        )
        user = (
            f"family: {family}\n"
            f"difficulty: {difficulty}\n"
            f"score: {score}\n"
            f"expected_focus: {expected_focus}\n"
            f"problem_statement:\n{problem_statement}\n\n"
            f"schema:\n{schema_markdown}\n\n"
            f"reference_sql:\n{reference_sql}\n\n"
            f"user_sql:\n{user_sql}\n\n"
            f"rule_breakdown_json:\n{rule_breakdown_json}"
        )
        try:
            raw = self._transport.call(
                model=_SQL_DOJO_MODEL,
                operation="sql_dojo.generate_question",
                messages=[
                    CodexMessage(role="system", content=system),
                    CodexMessage(role="user", content=user),
                ],
            )
            data = _parse_json(raw)
            feedback = data["feedback"]
            improvement_suggestions = data["improvement_suggestions"]
            if not isinstance(feedback, str) or not isinstance(improvement_suggestions, str):
                msg = "feedback fields must be strings"
                raise TypeError(msg)
            return {
                "feedback": feedback,
                "improvement_suggestions": improvement_suggestions,
            }
        except SqlDojoEvaluationError:
            raise
        except Exception as exc:
            raise SqlDojoEvaluationError(
                error_code=_error_code_for(exc),
                message=f"sql dojo feedback generation failed: {exc}",
            ) from exc


class CodexSqlDojoQuestionLlm:
    """提出前のヒント応答。"""

    def __init__(self, transport: CodexLlmTransport) -> None:
        self._transport = transport

    def generate_chat_response(  # noqa: PLR0913
        self,
        *,
        problem_statement: str,
        schema_markdown: str,
        expected_focus: str,
        user_input: str,
        history: list[dict[str, str]],
    ) -> str:
        history_text = "\n".join(
            f"{item['role']}: {item['content']}" for item in history
        ) or "なし"
        system = (
            "あなたは SQL 学習メンターです。"
            "完成 SQL や答えそのものは出さず、ヒントだけを返してください。"
            "考える順序、見るべき clause、注意点に留めてください。"
            f"{_JSON_INSTRUCTION}\n"
            "形式:\n"
            "{\n"
            '  "chat_response_text": "ヒント"\n'
            "}"
        )
        user = (
            f"problem_statement:\n{problem_statement}\n\n"
            f"schema:\n{schema_markdown}\n\n"
            f"expected_focus: {expected_focus}\n\n"
            f"history:\n{history_text}\n\n"
            f"user_input:\n{user_input}"
        )
        try:
            raw = self._transport.call(
                model=_SQL_DOJO_MODEL,
                operation="sql_dojo.generate_feedback",
                messages=[
                    CodexMessage(role="system", content=system),
                    CodexMessage(role="user", content=user),
                ],
            )
            data = _parse_json(raw)
            response = data["chat_response_text"]
            if not isinstance(response, str):
                msg = "chat_response_text must be str"
                raise TypeError(msg)
            return response
        except SqlDojoQuestionError:
            raise
        except Exception as exc:
            raise SqlDojoQuestionError(
                error_code=_error_code_for(exc),
                message=f"sql dojo question response failed: {exc}",
            ) from exc


__all__ = ["CodexSqlDojoFeedbackLlm", "CodexSqlDojoQuestionLlm"]
