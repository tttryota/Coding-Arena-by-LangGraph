"""SQL道場 API。"""

from __future__ import annotations

import json
import uuid
from typing import TYPE_CHECKING, cast

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from sql_dojo.domain.sql_dojo_types import (
    SqlDojoCatalog,
    SqlDojoDifficulty,
    SqlDojoEvaluationError,
    SqlDojoGenerationError,
    SqlDojoQuestionError,
)

if TYPE_CHECKING:
    from api.dependencies import Container

router = APIRouter(prefix="/sql-dojo", tags=["sql-dojo"])


class _StartSessionRequest(BaseModel):
    difficulty: SqlDojoDifficulty = "beginner"
    theme_family: str | None = None


class _SubmitAnswerRequest(BaseModel):
    user_sql: str = Field(min_length=1)


class _ChatMessage(BaseModel):
    role: str
    content: str = Field(min_length=1)


class _QuestionRequest(BaseModel):
    user_input: str = Field(min_length=1)
    history: list[_ChatMessage] = Field(default_factory=list)


def _container(request: Request) -> Container:
    c = getattr(request.app.state, "container", None)
    if c is None:
        raise HTTPException(status_code=503, detail="Service not initialized")
    return cast("Container", c)


def _question_error_to_http(exc: Exception) -> HTTPException:
    error_code = getattr(exc, "error_code", None)
    if error_code == "llm_request_failed":
        return HTTPException(status_code=503, detail=str(exc))
    if error_code == "llm_response_parse_failed":
        return HTTPException(status_code=502, detail=str(exc))
    return HTTPException(status_code=503, detail=str(exc))


@router.get("/catalog")
def get_catalog(request: Request) -> SqlDojoCatalog:
    c = _container(request)
    return c.sql_theme_bank.list_catalog()


@router.get("/sessions")
def list_sessions(request: Request) -> dict[str, object]:
    c = _container(request)
    items = []
    for session in c.sql_dojo_store.list_recent_sessions(limit=50):
        details = c.sql_dojo_store.get_session_details(session.id)
        item: dict[str, object] = {
            "session_id": session.id,
            "theme_family": session.theme_family,
            "difficulty": session.difficulty,
            "dialect": session.dialect,
            "theme_title": session.theme_title,
            "status": session.status,
            "created_at": details["created_at"],
        }
        answer = c.sql_dojo_store.find_answer_by_session(session.id)
        if answer is not None:
            item["score"] = answer.score
        items.append(item)
    return {"sessions": items}


@router.post("/sessions", status_code=201)
def start_session(request: Request, body: _StartSessionRequest) -> dict[str, object]:
    c = _container(request)
    session_id = str(uuid.uuid4())
    try:
        problem = c.sql_theme_bank.create_problem(
            difficulty=body.difficulty,
            theme_family=body.theme_family,
        )
    except SqlDojoGenerationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    c.sql_dojo_store.create_session(
        session_id=session_id,
        theme_family=problem["family"],
        difficulty=problem["difficulty"],
        dialect=problem["dialect"],
        theme_title=problem["theme_title"],
        business_domain=problem["business_domain"],
        target_skill=problem["target_skill"],
        problem_statement=problem["problem_statement"],
        schema_markdown=problem["schema_markdown"],
        sample_data_json=problem["sample_data_json"],
        expected_focus=problem["expected_focus"],
        reference_sql=problem["reference_sql"],
        grading_contract_json=json.dumps(problem["grading_contract"], ensure_ascii=False),
    )
    return {
        "session_id": session_id,
        "theme_family": problem["family"],
        "difficulty": problem["difficulty"],
        "dialect": problem["dialect"],
        "theme_title": problem["theme_title"],
        "business_domain": problem["business_domain"],
        "target_skill": problem["target_skill"],
        "problem_statement": problem["problem_statement"],
        "schema_markdown": problem["schema_markdown"],
        "sample_data_json": problem["sample_data_json"],
        "expected_focus": problem["expected_focus"],
    }


