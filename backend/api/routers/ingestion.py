"""Ingestion API endpoints."""

from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID  # noqa: TC003

from fastapi import APIRouter, HTTPException, Request

if TYPE_CHECKING:
    from api.dependencies import Container

router = APIRouter(prefix="/ingestion", tags=["ingestion"])


def _container(request: Request) -> Container:
    c = getattr(request.app.state, "container", None)
    if c is None:
        raise HTTPException(status_code=503, detail="Service not initialized")
    return c  # type: ignore[return-value]


@router.get("/feedbacks")
def list_feedbacks(
    request: Request,
    date_from: str | None = None,
    date_to: str | None = None,
    read_status: str = "all",
) -> dict:
    from ingestion.application.feedback_listing import list_feedbacks as _list
    from ingestion.domain.feedback_listing_types import (
        FeedbackListingInputError,
        FeedbackListingQuery,
    )

    c = _container(request)
    try:
        result = _list(
            FeedbackListingQuery(
                date_from=date_from,
                date_to=date_to,
                read_status=read_status,  # type: ignore[arg-type]
            ),
            reader=c.ingestion_feedback_store,
        )
    except FeedbackListingInputError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return {
        "items": [_serialize_feedback(item) for item in result.items],
        "total_count": result.total_count,
    }


@router.put("/feedbacks/{feedback_id}/read")
def mark_as_read(feedback_id: UUID, request: Request) -> dict:
    from datetime import UTC, datetime

    from ingestion.application.feedback_listing import mark_feedback_as_read
    from ingestion.domain.feedback_listing_types import FeedbackListingNotFoundError

    c = _container(request)
    try:
        item = mark_feedback_as_read(
            feedback_id,
            writer=c.ingestion_feedback_store,
            now=datetime.now(tz=UTC).isoformat(),
        )
    except FeedbackListingNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return _serialize_feedback(item)


def _serialize_feedback(item: object) -> dict:
    rid = getattr(item, "roadmap_item_id", None)
    return {
        "id": str(getattr(item, "id", "")),
        "source_path": getattr(item, "source_path", ""),
        "roadmap_item_id": str(rid) if rid is not None else None,
        "title": getattr(item, "title", ""),
        "body": getattr(item, "body", ""),
        "is_read": getattr(item, "is_read", False),
        "created_at": getattr(item, "created_at", ""),
        "read_at": getattr(item, "read_at", None),
    }
