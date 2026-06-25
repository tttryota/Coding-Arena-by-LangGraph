"""競プロうさぎ API。"""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING, Any, cast

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy.exc import IntegrityError

from algorithm_foundations.domain.foundation_types import (
    AlgorithmFoundationCatalogError,
    AlgorithmFoundationCatalogResponse,
    AlgorithmFoundationLanguageAdaptationError,
    AlgorithmFoundationProblem,
    AlgorithmFoundationUnit,
    AlgorithmFoundationUnitDetailResponse,
)
from competitive.domain.competitive_types import SolutionEvaluationError
from competitive.domain.languages import (
    default_language,
    is_supported_language,
    list_supported_languages,
)

if TYPE_CHECKING:
    from api.dependencies import Container

router = APIRouter(prefix="/algorithm-foundations", tags=["algorithm-foundations"])


class _StartSessionRequest(BaseModel):
    unit_id: str | None = None
    problem_id: str | None = None
    programming_language: str | None = None


class _SubmitAnswerRequest(BaseModel):
    user_code: str = Field(min_length=1)


def _container(request: Request) -> Container:
    c = getattr(request.app.state, "container", None)
    if c is None:
        raise HTTPException(status_code=503, detail="Service not initialized")
    return cast("Container", c)


def _history_maps(c: Container) -> tuple[dict[str, int | None], dict[str, str | None]]:
    rows = c.algorithm_foundation_store.list_unit_history()
    best_scores = {row.unit_id: row.best_score for row in rows}
    last_attempted_at = {row.unit_id: row.last_attempted_at for row in rows}
    return best_scores, last_attempted_at


def _problem_history_map(
    c: Container,
    unit_id: str,
) -> dict[str, dict[str, int | str | None]]:
    rows = c.algorithm_foundation_store.list_problem_history_for_unit(unit_id)
    return {
        row.problem_id: {
            "best_score": row.best_score,
            "last_attempted_at": row.last_attempted_at,
        }
        for row in rows
    }


def _evaluation_error_to_http(exc: SolutionEvaluationError) -> HTTPException:
    error_code = getattr(exc, "error_code", None)
    if error_code == "llm_response_parse_failed":
        return HTTPException(status_code=502, detail=str(exc))
    return HTTPException(status_code=503, detail=str(exc))


def _adaptation_error_to_http(
    exc: AlgorithmFoundationLanguageAdaptationError,
) -> HTTPException:
    error_code = getattr(exc, "error_code", None)
    if error_code == "llm_response_parse_failed":
        return HTTPException(status_code=502, detail=str(exc))
    return HTTPException(status_code=503, detail=str(exc))


@router.get("/languages")
def list_languages() -> dict[str, object]:
    return {"languages": list_supported_languages()}


def _has_unmet_prerequisites(
    prerequisite_unit_ids: list[str],
    best_scores: dict[str, int | None],
) -> bool:
    return any((best_scores.get(pid) or 0) < 80 for pid in prerequisite_unit_ids)


def _resolve_programming_language(
    body: _StartSessionRequest | None,
) -> str:
    programming_language = (
        body.programming_language if body is not None and body.programming_language
        else default_language()
    )
    if not is_supported_language(programming_language):
        raise HTTPException(
            status_code=422,
            detail=f"Unsupported programming language: {programming_language}",
        )
    return programming_language


def _load_unit_and_problem(
    c: Container,
    *,
    unit_id: str | None,
    problem_id: str | None,
    best_scores: dict[str, int | None],
) -> tuple[AlgorithmFoundationUnit, AlgorithmFoundationProblem]:
    if problem_id is not None and unit_id is None:
        raise HTTPException(
            status_code=422,
            detail="unit_id is required when problem_id is specified",
        )
    resolved_unit_id = unit_id or c.algorithm_foundation_catalog.pick_recommended_unit_id(
        best_scores,
    )
    try:
        unit = c.algorithm_foundation_catalog.get_unit(resolved_unit_id)
    except AlgorithmFoundationCatalogError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    try:
        if problem_id is not None:
            problem = c.algorithm_foundation_catalog.get_problem(
                resolved_unit_id,
                problem_id,
            )
        else:
            recent_problem_ids = c.algorithm_foundation_store.list_recent_problem_ids_for_unit(
                resolved_unit_id,
            )
            problem = c.algorithm_foundation_catalog.pick_problem(
                resolved_unit_id,
                recent_problem_ids,
            )
    except AlgorithmFoundationCatalogError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return unit, problem


