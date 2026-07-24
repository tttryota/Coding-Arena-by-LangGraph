"""競プロうさぎの言語依存 artifact を生成する LLM アダプタ。"""

from __future__ import annotations

import json
from typing import Any

from algorithm_foundations.domain.foundation_types import (
    AlgorithmFoundationLanguageAdaptationError,
)
from infrastructure.llm.codex_transport import (
    CodexLlmTransport,
    CodexMessage,
    CodexTransportHttpError,
    CodexTransportResponseError,
)

_JSON_INSTRUCTION = (
    "必ず JSON のみで回答してください。JSON の外にテキストを含めないでください。"
)
_COMPETITIVE_MODEL = "gpt-5.3-codex-spark"


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


def _validate_str(value: object, field: str) -> str:
    if not isinstance(value, str):
        msg = f"{field} must be str, got {type(value).__name__}"
        raise TypeError(msg)
    return value


def _error_code_for(exc: Exception) -> str:
    if isinstance(exc, CodexTransportHttpError):
        return "llm_request_failed"
    if isinstance(exc, (CodexTransportResponseError, json.JSONDecodeError, KeyError)):
        return "llm_response_parse_failed"
    if isinstance(exc, (TypeError, ValueError)):
        return "llm_response_parse_failed"
    return "llm_request_failed"


class CodexAlgorithmFoundationLanguageAdapter:
    """静的 problem 定義から対象言語の模範解答を生成する。"""

    def __init__(self, transport: CodexLlmTransport) -> None:
        self._transport = transport

    def adapt_reference_solution(  # noqa: PLR0913
        self,
        *,
        canonical_reference_solution: str,
        canonical_language: str,
        target_language: str,
        problem_statement: str,
        input_format: str,
        output_format: str,
        constraints: str,
        examples: list[dict[str, str]],
    ) -> str:
        if target_language == canonical_language:
            return canonical_reference_solution

        examples_text = "\n".join(
            f"入力:\n{item['input']}\n出力:\n{item['output']}" for item in examples
        )
        system = (
            "あなたは競技プログラミングの模範解答変換AIです。\n"
            "与えられた問題に対する canonical 解答コードを、別の出題言語へ正確に移植してください。\n"
            "- 問題の解法方針、計算量、入出力仕様を変えないでください\n"
            "- 出力は完成した解答コードのみを reference_solution に入れてください\n"
            "- 解説、コメント、補足テキストは付けないでください\n"
            "- target language の標準的な入出力スタイルに合わせてください\n"
            "- 問題文の難易度や要求知識は変更しないでください\n\n"
            f"{_JSON_INSTRUCTION}\n"
            "形式:\n"
            "{\n"
            '  "reference_solution": "target language の模範解答コード"\n'
            "}"
        )
        user = (
            f"問題文:\n{problem_statement}\n\n"
            f"入力形式:\n{input_format}\n\n"
            f"出力形式:\n{output_format}\n\n"
            f"制約:\n{constraints}\n\n"
            f"入出力例:\n{examples_text}\n\n"
            f"canonical language: {canonical_language}\n"
            f"target language: {target_language}\n\n"
            f"canonical reference solution:\n{canonical_reference_solution}"
        )
        try:
            raw = self._transport.call(
                model=_COMPETITIVE_MODEL,
                operation="algorithm_foundations.adapt_language",
                messages=[
                    CodexMessage(role="system", content=system),
                    CodexMessage(role="user", content=user),
                ],
            )
            response = _parse_json(raw)
            return _validate_str(
                response["reference_solution"],
                "reference_solution",
            )
        except AlgorithmFoundationLanguageAdaptationError:
            raise
        except Exception as exc:
            raise AlgorithmFoundationLanguageAdaptationError(
                error_code=_error_code_for(exc),
                message=f"language adaptation failed: {exc}",
            ) from exc


__all__ = ["CodexAlgorithmFoundationLanguageAdapter"]
