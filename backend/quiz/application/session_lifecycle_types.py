from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol

from quiz.domain.session_state import QuizAnswerRecord, RoadmapItemLevel, SessionState


class QuizSessionLifecycleError(Exception):
    def __init__(self, *, error_code: str, message: str) -> None:
        super().__init__(message)
        self.error_code = error_code
        self.message = message


@dataclass(frozen=True)
class StartSessionInput:
    roadmap_item_id: str


@dataclass(frozen=True)
class ResumeSessionInput:
    session_id: str


@dataclass(frozen=True)
class StartSessionResult:
    session_id: str
    resume_required: bool
    resume_session_id: str | None


class QuizSessionStore(Protocol):
    def create_session(self, roadmap_item_id: str) -> Any: ...

    def find_in_progress_by_item(
        self,
        roadmap_item_id: str,
    ) -> Any | None: ...

    def find_session(self, session_id: str) -> Any: ...

    def mark_completed(self, session_id: str, completed_at: str) -> None: ...

    def delete_session(self, session_id: str) -> None: ...


class QuizAnswerStore(Protocol):
    def save_answer(self, quiz_session_id: str, answer: Any) -> None: ...

    def find_by_session(self, session_id: str) -> list[Any]: ...


class RoadmapItemReader(Protocol):
    def find_item(self, item_id: str) -> Any: ...

    def update_score(self, item_id: str, score: int) -> None: ...


class GraphRunner(Protocol):
    def start_graph(self, state: dict[str, object]) -> None: ...

    def resume_graph(self, state: dict[str, object]) -> None: ...


__all__ = [
    "GraphRunner",
    "QuizAnswerRecord",
    "QuizAnswerStore",
    "QuizSessionLifecycleError",
    "QuizSessionStore",
    "ResumeSessionInput",
    "RoadmapItemLevel",
    "RoadmapItemReader",
    "SessionState",
    "StartSessionInput",
    "StartSessionResult",
]
