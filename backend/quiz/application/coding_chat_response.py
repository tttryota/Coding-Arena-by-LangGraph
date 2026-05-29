"""coding_chat_response ノード: practice 中のチャット応答。"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from quiz.application.coding_chat_response_types import (
        CodingChatResponseLlmClient,
    )
    from quiz.domain.coding_session_state import CodingSessionState


def respond_to_coding_chat(
    state: CodingSessionState,
    *,
    llm: CodingChatResponseLlmClient,
) -> dict[str, object]:
    """座学コンテンツの範囲内でユーザーの質問に回答する。"""
    return {
        "chat_response_text": llm.generate_chat_response(
            state["lecture_content"],
            state["user_input"],
        ),
    }


__all__ = ["respond_to_coding_chat"]
