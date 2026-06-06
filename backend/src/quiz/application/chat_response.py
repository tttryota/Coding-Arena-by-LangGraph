from __future__ import annotations

from typing import TYPE_CHECKING

import structlog

from quiz.application.chat_response_types import (
    ChatResponseError,
    ChatResponseLlmClient,
)

if TYPE_CHECKING:
    from quiz.domain.session_state import SessionState

logger = structlog.get_logger(__name__)

_FAILED_EVENT = "chat_response_failed"


def respond_to_chat(
    state: SessionState,
    *,
    llm: ChatResponseLlmClient,
) -> dict[str, object]:
    """出題内容への質問に LLM が回答する LangGraph ノード関数。"""
    try:
        response_text = llm.generate_chat_response(
            question_text=state["current_question_text"],
            user_input=state["user_input"],
        )
    except ChatResponseError as exception:
        logger.exception(
            _FAILED_EVENT,
            error_code=exception.error_code,
            message=exception.message,
        )
        raise

    return {"chat_response_text": response_text}


__all__ = ["respond_to_chat"]