@router.get("/sessions/{session_id}")
def get_session(session_id: str, request: Request) -> dict[str, object]:
    c = _container(request)
    try:
        details = c.sql_dojo_store.get_session_details(session_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    response = {
        "session_id": details["session_id"],
        "theme_family": details["theme_family"],
        "difficulty": details["difficulty"],
        "dialect": details["dialect"],
        "theme_title": details["theme_title"],
        "business_domain": details["business_domain"],
        "target_skill": details["target_skill"],
        "problem_statement": details["problem_statement"],
        "schema_markdown": details["schema_markdown"],
        "sample_data_json": details["sample_data_json"],
        "expected_focus": details["expected_focus"],
        "status": details["status"],
        "created_at": details["created_at"],
    }
    answer = c.sql_dojo_store.find_answer_by_session(session_id)
    if answer is not None:
        response.update(
            {
                "score": answer.score,
                "feedback": answer.feedback,
                "rule_breakdown_json": answer.rule_breakdown_json,
                "improvement_suggestions": answer.improvement_suggestions,
            },
        )
    return response


@router.post("/sessions/{session_id}/answer")
def submit_answer(
    session_id: str,
    body: _SubmitAnswerRequest,
    request: Request,
) -> dict[str, object]:
    c = _container(request)
    try:
        details = c.sql_dojo_store.get_session_details(session_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    if c.sql_dojo_store.find_answer_by_session(session_id) is not None:
        raise HTTPException(status_code=409, detail="Answer already submitted")

    grading_contract = c.sql_dojo_store.grading_contract_as_dict(details)
    try:
        from sql_dojo.application.sql_grading import grade_sql_answer

        grading_result = grade_sql_answer(body.user_sql, grading_contract)
        llm_feedback = c.sql_dojo_feedback_llm.generate_feedback(
            family=str(details["theme_family"]),
            difficulty=str(details["difficulty"]),
            problem_statement=str(details["problem_statement"]),
            schema_markdown=str(details["schema_markdown"]),
            expected_focus=str(details["expected_focus"]),
            reference_sql=str(details["reference_sql"]),
            user_sql=body.user_sql,
            rule_breakdown_json=grading_result.rule_breakdown_json,
            score=grading_result.score,
        )
    except SqlDojoEvaluationError as exc:
        if exc.error_code == "llm_request_failed":
            raise HTTPException(status_code=503, detail=str(exc)) from exc
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    answer = c.sql_dojo_store.save_answer_and_complete(
        session_id=session_id,
        answer_text=body.user_sql,
        score=grading_result.score,
        feedback=llm_feedback["feedback"],
        rule_breakdown_json=grading_result.rule_breakdown_json,
        improvement_suggestions=llm_feedback["improvement_suggestions"],
    )
    return {
        "session_id": session_id,
        "score": answer.score,
        "feedback": answer.feedback,
        "rule_breakdown_json": answer.rule_breakdown_json,
        "improvement_suggestions": answer.improvement_suggestions,
        "reference_sql": details["reference_sql"],
    }


@router.post("/sessions/{session_id}/question")
def ask_question(
    session_id: str,
    body: _QuestionRequest,
    request: Request,
) -> dict[str, object]:
    c = _container(request)
    try:
        details = c.sql_dojo_store.get_session_details(session_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    if c.sql_dojo_store.find_answer_by_session(session_id) is not None:
        raise HTTPException(status_code=409, detail="Session already completed")
    try:
        text = c.sql_dojo_question_llm.generate_chat_response(
            problem_statement=str(details["problem_statement"]),
            schema_markdown=str(details["schema_markdown"]),
            expected_focus=str(details["expected_focus"]),
            user_input=body.user_input,
            history=[{"role": item.role, "content": item.content} for item in body.history],
        )
    except SqlDojoQuestionError as exc:
        raise _question_error_to_http(exc) from exc
    return {"session_id": session_id, "chat_response_text": text}
