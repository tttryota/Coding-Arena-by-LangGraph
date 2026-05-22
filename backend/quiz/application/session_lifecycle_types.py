from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol

from quiz.domain.session_state import (
    QuizAnswerRecord,
    QuizAnswerType,
    RoadmapItemLevel,
    SessionState,
)


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


class QuizAnswerRecordLike(Protocol):
    question_number: int
    question_text: str
    answer_text: str
    answer_type: str
    score: int
    feedback: str
    confirmation_point_id: str


class QuizSessionStore(Protocol):
    def create_session(self, roadmap_item_id: str) -> Any: ...

    def find_in_progress_by_item(
        self,
        roadmap_item_id: str,
    ) -> Any | None: ...

    def find_session(self, session_id: str) -> Any: ...

    def complete_session(
        self,
        session_id: str,
        roadmap_item_id: str,
        score: int,
        completed_at: str,
    ) -> None: ...

    def discard_session(self, session_id: str) -> None: ...


class QuizAnswerStore(Protocol):
    def save_answer(
        self,
        quiz_session_id: str,
        answer: QuizAnswerRecordLike,
    ) -> None: ...

    def find_by_session(self, session_id: str) -> list[QuizAnswerRecordLike]: ...


class RoadmapItemReader(Protocol):
    def find_item(self, item_id: str) -> Any: ...


class GraphRunner(Protocol):
    def start_graph(self, state: SessionState) -> None: ...

    def resume_graph(self, state: SessionState) -> None: ...


__all__ = [
    "GraphRunner",
    "QuizAnswerRecord",
    "QuizAnswerRecordLike",
    "QuizAnswerStore",
    "QuizAnswerType",
    "QuizSessionLifecycleError",
    "QuizSessionStore",
    "ResumeSessionInput",
    "RoadmapItemLevel",
    "RoadmapItemReader",
    "SessionState",
    "StartSessionInput",
    "StartSessionResult",
]
