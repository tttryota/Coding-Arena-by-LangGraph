from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from quiz.domain.session_state import ConfirmationPoint, RoadmapItemLevel


class QuestionSetDesignError(Exception):
    error_code: str
    message: str

    def __init__(self, *, error_code: str, message: str) -> None:
        super().__init__(message)
        self.error_code = error_code
        self.message = message


@dataclass(frozen=True)
class QuestionSetDesignResult:
    confirmation_points: list[ConfirmationPoint]
    topic_overview: str


class QuestionSetDesignLlmClient(Protocol):
    def generate_confirmation_points(
        self,
        title: str,
        description: str,
        level: RoadmapItemLevel,
    ) -> QuestionSetDesignResult: ...


__all__ = [
    "QuestionSetDesignError",
    "QuestionSetDesignLlmClient",
    "QuestionSetDesignResult",
]
