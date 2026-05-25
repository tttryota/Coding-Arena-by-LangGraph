"""Quiz API endpoints."""

from __future__ import annotations

from typing import TYPE_CHECKING, Literal

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from api.dependencies import Container

router = APIRouter(prefix="/sessions", tags=["quiz"])


class _StartSessionRequest(BaseModel):
    roadmap_item_id: str


class _SubmitInputRequest(BaseModel):
    user_input: str = Field(min_length=1)
    input_source: Literal["form", "chat"] = "form"


def _container(request: Request) -> Container:
    c = getattr(request.app.state, "container", None)
    if c is None:
        raise HTTPException(status_code=503, detail="Service not initialized")
    return c  # type: ignore[return-value]


@router.post("", status_code=201)
def start_session(body: _StartSessionRequest, request: Request) -> dict:
    from quiz.application.session_lifecycle import start_session as _start
    from quiz.application.session_lifecycle_types import (
        QuizSessionLifecycleError,
        StartSessionInput,
    )

    c = _container(request)
    if c.graph_runner is None:
        raise HTTPException(
            status_code=503,
            detail="Quiz service unavailable: embedder not configured",
        )
    try:
        result = _start(
            StartSessionInput(roadmap_item_id=body.roadmap_item_id),
            session_store=c.quiz_session_store,
            item_reader=c.roadmap_item_read_store,
            graph_runner=c.graph_runner,
        )
    except QuizSessionLifecycleError as exc:
        raise HTTPException(status_code=422, detail=exc.message) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return {
        "session_id": result.session_id,
        "resume_required": result.resume_required,
        "resume_session_id": result.resume_session_id,
    }


@router.post("/{session_id}/input")
def submit_input(session_id: str, body: _SubmitInputRequest, request: Request) -> dict:
    from quiz.application.session_lifecycle import resume_session
    from quiz.application.session_lifecycle_types import (
        QuizSessionLifecycleError,
        ResumeSessionInput,
    )

    c = _container(request)
    if c.graph_runner is None:
        raise HTTPException(
            status_code=503,
            detail="Quiz service unavailable: embedder not configured",
        )
    try:
        result = resume_session(
            ResumeSessionInput(
                session_id=session_id,
                user_input=body.user_input,
                input_source=body.input_source,
            ),
            session_store=c.quiz_session_store,
            answer_store=c.quiz_answer_store,
            item_reader=c.roadmap_item_read_store,
            graph_runner=c.graph_runner,
        )
    except QuizSessionLifecycleError as exc:
        if exc.error_code == "session_resume_transient_llm_error":
            raise HTTPException(status_code=503, detail=exc.message) from exc
        raise HTTPException(status_code=422, detail=exc.message) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return dict(result)


@router.get("/{session_id}")
def get_session(session_id: str, request: Request) -> dict:
    c = _container(request)
    try:
        session = c.quiz_session_store.find_session(session_id)
    except (ValueError, KeyError) as exc:
        raise HTTPException(status_code=404, detail="Session not found") from exc
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")
    response: dict = {"session_id": session_id, "session": session}
    if c.graph_runner is not None:
        try:
            graph_state = c.graph_runner.get_state(thread_id=session_id)
            response["graph_state"] = dict(graph_state)
        except LookupError:
            pass
    return response
