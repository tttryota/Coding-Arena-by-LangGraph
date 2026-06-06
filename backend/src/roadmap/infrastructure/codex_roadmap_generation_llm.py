"""RoadmapGenerationLlmClient Protocol の Codex app-server concrete 実装。"""

from __future__ import annotations

from infrastructure.llm.codex_transport import (
    CodexLlmTransport,
    CodexMessage,
)
from roadmap.domain.roadmap_generation_types import RoadmapGenerationLlmError

_JSON_INSTRUCTION = "必ず JSON のみで回答してください。JSON の外にテキストを含めないでください。"
_ROADMAP_MODEL = "gpt-5.5"


class CodexRoadmapGenerationLlm:
    def __init__(self, transport: CodexLlmTransport) -> None:
        self._transport = transport

    def generate_roadmap_json(self, topic: str) -> str:
        system = (
            "あなたはコーディング実践ロードマップ設計AIです。\n"
            "与えられたトピックについて、3階層のコーディング実践ロードマップを JSON で返してください。\n"
            "- major は学習段階(基礎/応用)\n"
            "- middle は実装カテゴリ\n"
            "- detail は1回の演習ユニット(1つの実装目標)\n\n"
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
            "- 各 item に title, description, level, children を必須で含める\n"
            "- detail の description は「何を実装できるようになるか」を1つだけ書くこと\n"
            "  複数の実装目標を「〜と〜と〜を実装する」のように並列しないこと\n"
            "- detail は以下の5段階のコーディング演習に分解可能な粒度にすること:\n"
            "  rewrite(書き換え) → fill_blank(穴埋め) → bug_fix(バグ修正) → extend(機能追加) → implement(自力実装)\n"
            "- 各 middle の detail は2〜3件にすること。detail が広すぎる場合は middle を増やして分割すること"
        )
        user = f"トピック: {topic}"
        try:
            return self._transport.call(model=_ROADMAP_MODEL, messages=[
                CodexMessage(role="system", content=system),
                CodexMessage(role="user", content=user),
            ])
        except Exception as exc:
            msg = f"roadmap generation LLM call failed: {exc}"
            raise RoadmapGenerationLlmError(msg) from exc


__all__ = ["CodexRoadmapGenerationLlm"]
