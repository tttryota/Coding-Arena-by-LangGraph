from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Literal, Protocol

if TYPE_CHECKING:
    from uuid import UUID


class FeedbackListingInputError(Exception):
    pass


class FeedbackListingNotFoundError(Exception):
    pass


class FeedbackListingStoreError(Exception):
    pass


@dataclass(frozen=True)
class FeedbackListingQuery:
    date_from: str | None
    date_to: str | None
    read_status: Literal["all", "unread", "read"]


@dataclass(frozen=True)
class FeedbackListItem:
    id: UUID
    source_path: str
    roadmap_item_id: UUID | None
    title: str
    body: str
    is_read: bool
    created_at: str
    read_at: str | None


@dataclass(frozen=True)
class FeedbackListingResult:
    items: list[FeedbackListItem]
    total_count: int


class FeedbackListingReader(Protocol):
    def find_feedbacks(
        self,
        *,
        date_from: str | None,
        date_to: str | None,
        read_status: Literal["all", "unread", "read"],
    ) -> list[FeedbackListItem]: ...


class FeedbackReadWriter(Protocol):
    def get_by_id(self, feedback_id: UUID) -> FeedbackListItem | None: ...

    def update_read_status(
        self,
        feedback_id: UUID,
        *,
        is_read: bool,
        read_at: str,
    ) -> FeedbackListItem: ...


__all__ = [
    "FeedbackListItem",
    "FeedbackListingInputError",
    "FeedbackListingNotFoundError",
    "FeedbackListingQuery",
    "FeedbackListingReader",
    "FeedbackListingResult",
    "FeedbackListingStoreError",
    "FeedbackReadWriter",
]
