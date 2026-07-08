"""roadmap の参照・生成・編集 API を提供する。"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, cast
from uuid import UUID  # noqa: TC003

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

if TYPE_CHECKING:
    from api.dependencies import Container

router = APIRouter(prefix="/roadmaps", tags=["roadmaps"])


class _GenerateRequest(BaseModel):
    """roadmap 生成要求。"""

    topic: str


class _AddItemRequest(BaseModel):
    """item 追加要求。"""

    parent_id: UUID | None = None
    title: str
    description: str
    order: int | None = None


class _RegisterTopicRequest(BaseModel):
    """topic 手動登録要求。"""

    name: str


class _MoveItemRequest(BaseModel):
    """item 移動要求。"""

    target_parent_id: UUID | None = None
    target_order: int


def _container(request: Request) -> Container:
    """request から共有 container を取り出す。"""
    c = getattr(request.app.state, "container", None)
    if c is None:
        raise HTTPException(status_code=503, detail="Service not initialized")
    return cast("Container", c)


@router.get("")
def list_roadmaps(request: Request) -> dict[str, object]:
    """保存済み roadmap の一覧を返す。"""
    from dataclasses import asdict

    from roadmap.application.roadmap_retrieval import list_roadmaps as _list

    c = _container(request)
    result = _list(reader=c.roadmap_retrieval_reader)
    return cast("dict[str, object]", asdict(cast("Any", result)))


@router.get("/topics")
def list_topics(request: Request) -> dict[str, object]:
    """preset / 手動登録をマージした topic 候補を返す。"""
    from roadmap.application.topic_listing import list_topic_candidates

    c = _container(request)
    candidates = list_topic_candidates(
        preset_reader=c.preset_reader,
        topic_store=c.topic_store,
    )
    return {"candidates": [_serialize_candidate(tc) for tc in candidates]}


@router.post("/topics", status_code=201)
def register_topic(
    body: _RegisterTopicRequest, request: Request,
) -> dict[str, object]:
    """手動 topic を登録する。"""
    from roadmap.application.topic_listing import register_manual_topic
    from roadmap.domain.topic_listing_types import TopicListingEmptyTopicNameError

    c = _container(request)
    try:
        result = register_manual_topic(
            body.name,
            topic_store=c.topic_store,
        )
    except TopicListingEmptyTopicNameError as exc:
        raise HTTPException(
            status_code=422,
            detail="Topic name must not be empty",
        ) from exc
    return _serialize_candidate(result)


@router.get("/{roadmap_id}")
def get_roadmap(roadmap_id: UUID, request: Request) -> dict[str, object]:
    """roadmap 詳細を返す。"""
    from dataclasses import asdict

    from roadmap.application.roadmap_retrieval import get_roadmap as _get
    from roadmap.domain.roadmap_retrieval_types import RoadmapRetrievalNotFoundError

    c = _container(request)
    try:
        result = _get(roadmap_id, reader=c.roadmap_retrieval_reader)
    except RoadmapRetrievalNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return cast("dict[str, object]", asdict(cast("Any", result)))


@router.post("/generate", status_code=202)
def generate_roadmap(
    body: _GenerateRequest, request: Request,
) -> dict[str, object]:
    """roadmap 生成ジョブを受け付ける。"""
    from roadmap.application.roadmap_generation import request_roadmap_generation
    from roadmap.domain.roadmap_generation_types import (
        RoadmapGenerationInputError,
        RoadmapGenerationScheduleError,
    )

    c = _container(request)
    try:
        result = request_roadmap_generation(
            body.topic,
            job_id_generator=c.uuid_generator,
            scheduler=c.job_scheduler,
            job_store=c.job_status_store,
        )
    except RoadmapGenerationInputError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except RoadmapGenerationScheduleError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return {"job_id": str(result["job_id"]), "status": result["status"]}


@router.get("/generate/{job_id}")
def get_generation_job(job_id: UUID, request: Request) -> dict[str, object]:
    """生成ジョブの状態を返す。"""
    from roadmap.domain.roadmap_generation_types import (
        RoadmapGenerationJobNotFoundError,
    )

    c = _container(request)
    try:
        status = c.job_status_store.get_job(job_id)
    except RoadmapGenerationJobNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return dict(status)


@router.put("/{roadmap_id}/items/{item_id}/move")
def move_item(
    roadmap_id: UUID,
    item_id: UUID,
    body: _MoveItemRequest,
    request: Request,
) -> dict[str, object]:
    """item を別の親・並び順へ移動する。"""
    from roadmap.application.roadmap_item_crud import move_roadmap_item
    from roadmap.domain.roadmap_item_crud_types import (
        RoadmapItemCrudInputError,
        RoadmapItemCrudNotFoundError,
        RoadmapItemMoveInput,
    )

    c = _container(request)
    try:
        result = move_roadmap_item(
            RoadmapItemMoveInput(
                roadmap_id=roadmap_id,
                item_id=item_id,
                target_parent_id=body.target_parent_id,
                target_order=body.target_order,
            ),
            store=c.roadmap_item_crud_store,
        )
    except RoadmapItemCrudNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except RoadmapItemCrudInputError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return {"moved_item": _serialize_crud_item(result.moved_item)}


@router.post("/{roadmap_id}/items", status_code=201)
def add_item(
    roadmap_id: UUID,
    body: _AddItemRequest,
    request: Request,
) -> dict[str, object]:
    """item を追加する。"""
    from roadmap.application.roadmap_item_crud import add_roadmap_item
    from roadmap.domain.roadmap_item_crud_types import (
        RoadmapItemAddInput,
        RoadmapItemCrudInputError,
        RoadmapItemCrudNotFoundError,
    )

    c = _container(request)
    try:
        result = add_roadmap_item(
            RoadmapItemAddInput(
                roadmap_id=roadmap_id,
                parent_id=body.parent_id,
                title=body.title,
                description=body.description,
                order=body.order,
            ),
            store=c.roadmap_item_crud_store,
            id_generator=c.uuid_generator,
        )
    except RoadmapItemCrudNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except RoadmapItemCrudInputError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return {"created_item": _serialize_crud_item(result.created_item)}


@router.delete("/{roadmap_id}/items/{item_id}")
def delete_item(
    roadmap_id: UUID,
    item_id: UUID,
    request: Request,
) -> dict[str, object]:
    """item とその子孫を削除する。"""
    from roadmap.application.roadmap_item_crud import delete_roadmap_item
    from roadmap.domain.roadmap_item_crud_types import (
        RoadmapItemCrudInputError,
        RoadmapItemCrudNotFoundError,
        RoadmapItemDeleteInput,
    )

    c = _container(request)
    try:
        result = delete_roadmap_item(
            RoadmapItemDeleteInput(roadmap_id=roadmap_id, item_id=item_id),
            store=c.roadmap_item_crud_store,
        )
    except RoadmapItemCrudNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except RoadmapItemCrudInputError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return {
        "deleted_item_ids": [str(i) for i in result.deleted_item_ids],
        "deleted_count": result.deleted_count,
    }


def _serialize_candidate(candidate: object) -> dict[str, object]:
    """topic 候補の返却形を API 契約にそろえる。"""
    return {
        "name": getattr(candidate, "name", ""),
        "source": getattr(candidate, "source", ""),
    }


def _serialize_crud_item(item: object) -> dict[str, object]:
    """CRUD 結果の item を JSON 互換形に変換する。"""
    return {
        "id": str(getattr(item, "id", "")),
        "roadmap_id": str(getattr(item, "roadmap_id", "")),
        "parent_id": _str_or_none(getattr(item, "parent_id", None)),
        "title": getattr(item, "title", ""),
        "description": getattr(item, "description", ""),
        "level": getattr(item, "level", ""),
        "order": getattr(item, "order", 0),
        "score": getattr(item, "score", 0),
    }


def _str_or_none(value: object) -> str | None:
    """UUID 互換値を API 応答用に文字列化する。"""
    return str(value) if value is not None else None
