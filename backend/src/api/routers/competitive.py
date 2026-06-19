"""競プロセッションの開始・提出・取得を提供する。"""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING, cast

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from collections.abc import Mapping

    from api.dependencies import Container
    from competitive.application.competitive_graph import CompetitiveGraphRunner
    from competitive.application.question_response_types import (
        CompetitiveChatMessage,
        QuestionResponseLlmClient,
    )
    from competitive.domain.competitive_types import (
        CompetitiveSessionState,
        ProblemExample,
        ProgrammingLanguage,
    )
    from competitive.infrastructure.sql_competitive_store import (
        CompetitiveAnswerRecord,
    )

router = APIRouter(prefix="/algorithm-quiz", tags=["competitive"])

_HIDDEN_FIELDS = frozenset(
    {
        "reference_solution",
        "grading_rubric",
    },
)


class _StartSessionRequest(BaseModel):
    """競プロセッション開始要求。"""

    theme_id: str | None = None


class _SubmitAnswerRequest(BaseModel):
    """競プロ回答提出要求。"""

    user_code: str = Field(min_length=1)


class _CompetitiveChatMessage(BaseModel):
    """競プロ質問のローカル会話履歴。"""

    role: str
    content: str = Field(min_length=1)


class _QuestionRequest(BaseModel):
    """競プロ問題への質問要求。"""

    user_input: str = Field(min_length=1)
    history: list[_CompetitiveChatMessage] = Field(default_factory=list)


def _container(request: Request) -> Container:
    """request から共有 container を取り出す。"""
    c = getattr(request.app.state, "container", None)
    if c is None:
        raise HTTPException(status_code=503, detail="Service not initialized")
    return cast("Container", c)


def _require_runner(c: Container) -> CompetitiveGraphRunner:
    """競プロ graph が有効な環境かを確認する。"""
    if c.competitive_graph_runner is None:
        raise HTTPException(
            status_code=503,
            detail="Competitive service unavailable",
        )
    return cast("CompetitiveGraphRunner", c.competitive_graph_runner)


def _require_question_llm(c: Container) -> QuestionResponseLlmClient:
    """競プロ質問応答 LLM が有効な環境かを確認する。"""
    llm = getattr(c, "competitive_question_llm", None)
    if llm is None:
        raise HTTPException(
            status_code=503,
            detail="Competitive question service unavailable",
        )
    return cast("QuestionResponseLlmClient", llm)


def _question_error_to_http(exc: Exception) -> HTTPException:
    """競プロ質問 API のエラーを HTTP ステータスへ変換する。"""
    error_code = getattr(exc, "error_code", None)
    if error_code == "llm_request_failed":
        return HTTPException(status_code=503, detail=str(exc))
    if error_code == "llm_response_parse_failed":
        return HTTPException(status_code=502, detail=str(exc))
    return HTTPException(status_code=503, detail=str(exc))


def _run_graph_start(
    runner: CompetitiveGraphRunner,
    state: dict[str, object],
    thread_id: str,
) -> None:
    """競プロ graph の開始時例外を HTTP エラーへ変換する。"""
    from competitive.application.competitive_graph import TransientLlmNodeError
    from competitive.domain.competitive_types import CompetitiveError

    try:
        runner.start_graph(cast("CompetitiveSessionState", state), thread_id=thread_id)
    except TransientLlmNodeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except CompetitiveError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


def _run_graph_resume(
    runner: CompetitiveGraphRunner,
    user_input: dict[str, object],
    thread_id: str,
) -> None:
    """競プロ graph の再開時例外を HTTP エラーへ変換する。"""
    from competitive.application.competitive_graph import TransientLlmNodeError
    from competitive.domain.competitive_types import CompetitiveError

    try:
        runner.resume_graph(user_input, thread_id=thread_id)
    except TransientLlmNodeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except CompetitiveError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get("/themes")
def list_themes(request: Request) -> dict[str, object]:
    """テーマ一覧を取得する。"""
    from competitive.domain.competitive_types import CompetitiveError

    c = _container(request)
    try:
        themes = c.algo_theme_reader.list_themes()
    except CompetitiveError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return {"themes": themes}