def _adapt_reference_solution(
    c: Container,
    *,
    problem: AlgorithmFoundationProblem,
    programming_language: str,
) -> str:
    try:
        return cast(
            "str",
            c.algorithm_foundation_language_adapter.adapt_reference_solution(
            canonical_reference_solution=problem["canonical_reference_solution"],
            canonical_language=problem["canonical_language"],
            target_language=programming_language,
            problem_statement=problem["problem_statement"],
            input_format=problem["input_format"],
            output_format=problem["output_format"],
            constraints=problem["constraints"],
            examples=cast("list[dict[str, str]]", problem["examples"]),
            ),
        )
    except AlgorithmFoundationLanguageAdaptationError as exc:
        raise _adaptation_error_to_http(exc) from exc


_LEGACY_PROMPT_KIND_LABELS = {
    "知識をそのまま使う確認": "基本確認",
    "実装の定着": "実装確認",
    "境界条件の確認": "境界条件確認",
    "別表現への言い換え": "別視点確認",
    "制約付きの整理": "条件整理",
    "既習2unitの組み合わせ確認": "2unit組み合わせ確認",
    "実装のつなぎ込み": "実装つなぎ込み",
    "条件違いの確認": "条件違い確認",
}


def _display_problem_title(raw_title: str, unit_title: str) -> str:
    if " / " in raw_title:
        return raw_title
    if ":" not in raw_title:
        return raw_title
    prefix, suffix = raw_title.split(":", 1)
    title = suffix.strip()
    if title != unit_title:
        return raw_title
    normalized = _LEGACY_PROMPT_KIND_LABELS.get(prefix.strip(), prefix.strip())
    return f"{unit_title} / {normalized}"


def _concept_overview(
    c: Container,
    *,
    unit_id: str,
    fallback_title: str,
) -> str:
    try:
        return c.algorithm_foundation_catalog.get_unit(unit_id)["concept_overview"]
    except AlgorithmFoundationCatalogError:
        return f"{fallback_title}を使って答えを作る考え方を、この問題で確かめます。"


def _display_problem_statement(
    raw_statement: str,
    *,
    concept_overview: str,
) -> str:
    normalized_lines: list[str] = []
    for index, line in enumerate(raw_statement.splitlines()):
        if index == 0 and "として、" in line and " を使う 1 問です。" in line:
            normalized_lines.append(concept_overview)
            continue
        if line.startswith(("- ねらい:", "- 補足:")):
            continue
        normalized_lines.append(line)

    normalized = "\n".join(normalized_lines).strip()
    while "\n\n\n" in normalized:
        normalized = normalized.replace("\n\n\n", "\n\n")
    return normalized


@router.get("/catalog")
def get_catalog(request: Request) -> AlgorithmFoundationCatalogResponse:
    c = _container(request)
    best_scores, last_attempted_at = _history_maps(c)
    return c.algorithm_foundation_catalog.list_catalog(
        best_scores=best_scores,
        last_attempted_at=last_attempted_at,
    )


@router.get("/units/{unit_id}")
def get_unit_detail(
    unit_id: str,
    request: Request,
) -> AlgorithmFoundationUnitDetailResponse:
    c = _container(request)
    best_scores, last_attempted_at = _history_maps(c)
    try:
        unit = c.algorithm_foundation_catalog.get_unit(unit_id)
    except AlgorithmFoundationCatalogError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    problem_history = _problem_history_map(c, unit_id)
    return {
        "unit_id": unit["unit_id"],
        "theme_id": unit["theme_id"],
        "group_id": unit["group_id"],
        "group_title": unit["group_title"],
        "title": unit["title"],
        "concept_overview": unit["concept_overview"],
        "display_order": unit["display_order"],
        "prerequisite_unit_ids": unit["prerequisite_unit_ids"],
        "prerequisite_titles": unit["prerequisite_titles"],
        "allowed_knowledge": unit["allowed_knowledge"],
        "forbidden_knowledge": unit["forbidden_knowledge"],
        "target_skill": unit["target_skill"],
        "unit_kind": unit["unit_kind"],
        "problem_count": len(unit["problem_bank"]),
        "best_score": best_scores.get(unit_id),
        "last_attempted_at": last_attempted_at.get(unit_id),
        "has_unmet_prerequisites": _has_unmet_prerequisites(
            unit["prerequisite_unit_ids"],
            best_scores,
        ),
        "problems": [
            {
                "problem_id": problem["problem_id"],
                "title": problem["title"],
                "best_score": cast(
                    "int | None",
                    problem_history.get(problem["problem_id"], {}).get("best_score"),
                ),
                "last_attempted_at": cast(
                    "str | None",
                    problem_history.get(problem["problem_id"], {}).get("last_attempted_at"),
                ),
            }
            for problem in unit["problem_bank"]
        ],
    }


