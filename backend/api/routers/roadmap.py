"""Roadmap API endpoints."""

from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID  # noqa: TC003

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

if TYPE_CHECKING:
    from api.dependencies import Container

router = APIRouter(prefix="/roadmaps", tags=["roadmaps"])


class _GenerateRequest(BaseModel):
    topic: str


class _AddItemRequest(BaseModel):
    parent_id: UUID | None = None
    title: str
    description: str
    order: int | None = None


class _MoveItemRequest(BaseModel):
    target_parent_id: UUID | None = None
    target_order: int


def _container(request: Request) -> Container:
    c = getattr(request.app.state, "container", None)
    if c is None:
        raise HTTPException(status_code=503, detail="Service not initialized")
    return c  # type: ignore[return-value]


@router.get("")
def list_roadmaps(request: Request) -> dict:
    from dataclasses import asdict

    from roadmap.application.roadmap_retrieval import list_roadmaps as _list

    c = _container(request)
    result = _list(reader=c.roadmap_retrieval_reader)
    return asdict(result)  # type: ignore[arg-type]


@router.get("/{roadmap_id}")
def get_roadmap(roadmap_id: UUID, request: Request) -> dict:
    from roadmap.application.roadmap_retrieval import get_roadmap as _get
    from roadmap.domain.roadmap_retrieval_types import RoadmapRetrievalNotFoundError

    c = _container(request)
    try:
        return _get(roadmap_id, reader=c.roadmap_retrieval_reader)  # type: ignore[return-value]
    except RoadmapRetrievalNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/generate", status_code=202)
def generate_roadmap(body: _GenerateRequest, request: Request) -> dict:
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
def get_generation_job(job_id: UUID, request: Request) -> dict:
    from roadmap.domain.roadmap_generation_types import (
        RoadmapGenerationJobNotFoundError,
    )

    c = _container(request)
    try:
        status = c.job_status_store.get_job(job_id)
    except RoadmapGenerationJobNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return dict(status)


@router.post("/{roadmap_id}/items", status_code=201)
def add_item(
    roadmap_id: UUID,
    body: _AddItemRequest,
    request: Request,
) -> dict:
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
) -> dict:
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


def _serialize_crud_item(item: object) -> dict:
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
    return str(value) if value is not None else None
