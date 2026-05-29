"""coding_chat_response ノードの Protocol 定義。"""

from __future__ import annotations

from typing import Protocol


class CodingChatResponseLlmClient(Protocol):
    """practice 中のユーザー質問に回答するインターフェース。"""

    def generate_chat_response(
        self, lecture_content: str, user_input: str,
    ) -> str: ...


__all__ = ["CodingChatResponseLlmClient"]