@router.get("/sessions")
def list_sessions(request: Request) -> dict[str, object]:
    c = _container(request)
    items = []
    for session in c.algorithm_foundation_store.list_recent_sessions(limit=50):
        details = c.algorithm_foundation_store.get_session_details(session.id)
        answer = c.algorithm_foundation_store.find_answer_by_session(session.id)
        items.append(
            {
                "session_id": session.id,
                "unit_id": session.unit_id,
                "group_id": session.group_id,
                "group_title": session.group_title,
                "unit_title": session.unit_title,
                "target_skill": session.target_skill,
                "unit_kind": session.unit_kind,
                "problem_id": session.problem_id,
                "problem_title": _display_problem_title(
                    str(session.problem_title),
                    str(session.unit_title),
                ),
                "programming_language": session.programming_language,
                "status": session.status,
                "created_at": details["completed_at"] or details["created_at"],
                "score": answer.score if answer is not None else 0,
            },
        )
    return {"sessions": items}


@router.post("/sessions", status_code=201)
def start_session(
    request: Request,
    body: _StartSessionRequest | None = None,
) -> dict[str, object]:
    c = _container(request)
    best_scores, _last_attempted_at = _history_maps(c)
    unit_id = body.unit_id if body is not None else None
    problem_id = body.problem_id if body is not None else None
    programming_language = _resolve_programming_language(body)
    unit, problem = _load_unit_and_problem(
        c,
        unit_id=unit_id,
        problem_id=problem_id,
        best_scores=best_scores,
    )
    reference_solution = _adapt_reference_solution(
        c,
        problem=problem,
        programming_language=programming_language,
    )
    session_id = str(uuid.uuid4())
    c.algorithm_foundation_store.create_session(
        session_id=session_id,
        unit_id=unit["unit_id"],
        group_id=unit["group_id"],
        group_title=unit["group_title"],
        unit_title=unit["title"],
        target_skill=unit["target_skill"],
        unit_kind=unit["unit_kind"],
        prerequisite_unit_ids=unit["prerequisite_unit_ids"],
        prerequisite_titles=unit["prerequisite_titles"],
        allowed_knowledge=unit["allowed_knowledge"],
        forbidden_knowledge=unit["forbidden_knowledge"],
        programming_language=programming_language,
        problem_id=problem["problem_id"],
        problem_title=problem["title"],
        problem_statement=problem["problem_statement"],
        input_format=problem["input_format"],
        output_format=problem["output_format"],
        constraints=problem["constraints"],
        examples=cast("list[dict[str, str]]", problem["examples"]),
        reference_solution=reference_solution,
        grading_rubric=cast("list[dict[str, object]]", problem["grading_rubric"]),
    )
    return {
        "session_id": session_id,
        "unit_id": unit["unit_id"],
        "group_id": unit["group_id"],
        "group_title": unit["group_title"],
        "unit_title": unit["title"],
        "target_skill": unit["target_skill"],
        "unit_kind": unit["unit_kind"],
        "prerequisite_unit_ids": unit["prerequisite_unit_ids"],
        "prerequisite_titles": unit["prerequisite_titles"],
        "allowed_knowledge": unit["allowed_knowledge"],
        "forbidden_knowledge": unit["forbidden_knowledge"],
        "problem_id": problem["problem_id"],
        "problem_title": problem["title"],
        "programming_language": programming_language,
        "problem_statement": problem["problem_statement"],
        "input_format": problem["input_format"],
        "output_format": problem["output_format"],
        "constraints": problem["constraints"],
        "examples": problem["examples"],
        "recommended": unit["unit_id"] == c.algorithm_foundation_catalog.pick_recommended_unit_id(best_scores),
        "has_unmet_prerequisites": _has_unmet_prerequisites(
            unit["prerequisite_unit_ids"],
            best_scores,
        ),
    }


