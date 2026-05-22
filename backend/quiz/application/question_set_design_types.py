from __future__ import annotations

from importlib import import_module
from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from quiz.domain import session_state as session_state_domain
else:
    session_state_domain = import_module("quiz.domain.session_state")


class QuestionSetDesignError(Exception):
    def __init__(self, *, error_code: str, message: str) -> None:
        super().__init__(message)
        self.error_code = error_code
        self.message = message


class QuestionSetDesignLlmClient(Protocol):
    def generate_confirmation_points(
        self,
        title: str,
        description: str,
        level: str,
    ) -> list[session_state_domain.ConfirmationPoint]: ...


__all__ = [
    "QuestionSetDesignError",
    "QuestionSetDesignLlmClient",
]
