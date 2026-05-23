"""RoadmapGenerationLlmClient Protocol の Codex app-server concrete 実装。"""

from __future__ import annotations

from infrastructure.llm.codex_transport import (
    CodexLlmTransport,
    CodexMessage,
)
from roadmap.domain.roadmap_generation_types import RoadmapGenerationLlmError

_JSON_INSTRUCTION = "必ず JSON のみで回答してください。JSON の外にテキストを含めないでください。"


class CodexRoadmapGenerationLlm:
    def __init__(self, transport: CodexLlmTransport) -> None:
        self._transport = transport

    def generate_roadmap_json(self, topic: str) -> str:
        system = (
            "あなたは学習ロードマップ設計AIです。\n"
            "与えられたトピックについて、3階層の学習ロードマップを JSON で返してください。\n"
            f"{_JSON_INSTRUCTION}\n"
            '形式: {"topic": "<入力トピック>", "items": [\n'
            '  {"title": "基礎", "description": "...", "level": "major", "children": [\n'
            '    {"title": "...", "description": "...", "level": "middle", "children": [\n'
            '      {"title": "...", "description": "...", "level": "detail", "children": []}\n'
            "    ]}\n  ]},\n"
            '  {"title": "応用", "description": "...", "level": "major", "children": [...]}\n'
            "]}\n"
            "- topic は入力と完全一致\n"
            "- items はちょうど2件(基礎/応用)\n"
            "- 各 item に title, description, level, children を必須で含める"
        )
        user = f"トピック: {topic}"
        try:
            return self._transport.call([
                CodexMessage(role="system", content=system),
                CodexMessage(role="user", content=user),
            ])
        except Exception as exc:
            msg = f"roadmap generation LLM call failed: {exc}"
            raise RoadmapGenerationLlmError(msg) from exc


__all__ = ["CodexRoadmapGenerationLlm"]
