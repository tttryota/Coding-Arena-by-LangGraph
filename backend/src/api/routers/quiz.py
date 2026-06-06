"""通常 quiz とコーディングセッションの入口を提供する。"""

from __future__ import annotations

from typing import TYPE_CHECKING, Literal, cast

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from api.dependencies import Container
    from quiz.application.coding_graph import CodingGraphRunner
    from quiz.application.graph import QuizGraphRunner
    from quiz.application.session_lifecycle_types import QuizAnswerStore
    from quiz.domain.coding_session_state import CodingSessionState
    from quiz.domain.session_state import RoadmapItemLevel

router = APIRouter(prefix="/sessions", tags=["quiz"])


class _StartSessionRequest(BaseModel):
    """ロードマップ項目からセッションを始めるための入力。"""

    roadmap_item_id: str


class _SubmitInputRequest(BaseModel):
    """一時停止中セッションを再開するための入力。"""

    user_input: str = Field(min_length=1)
    input_source: Literal["form", "chat"] = "form"


def _container(request: Request) -> Container:
    """request から共有 container を取り出す。"""
    c = getattr(request.app.state, "container", None)
    if c is None:
        raise HTTPException(status_code=503, detail="Service not initialized")
    return cast("Container", c)


def _require_quiz_runner(c: Container) -> QuizGraphRunner:
    """通常 quiz が有効な環境かを確認して runner を返す。"""
    runner = c.graph_runner
    if runner is None:
        raise HTTPException(
            status_code=503,
            detail="Quiz service unavailable: embedder not configured",
        )
    return cast("QuizGraphRunner", runner)


def _require_coding_runner(c: Container) -> CodingGraphRunner:
    """コーディングセッション用 runner を返す。"""
    runner = c.coding_graph_runner
    if runner is None:
        raise HTTPException(
            status_code=503,
            detail="Coding session service unavailable",
        )
    return cast("CodingGraphRunner", runner)


