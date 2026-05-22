from __future__ import annotations

from dataclasses import dataclass
from importlib import import_module
from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from datetime import datetime

    from quiz.domain import session_state as session_state_domain
else:
    session_state_domain = import_module("quiz.domain.session_state")


class ProgressUpdateError(Exception):
    def __init__(self, *, error_code: str, message: str) -> None:
        super().__init__(message)
        self.error_code = error_code
        self.message = message


@dataclass(frozen=True)
class ProgressOutput:
    score: int
    comment: str


class ProgressUpdateLlmClient(Protocol):
    def evaluate_session(
        self,
        roadmap_item_title: str,
        roadmap_item_description: str,
        checkpoints: list[str],
        answers: list[session_state_domain.QuizAnswerRecord],
    ) -> ProgressOutput: ...


class ProgressUpdateStore(Protocol):
    def update_roadmap_item_progress(
        self,
        item_id: str,
        score: int,
        last_quiz_at: datetime,
    ) -> None: ...

    def save_summary_test_result(
        self,
        session_id: str,
        item_id: str,
        score: int,
        comment: str,
    ) -> None: ...

    def complete_session(self, session_id: str) -> None: ...


__all__ = [
    "ProgressOutput",
    "ProgressUpdateError",
    "ProgressUpdateLlmClient",
    "ProgressUpdateStore",
]
