from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


class SummaryTestResultsError(Exception):
    error_code: str
    message: str

    def __init__(self, *, error_code: str, message: str) -> None:
        super().__init__(message)
        self.error_code = error_code
        self.message = message


class SummaryTestResultsNotFoundError(SummaryTestResultsError):
    pass


@dataclass(frozen=True)
class SummaryTestResultRecord:
    id: str
    session_id: str
    score: int
    analysis: str
    created_at: str


class SummaryTestResultsStore(Protocol):
    def find_by_roadmap_item(
        self,
        roadmap_item_id: str,
    ) -> list[SummaryTestResultRecord]: ...


class RoadmapItemExistenceChecker(Protocol):
    def item_exists(self, item_id: str) -> bool: ...


__all__ = [
    "RoadmapItemExistenceChecker",
    "SummaryTestResultRecord",
    "SummaryTestResultsError",
    "SummaryTestResultsNotFoundError",
    "SummaryTestResultsStore",
]
