"""ingestion の実行と feedback 閲覧 API を提供する。"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Literal, cast
from uuid import UUID  # noqa: TC003

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

if TYPE_CHECKING:
    from api.dependencies import Container

router = APIRouter(prefix="/ingestion", tags=["ingestion"])


class _TriggerRequest(BaseModel):
    """ingestion 実行要求。"""

    target_path: str
    trigger: str = "startup"


def _container(request: Request) -> Container:
    """request から共有 container を取り出す。"""
    c = getattr(request.app.state, "container", None)
    if c is None:
        raise HTTPException(status_code=503, detail="Service not initialized")
    return cast("Container", c)


@router.post("/trigger", status_code=202)
def trigger_ingestion(
    body: _TriggerRequest, request: Request,
) -> dict[str, object]:
    """vault 配下の markdown を一括取り込みする。"""
    from dataclasses import asdict

    from ingestion.application.batch_executor import BatchExecutionConfig, run_once
    from ingestion.domain.batch_scheduler_types import BatchSchedulerConfigError
    from ingestion.infrastructure.batch_adapters import VaultMarkdownLoaderImpl

    c = _container(request)
    if c.vault_path is None:
        # feedback の閲覧は vault なしでも成立するため、
        # trigger だけを明示的に止める。
        raise HTTPException(
            status_code=503,
            detail="Ingestion service unavailable: VAULT_PATH not configured",
        )
    if c.batch_embedder is None:
        raise HTTPException(
            status_code=503,
            detail="Ingestion service unavailable: embedder not configured",
        )
    trigger = body.trigger
    if trigger not in ("startup", "interval"):
        raise HTTPException(status_code=422, detail=f"Invalid trigger: {trigger}")
    try:
        config = BatchExecutionConfig(
            target_path=body.target_path,
            diff_detector=c.batch_diff_detector,
            markdown_loader=VaultMarkdownLoaderImpl(body.target_path),
            chunk_splitter=c.batch_chunk_splitter,
            chunk_tagger=c.batch_chunk_tagger,
            embedder=c.batch_embedder,
            chunk_store=c.chunk_store,
            post_ingestion_hook=c.post_ingestion_hook,
        )
        result = run_once(
            config,
            trigger=cast("Literal['startup', 'interval']", trigger),
        )
    except BatchSchedulerConfigError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return cast("dict[str, object]", asdict(cast("Any", result)))


@router.get("/feedbacks")
def list_feedbacks(
    request: Request,
    date_from: str | None = None,
    date_to: str | None = None,
    read_status: str = "all",
) -> dict[str, object]:
    """feedback 一覧を条件付きで返す。"""
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
                read_status=cast("Literal['all', 'read', 'unread']", read_status),
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
def mark_as_read(feedback_id: UUID, request: Request) -> dict[str, object]:
    """feedback を既読に更新する。"""
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


def _serialize_feedback(item: object) -> dict[str, object]:
    """feedback の返却形を API 契約にそろえる。"""
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
