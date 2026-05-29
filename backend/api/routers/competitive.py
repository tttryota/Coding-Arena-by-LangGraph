"""競プロクイズ API endpoints."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from api.dependencies import Container

router = APIRouter(prefix="/algorithm-quiz", tags=["competitive"])

_HIDDEN_FIELDS = frozenset({
    "reference_solution",
    "grading_rubric",
})


class _StartSessionRequest(BaseModel):
    theme_id: str | None = None


class _SubmitAnswerRequest(BaseModel):
    user_code: str = Field(min_length=1)


def _container(request: Request) -> Container:
    c = getattr(request.app.state, "container", None)
    if c is None:
        raise HTTPException(status_code=503, detail="Service not initialized")
    return c  # type: ignore[return-value]


def _require_runner(c: Container) -> object:
    if c.competitive_graph_runner is None:
        raise HTTPException(
            status_code=503,
            detail="Competitive service unavailable",
        )
    return c.competitive_graph_runner


def _run_graph_start(runner: object, state: dict, thread_id: str) -> None:
    from competitive.application.competitive_graph import TransientLlmNodeError
    from competitive.domain.competitive_types import CompetitiveError

    try:
        runner.start_graph(state, thread_id=thread_id)  # type: ignore[union-attr]
    except TransientLlmNodeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except CompetitiveError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


def _run_graph_resume(
    runner: object, user_input: dict, thread_id: str,
) -> None:
    from competitive.application.competitive_graph import TransientLlmNodeError
    from competitive.domain.competitive_types import CompetitiveError

    try:
        runner.resume_graph(user_input, thread_id=thread_id)  # type: ignore[union-attr]
    except TransientLlmNodeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except CompetitiveError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except (ValueError, LookupError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get("/themes")
def list_themes(request: Request) -> dict:
    """テーマ一覧を取得する。"""
    from competitive.domain.competitive_types import CompetitiveError

    c = _container(request)
    try:
        themes = c.algo_theme_reader.list_themes()
    except CompetitiveError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return {"themes": themes}


@router.get("/sessions")
def list_sessions(request: Request) -> dict:
    """最近のセッション一覧を返す。"""
    c = _container(request)
    sessions = c.competitive_store.list_recent_sessions(limit=50)
    items = []
    for s in sessions:
        details = c.competitive_store.get_session_details(s.id)
        item: dict[str, object] = {
            "session_id": s.id,
            "theme_id": s.theme_id,
            "theme_label": s.theme_label,
            "theme_category": s.theme_category,
            "programming_language": s.programming_language,
            "status": s.status,
            "created_at": details.get("created_at", ""),
        }
        if s.status == "completed":
            answer = c.competitive_store.find_answer_by_session(s.id)
            if answer:
                item["score"] = answer.score
        items.append(item)
    return {"sessions": items}


@router.post("/sessions", status_code=201)
def start_session(
    request: Request, body: _StartSessionRequest | None = None,
) -> dict:
    """セッションを開始する。テーマ未指定時はランダム選択。"""
    c = _container(request)
    runner = _require_runner(c)
    session_id = str(uuid.uuid4())
    initial_state: dict[str, object] = {"session_id": session_id}
    if body and body.theme_id:
        initial_state["algo_theme_id"] = body.theme_id

    _run_graph_start(runner, initial_state, session_id)
    state = runner.get_state(thread_id=session_id)  # type: ignore[union-attr]

    c.competitive_store.create_session(
        session_id=session_id,
        theme_id=state.get("algo_theme_id", ""),
        theme_label=state.get("algo_theme_label", ""),
        theme_category=state.get("algo_theme_category", ""),
        programming_language=state.get("programming_language", ""),
        problem_statement=state.get("problem_statement", ""),
        input_format=state.get("input_format", ""),
        output_format=state.get("output_format", ""),
        constraints=state.get("constraints", ""),
        examples=state.get("examples", []),
        reference_solution=state.get("reference_solution", ""),
        grading_rubric=state.get("grading_rubric", []),
    )

    return {
        "session_id": session_id,
        "theme_id": state.get("algo_theme_id"),
        "theme_label": state.get("algo_theme_label"),
        "theme_category": state.get("algo_theme_category"),
        "programming_language": state.get("programming_language"),
        "problem_statement": state.get("problem_statement"),
        "input_format": state.get("input_format"),
        "output_format": state.get("output_format"),
        "constraints": state.get("constraints"),
        "examples": state.get("examples"),
    }


def _save_answer(c: Container, session_id: str, state: dict, user_code: str) -> object:
    from sqlalchemy.exc import IntegrityError

    try:
        return c.competitive_store.save_answer_and_complete(
            session_id=session_id,
            answer_text=user_code,
            score=state.get("score", 0),
            feedback=state.get("feedback", ""),
            time_complexity=state.get("time_complexity", ""),
            space_complexity=state.get("space_complexity", ""),
            improvement_suggestions=state.get("improvement_suggestions", ""),
            rubric_scores_json=state.get("rubric_scores_json", "[]"),
        )
    except IntegrityError as exc:
        raise HTTPException(
            status_code=409, detail="Answer already submitted",
        ) from exc
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/sessions/{session_id}/answer")
def submit_answer(
    session_id: str, body: _SubmitAnswerRequest, request: Request,
) -> dict:
    """コードを提出して採点する。"""
    c = _container(request)
    runner = _require_runner(c)

    _run_graph_resume(runner, {"user_code": body.user_code}, session_id)

    try:
        state = runner.get_state(thread_id=session_id)  # type: ignore[union-attr]
    except LookupError as exc:
        raise HTTPException(
            status_code=404, detail="Session not found",
        ) from exc

    answer = _save_answer(c, session_id, state, body.user_code)
    return {
        "session_id": session_id,
        "score": answer.score,  # type: ignore[union-attr]
        "feedback": answer.feedback,  # type: ignore[union-attr]
        "time_complexity": answer.time_complexity,  # type: ignore[union-attr]
        "space_complexity": answer.space_complexity,  # type: ignore[union-attr]
        "improvement_suggestions": answer.improvement_suggestions,  # type: ignore[union-attr]
        "rubric_scores_json": answer.rubric_scores_json,  # type: ignore[union-attr]
    }


@router.get("/sessions/{session_id}")
def get_session(session_id: str, request: Request) -> dict:
    """セッション状態を取得する(reference_solution/rubricは除外)。"""
    c = _container(request)
    try:
        details = c.competitive_store.get_session_details(session_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail="Session not found") from exc
    response = {
        k: v for k, v in details.items()
        if k not in _HIDDEN_FIELDS
    }
    response["session_id"] = response.pop("id", session_id)
    answer = c.competitive_store.find_answer_by_session(session_id)
    if answer is not None:
        response["score"] = answer.score
        response["feedback"] = answer.feedback
        response["time_complexity"] = answer.time_complexity
        response["space_complexity"] = answer.space_complexity
        response["improvement_suggestions"] = answer.improvement_suggestions
        response["rubric_scores_json"] = answer.rubric_scores_json
    return response