@router.get("/sessions")
def list_sessions(request: Request) -> dict[str, object]:
    """最近のセッション一覧を返す。"""
    c = _container(request)
    sessions = c.competitive_store.list_recent_sessions(limit=50)
    items = []
    for s in sessions:
        # 一覧は score までを軽く返し、詳細の秘匿フィールドは含めない。
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
    request: Request,
    body: _StartSessionRequest | None = None,
) -> dict[str, object]:
    """セッションを開始する。テーマ未指定時は学習順で次のテーマを選択。"""
    c = _container(request)
    runner = _require_runner(c)
    session_id = str(uuid.uuid4())
    initial_state: dict[str, object] = {"session_id": session_id}
    if body and body.theme_id:
        initial_state["algo_theme_id"] = body.theme_id

    _run_graph_start(runner, initial_state, session_id)
    state = runner.get_state(thread_id=session_id)

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


def _save_answer(
    c: Container,
    session_id: str,
    state: Mapping[str, object],
    user_code: str,
) -> CompetitiveAnswerRecord:
    """採点済み回答を保存し、二重提出だけは 409 に寄せる。"""
    from sqlalchemy.exc import IntegrityError

    try:
        return c.competitive_store.save_answer_and_complete(
            session_id=session_id,
            answer_text=user_code,
            score=cast("int", state.get("score", 0)),
            feedback=cast("str", state.get("feedback", "")),
            time_complexity=cast("str", state.get("time_complexity", "")),
            space_complexity=cast("str", state.get("space_complexity", "")),
            improvement_suggestions=cast(
                "str",
                state.get("improvement_suggestions", ""),
            ),
            rubric_scores_json=cast("str", state.get("rubric_scores_json", "[]")),
        )
    except IntegrityError as exc:
        raise HTTPException(
            status_code=409,
            detail="Answer already submitted",
        ) from exc
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/sessions/{session_id}/answer")
def submit_answer(
    session_id: str,
    body: _SubmitAnswerRequest,
    request: Request,
) -> dict[str, object]:
    """コードを提出して採点する。"""
    c = _container(request)
    runner = _require_runner(c)

    existing = c.competitive_store.find_answer_by_session(session_id)
    if existing is not None:
        raise HTTPException(status_code=409, detail="Answer already submitted")

    _run_graph_resume(runner, {"user_code": body.user_code}, session_id)

    try:
        state = runner.get_state(thread_id=session_id)
    except LookupError as exc:
        raise HTTPException(
            status_code=404,
            detail="Session not found",
        ) from exc

    answer = _save_answer(c, session_id, state, body.user_code)
    return {
        "session_id": session_id,
        "score": answer.score,
        "feedback": answer.feedback,
        "time_complexity": answer.time_complexity,
        "space_complexity": answer.space_complexity,
        "improvement_suggestions": answer.improvement_suggestions,
        "rubric_scores_json": answer.rubric_scores_json,
        "reference_solution": state.get("reference_solution", ""),
    }


@router.post("/sessions/{session_id}/question")
def ask_question(
    session_id: str,
    body: _QuestionRequest,
    request: Request,
) -> dict[str, object]:
    """問題への質問に答える。採点や状態更新は行わない。"""
    from competitive.domain.competitive_types import CompetitiveError

    c = _container(request)
    llm = _require_question_llm(c)
    try:
        details = c.competitive_store.get_session_details(session_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail="Session not found") from exc
    if details.get("status") == "completed":
        raise HTTPException(
            status_code=409,
            detail="Questions are unavailable after completion",
        )
    history = cast(
        "list[CompetitiveChatMessage]",
        [item.model_dump() for item in body.history],
    )
    try:
        chat_response_text = llm.generate_chat_response(
            problem_statement=cast("str", details["problem_statement"]),
            input_format=cast("str", details["input_format"]),
            output_format=cast("str", details["output_format"]),
            constraints=cast("str", details["constraints"]),
            examples=cast("list[ProblemExample]", details["examples"]),
            programming_language=cast(
                "ProgrammingLanguage",
                details["programming_language"],
            ),
            user_input=body.user_input,
            history=history,
        )
    except CompetitiveError as exc:
        raise _question_error_to_http(exc) from exc
    return {
        "session_id": session_id,
        "chat_response_text": chat_response_text,
    }


@router.get("/sessions/{session_id}")
def get_session(session_id: str, request: Request) -> dict[str, object]:
    """セッション状態を取得する(reference_solution/rubricは除外)。"""
    c = _container(request)
    try:
        details = c.competitive_store.get_session_details(session_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail="Session not found") from exc
    response = {k: v for k, v in details.items() if k not in _HIDDEN_FIELDS}
    # 非公開採点情報は永続化していても取得 API には出さない。
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