@router.post("", status_code=201)
def start_session(
    body: _StartSessionRequest, request: Request,
) -> dict[str, object]:
    """通常 quiz セッションを開始する。"""
    from quiz.application.session_lifecycle import start_session as _start
    from quiz.application.session_lifecycle_types import (
        QuizSessionLifecycleError,
        StartSessionInput,
    )

    c = _container(request)
    runner = _require_quiz_runner(c)
    try:
        result = _start(
            StartSessionInput(roadmap_item_id=body.roadmap_item_id),
            session_store=c.quiz_session_store,
            item_reader=c.roadmap_item_read_store,
            graph_runner=runner,
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
def submit_input(
    session_id: str, body: _SubmitInputRequest, request: Request,
) -> dict[str, object]:
    """セッション種別を判定して再開処理を振り分ける。"""
    c = _container(request)

    if c.coding_graph_runner is not None:
        try:
            c.coding_graph_runner.get_state(thread_id=session_id)
            return _resume_coding_session(c, session_id, body)
        except LookupError:
            # coding 側に状態がなければ通常 quiz として再解釈する。
            pass

    return _resume_quiz_session(c, session_id, body)


def _resume_coding_session(
    c: Container, session_id: str, body: _SubmitInputRequest,
) -> dict[str, object]:
    """コーディングセッションを再開して最新状態を返す。"""
    from quiz.application.coding_graph import TransientLlmNodeError

    runner = _require_coding_runner(c)
    try:
        runner.resume_graph(
            {"user_input": body.user_input, "input_source": body.input_source},
            thread_id=session_id,
        )
    except TransientLlmNodeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except (ValueError, LookupError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    state = runner.get_state(thread_id=session_id)
    return dict(state)


def _resume_quiz_session(
    c: Container, session_id: str, body: _SubmitInputRequest,
) -> dict[str, object]:
    """通常 quiz セッションを再開する。"""
    from quiz.application.session_lifecycle import resume_session
    from quiz.application.session_lifecycle_types import (
        QuizSessionLifecycleError,
        ResumeSessionInput,
    )

    runner = _require_quiz_runner(c)
    try:
        result = resume_session(
            ResumeSessionInput(
                session_id=session_id,
                user_input=body.user_input,
                input_source=body.input_source,
            ),
            session_store=c.quiz_session_store,
            answer_store=cast("QuizAnswerStore", c.quiz_answer_store),
            item_reader=c.roadmap_item_read_store,
            graph_runner=runner,
        )
    except QuizSessionLifecycleError as exc:
        # 一過性 LLM エラーだけは再試行可能なので 503 に分ける。
        if exc.error_code == "session_resume_transient_llm_error":
            raise HTTPException(status_code=503, detail=exc.message) from exc
        raise HTTPException(status_code=422, detail=exc.message) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return dict(result)


@router.post("/coding", status_code=201)
def start_coding_session(  # noqa: PLR0915
    body: _StartSessionRequest, request: Request,
) -> dict[str, object]:
    """コーディングセッションを開始する(座学→練習フロー)。"""
    import uuid

    c = _container(request)
    runner = _require_coding_runner(c)
    session_id = str(uuid.uuid4())
    try:
        item = c.roadmap_item_read_store.find_item(body.roadmap_item_id)
    except (ValueError, KeyError) as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    if item is None:
        raise HTTPException(status_code=404, detail="Roadmap item not found")

    initial_state: CodingSessionState = {
        "session_id": session_id,
        "roadmap_item_id": body.roadmap_item_id,
        "roadmap_item_level": cast("RoadmapItemLevel", item.level),
        "roadmap_item_title": item.title,
        "roadmap_item_description": item.description,
        "is_resumed": False,
    }
    from quiz.application.coding_graph import TransientLlmNodeError

    try:
        runner.start_graph(initial_state, thread_id=session_id)
    except TransientLlmNodeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except (ValueError, LookupError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    state = runner.get_state(thread_id=session_id)
    return {
        "session_id": session_id,
        "lecture_content": state.get("lecture_content"),
        "lecture_phase_active": state.get("lecture_phase_active"),
    }


@router.post("/{session_id}/practice/start")
def start_practice(session_id: str, request: Request) -> dict[str, object]:
    """座学フェーズからコーディング練習に遷移する。"""
    c = _container(request)
    runner = _require_coding_runner(c)
    from quiz.application.coding_graph import TransientLlmNodeError

    try:
        runner.resume_graph(
            {"lecture_phase_active": False},
            thread_id=session_id,
        )
    except TransientLlmNodeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except (ValueError, LookupError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    state = runner.get_state(thread_id=session_id)
    return {
        "session_id": session_id,
        "confirmation_points": state.get("confirmation_points", []),
        "current_question_text": state.get("current_question_text"),
        "current_example_code": state.get("current_example_code"),
        "current_format": state.get("current_format"),
        "current_point_index": state.get("current_point_index", 0),
        "total_questions_asked": state.get("total_questions_asked", 1),
    }


@router.get("/{session_id}")
def get_session(  # noqa: PLR0915
    session_id: str, request: Request,
) -> dict[str, object]:
    """永続化済み session と graph 状態を可能な範囲で束ねて返す。"""
    c = _container(request)
    response: dict[str, object] = {"session_id": session_id}
    try:
        session = c.quiz_session_store.find_session(session_id)
        if session is not None:
            response["session"] = session
    except (ValueError, KeyError):
        pass
    if c.coding_graph_runner is not None:
        try:
            coding_state = c.coding_graph_runner.get_state(thread_id=session_id)
            response["graph_state"] = dict(coding_state)
        except LookupError:
            pass
    if "graph_state" not in response and c.graph_runner is not None:
        try:
            # 同じ session_id を coding / 通常 quiz の両方で探索するのは、
            # 取得 API を一本に保ったまま既存 UI 契約を崩さないため。
            graph_state = c.graph_runner.get_state(thread_id=session_id)
            response["graph_state"] = dict(graph_state)
        except LookupError:
            pass
    if "session" not in response and "graph_state" not in response:
        raise HTTPException(status_code=404, detail="Session not found")
    return response