@router.get("/sessions/{session_id}")
def get_session(session_id: str, request: Request) -> dict[str, object]:
    c = _container(request)
    best_scores, _last_attempted_at = _history_maps(c)
    try:
        details = c.algorithm_foundation_store.get_session_details(session_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    concept_overview = _concept_overview(
        c,
        unit_id=cast("str", details["unit_id"]),
        fallback_title=cast("str", details["unit_title"]),
    )
    response = {
        "session_id": details["session_id"],
        "unit_id": details["unit_id"],
        "group_id": details["group_id"],
        "group_title": details["group_title"],
        "unit_title": details["unit_title"],
        "target_skill": details["target_skill"],
        "unit_kind": details["unit_kind"],
        "problem_id": details["problem_id"],
        "problem_title": _display_problem_title(
            cast("str", details["problem_title"]),
            cast("str", details["unit_title"]),
        ),
        "programming_language": details["programming_language"],
        "problem_statement": _display_problem_statement(
            cast("str", details["problem_statement"]),
            concept_overview=concept_overview,
        ),
        "input_format": details["input_format"],
        "output_format": details["output_format"],
        "constraints": details["constraints"],
        "examples": details["examples"],
        "prerequisite_unit_ids": details["prerequisite_unit_ids"],
        "prerequisite_titles": details["prerequisite_titles"],
        "allowed_knowledge": details["allowed_knowledge"],
        "forbidden_knowledge": details["forbidden_knowledge"],
        "status": details["status"],
        "created_at": details["created_at"],
        "recommended": details["unit_id"] == c.algorithm_foundation_catalog.pick_recommended_unit_id(best_scores),
        "has_unmet_prerequisites": _has_unmet_prerequisites(
            cast("list[str]", details["prerequisite_unit_ids"]),
            best_scores,
        ),
    }
    answer = c.algorithm_foundation_store.find_answer_by_session(session_id)
    if answer is not None:
        response.update(
            {
                "score": answer.score,
                "feedback": answer.feedback,
                "time_complexity": answer.time_complexity,
                "space_complexity": answer.space_complexity,
                "improvement_suggestions": answer.improvement_suggestions,
                "rubric_scores_json": answer.rubric_scores_json,
                "reference_solution": details["reference_solution"],
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
        details = c.algorithm_foundation_store.get_session_details(session_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    if c.algorithm_foundation_store.find_answer_by_session(session_id) is not None:
        raise HTTPException(status_code=409, detail="answer already submitted")

    try:
        result = c.algorithm_foundation_solution_evaluator.evaluate_solution(
            problem_statement=cast("str", details["problem_statement"]),
            input_format=cast("str", details["input_format"]),
            output_format=cast("str", details["output_format"]),
            constraints=cast("str", details["constraints"]),
            examples=cast("list[dict[str, str]]", details["examples"]),
            reference_solution=cast("str", details["reference_solution"]),
            grading_rubric=cast("list[dict[str, object]]", details["grading_rubric"]),
            user_code=body.user_code,
            programming_language=cast("str", details["programming_language"]),
            allowed_knowledge=cast("list[str]", details["allowed_knowledge"]),
            forbidden_knowledge=cast("list[str]", details["forbidden_knowledge"]),
        )
    except SolutionEvaluationError as exc:
        raise _evaluation_error_to_http(exc) from exc

    try:
        answer = c.algorithm_foundation_store.save_answer_and_complete(
            session_id=session_id,
            answer_text=body.user_code,
            score=result.score,
            feedback=result.feedback,
            time_complexity=result.time_complexity,
            space_complexity=result.space_complexity,
            improvement_suggestions=result.improvement_suggestions,
            rubric_scores_json=json_dumps(result.rubric_scores),
        )
    except IntegrityError as exc:
        raise HTTPException(status_code=409, detail="answer already submitted") from exc
    return _answer_response(answer, cast("str", details["reference_solution"]))


def _answer_response(
    answer: Any,
    reference_solution: str,
) -> dict[str, object]:
    return {
        "session_id": answer.session_id,
        "score": answer.score,
        "feedback": answer.feedback,
        "time_complexity": answer.time_complexity,
        "space_complexity": answer.space_complexity,
        "improvement_suggestions": answer.improvement_suggestions,
        "rubric_scores_json": answer.rubric_scores_json,
        "reference_solution": reference_solution,
    }


def json_dumps(value: object) -> str:
    import json

    return json.dumps(value, ensure_ascii=False)


__all__ = ["router"]
