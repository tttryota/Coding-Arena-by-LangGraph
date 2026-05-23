"""LlmTagClassifier Protocol の Codex app-server concrete 実装。"""

from __future__ import annotations

import json

from infrastructure.llm.codex_transport import (
    CodexLlmTransport,
    CodexMessage,
)

_JSON_INSTRUCTION = "必ず JSON のみで回答してください。JSON の外にテキストを含めないでください。"


class CodexLlmTagClassifier:
    def __init__(self, transport: CodexLlmTransport) -> None:
        self._transport = transport

    def classify(self, prompt: object) -> list[str]:  # noqa: PLR0915
        from ingestion.application.tagger import (
            TaggingLlmCallError,
            TaggingResponseFormatError,
        )

        system = (
            "あなたはテキスト分類AIです。与えられたテキストに適切なタグを付与してください。\n"
            f"{_JSON_INSTRUCTION}\n"
            '形式: {"tags": ["tag1", "tag2"]}'
        )
        if isinstance(prompt, dict):
            user = json.dumps(prompt, ensure_ascii=False)
        else:
            user = str(prompt)
        try:
            raw = self._transport.call([
                CodexMessage(role="system", content=system),
                CodexMessage(role="user", content=user),
            ])
        except Exception as exc:
            msg = f"tag classification LLM call failed: {exc}"
            raise TaggingLlmCallError(msg) from exc

        try:
            data = json.loads(raw)
            tags = data["tags"]
            if not isinstance(tags, list) or not all(isinstance(t, str) for t in tags):
                msg = f"tags must be list[str], got {tags!r}"
                raise TaggingResponseFormatError(msg)
            return tags
        except TaggingResponseFormatError:
            raise
        except Exception as exc:
            msg = f"tag classification response parse failed: {exc}"
            raise TaggingResponseFormatError(msg) from exc


__all__ = ["CodexLlmTagClassifier"]
