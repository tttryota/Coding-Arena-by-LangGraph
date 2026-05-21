from __future__ import annotations

import re
from datetime import datetime
from typing import TYPE_CHECKING

import structlog

from ingestion.infrastructure.feedback_listing_types import (
    FeedbackListingInputError,
    FeedbackListingNotFoundError,
    FeedbackListingQuery,
    FeedbackListingResult,
    FeedbackListingStoreError,
)

if TYPE_CHECKING:
    from uuid import UUID

    from ingestion.infrastructure.feedback_listing_types import (
        FeedbackListingReader,
        FeedbackListItem,
        FeedbackReadWriter,
    )

_logger = structlog.get_logger()

_VALID_READ_STATUSES = frozenset({"all", "unread", "read"})

_DATETIME_RE = re.compile(
    r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,6})?(?:Z|[+-]\d{2}:\d{2})$",
)


def _validate_datetime_string(value: str, field_name: str) -> datetime:
    if not _DATETIME_RE.match(value):
        msg = f"{field_name} is not a valid datetime string: {value}"
        raise FeedbackListingInputError(msg)
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        msg = f"{field_name} could not be parsed: {value}"
        raise FeedbackListingInputError(msg) from exc
    if parsed.tzinfo is None:
        msg = f"{field_name} must be timezone-aware: {value}"
        raise FeedbackListingInputError(msg)
    return parsed


def _validate_store_created_at(item: FeedbackListItem) -> datetime:
    if not _DATETIME_RE.match(item.created_at):
        msg = f"store returned invalid created_at: {item.created_at}"
        raise FeedbackListingStoreError(msg)
    try:
        parsed = datetime.fromisoformat(item.created_at.replace("Z", "+00:00"))
    except ValueError as exc:
        msg = f"store returned unparseable created_at: {item.created_at}"
        raise FeedbackListingStoreError(msg) from exc
    return parsed


def _validate_listing_query(query: FeedbackListingQuery) -> None:
    if query.read_status not in _VALID_READ_STATUSES:
        msg = f"read_status must be one of {sorted(_VALID_READ_STATUSES)}, got: {query.read_status}"
        raise FeedbackListingInputError(msg)

    date_from_instant: datetime | None = None
    date_to_instant: datetime | None = None
    if query.date_from is not None:
        date_from_instant = _validate_datetime_string(query.date_from, "date_from")
    if query.date_to is not None:
        date_to_instant = _validate_datetime_string(query.date_to, "date_to")

    if (
        date_from_instant is not None
        and date_to_instant is not None
        and date_from_instant > date_to_instant
    ):
        msg = "date_from must not be after date_to"
        raise FeedbackListingInputError(msg)


def _call_reader(
    query: FeedbackListingQuery,
    reader: FeedbackListingReader,
) -> list[FeedbackListItem]:
    try:
        return reader.find_feedbacks(
            date_from=query.date_from,
            date_to=query.date_to,
            read_status=query.read_status,
        )
    except Exception as exc:
        _logger.error(
            "feedback_listing_store_failed",
            date_from=query.date_from,
            date_to=query.date_to,
            read_status=query.read_status,
            error_type=type(exc).__name__,
        )
        if isinstance(exc, FeedbackListingStoreError):
            raise
        msg = f"reader.find_feedbacks failed: {exc}"
        raise FeedbackListingStoreError(msg) from exc


def _sort_items(
    items: list[FeedbackListItem],
    query: FeedbackListingQuery,
) -> list[FeedbackListItem]:
    instant_map: dict[str, datetime] = {}
    for item in items:
        if item.created_at not in instant_map:
            try:
                instant_map[item.created_at] = _validate_store_created_at(item)
            except FeedbackListingStoreError:
                _logger.error(
                    "feedback_listing_store_failed",
                    date_from=query.date_from,
                    date_to=query.date_to,
                    read_status=query.read_status,
                    error_type="FeedbackListingStoreError",
                )
                raise

    return sorted(
        items,
        key=lambda item: (
            -instant_map[item.created_at].timestamp(),
            str(item.id),
        ),
    )


def _get_writer_item(
    feedback_id: UUID,
    writer: FeedbackReadWriter,
) -> FeedbackListItem | None:
    try:
        return writer.get_by_id(feedback_id)
    except Exception as exc:
        _logger.error(
            "feedback_listing_store_failed",
            feedback_id=str(feedback_id),
            error_type=type(exc).__name__,
        )
        if isinstance(exc, FeedbackListingStoreError):
            raise
        msg = f"writer.get_by_id failed: {exc}"
        raise FeedbackListingStoreError(msg) from exc


def _update_writer_item(
    feedback_id: UUID,
    writer: FeedbackReadWriter,
    now: str,
) -> FeedbackListItem:
    try:
        return writer.update_read_status(
            feedback_id,
            is_read=True,
            read_at=now,
        )
    except Exception as exc:
        _logger.error(
            "feedback_listing_store_failed",
            feedback_id=str(feedback_id),
            error_type=type(exc).__name__,
        )
        if isinstance(exc, FeedbackListingStoreError):
            raise
        msg = f"writer.update_read_status failed: {exc}"
        raise FeedbackListingStoreError(msg) from exc


def _validate_and_log_store_created_at(
    item: FeedbackListItem,
    feedback_id: UUID,
) -> None:
    try:
        _validate_store_created_at(item)
    except FeedbackListingStoreError:
        _logger.error(
            "feedback_listing_store_failed",
            feedback_id=str(feedback_id),
            error_type="FeedbackListingStoreError",
        )
        raise


def list_feedbacks(
    query: FeedbackListingQuery,
    *,
    reader: FeedbackListingReader,
) -> FeedbackListingResult:
    _validate_listing_query(query)
    items = _call_reader(query, reader)
    sorted_items = _sort_items(items, query)
    result = FeedbackListingResult(items=sorted_items, total_count=len(sorted_items))
    _logger.info(
        "feedback_listing_queried",
        total_count=result.total_count,
        date_from=query.date_from,
        date_to=query.date_to,
        read_status=query.read_status,
    )
    return result


def mark_feedback_as_read(
    feedback_id: UUID,
    *,
    writer: FeedbackReadWriter,
    now: str,
) -> FeedbackListItem:
    _validate_datetime_string(now, "now")
    item = _get_writer_item(feedback_id, writer)

    if item is None:
        _logger.warning(
            "feedback_listing_not_found",
            feedback_id=str(feedback_id),
        )
        msg = f"feedback not found: {feedback_id}"
        raise FeedbackListingNotFoundError(msg)

    _validate_and_log_store_created_at(item, feedback_id)

    if item.is_read:
        _logger.info("feedback_listing_marked_read", feedback_id=str(feedback_id))
        return item

    updated = _update_writer_item(feedback_id, writer, now)
    _validate_and_log_store_created_at(updated, feedback_id)
    _logger.info("feedback_listing_marked_read", feedback_id=str(feedback_id))
    return updated
