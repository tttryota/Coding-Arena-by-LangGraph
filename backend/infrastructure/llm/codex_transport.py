"""Codex app-server への HTTP 通信を担う共通トランスポート。

OpenAI 互換の chat completion API を想定。
各 Quiz/Roadmap/Ingestion LLM アダプタがこのトランスポートを使って LLM を呼び出す。
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

import httpx


class CodexTransportError(Exception):
    pass


class CodexTransportHttpError(CodexTransportError):
    pass


class CodexTransportResponseError(CodexTransportError):
    pass


@dataclass(frozen=True)
class CodexMessage:
    role: str
    content: str


class CodexLlmTransport:
    def __init__(self, base_url: str, *, timeout: float = 120.0) -> None:
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout

    def call(  # noqa: PLR0915
        self,
        messages: list[CodexMessage],
        *,
        model: str = "default",
        temperature: float = 0.7,
    ) -> str:
        """LLM に messages を送信し、応答テキストを返す。"""
        payload: dict[str, Any] = {
            "model": model,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "temperature": temperature,
        }
        try:
            response = httpx.post(
                f"{self._base_url}/v1/chat/completions",
                json=payload,
                timeout=self._timeout,
            )
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            msg = f"Codex API HTTP error: {exc.response.status_code}"
            raise CodexTransportHttpError(msg) from exc
        except httpx.RequestError as exc:
            msg = f"Codex API request error: {exc}"
            raise CodexTransportHttpError(msg) from exc

        try:
            data = response.json()
            content = data["choices"][0]["message"]["content"]
            if not isinstance(content, str):
                msg = f"Codex API response content is not a string: {type(content)}"
                raise CodexTransportResponseError(msg)
            return content
        except (json.JSONDecodeError, KeyError, IndexError, TypeError) as exc:
            msg = f"Codex API response parse error: {exc}"
            raise CodexTransportResponseError(msg) from exc


__all__ = [
    "CodexLlmTransport",
    "CodexMessage",
    "CodexTransportError",
    "CodexTransportHttpError",
    "CodexTransportResponseError",
]
