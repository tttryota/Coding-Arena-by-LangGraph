from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from inspect import Parameter, Signature
from typing import Any, Protocol, TypedDict, Unpack, cast

import structlog

from quiz.application.session_lifecycle_types import (
    GraphRunner,
    QuizAnswerRecordLike,
    QuizAnswerStore,
    QuizSessionLifecycleError,
    QuizSessionStore,
    ResumeSessionInput,
    RoadmapItemLevel,
    RoadmapItemReader,
    StartSessionInput,
    StartSessionResult,
)
from quiz.domain.session_state import QuizAnswerRecord, QuizAnswerType, SessionState

logger = structlog.get_logger(__name__)

_START_FAILED_EVENT = "quiz_session_start_failed"
_START_GRAPH_CLEANUP_FAILED_EVENT = "quiz_session_start_cleanup_failed"
_RESUME_HISTORY_LOAD_FAILED_EVENT = "quiz_session_resume_history_load_failed"
_RESUME_LLM_START_FAILED_EVENT = "quiz_session_resume_llm_start_failed"
_START_CLEANUP_FAILED_ERROR_CODE = "session_start_cleanup_failed"
_START_PERSISTENCE_FAILED_ERROR_CODE = "session_start_persistence_failed"
_RESUME_HISTORY_LOAD_FAILED_ERROR_CODE = "session_resume_history_load_failed"
_RESUME_LLM_START_FAILED_ERROR_CODE = "session_resume_llm_start_failed"
_START_GRAPH_FAILED_ERROR_CODE = "session_start_graph_failed"
_QUIZ_ANSWER_TYPE_VALUES = ("textarea", "code")


class _StartSessionDependencyArguments(TypedDict):
    session_store: QuizSessionStore
    item_reader: RoadmapItemReader
    graph_runner: GraphRunner


class _ResumeSessionDependencyArguments(TypedDict):
    session_store: QuizSessionStore
    answer_store: QuizAnswerStore
    item_reader: RoadmapItemReader
    graph_runner: GraphRunner


@dataclass(frozen=True)
class _StartGraphDependencies:
    session_store: QuizSessionStore
    graph_runner: GraphRunner


@dataclass(frozen=True)
class _ResumeSessionDependencies:
    session_store: QuizSessionStore
    answer_store: QuizAnswerStore
    item_reader: RoadmapItemReader
    graph_runner: GraphRunner


class _RoadmapItemSourceLike(Protocol):
    id: str
    level: RoadmapItemLevel
    title: str
    description: str


@dataclass(frozen=True)
class _RoadmapItemStateSource:
    id: str
    level: RoadmapItemLevel
    title: str
    description: str


def start_session(
    input: StartSessionInput,  # noqa: A002
    **dependency_arguments: Unpack[_StartSessionDependencyArguments],
) -> StartSessionResult:
    session_store = dependency_arguments["session_store"]
    item_reader = dependency_arguments["item_reader"]
    graph_runner = dependency_arguments["graph_runner"]

    existing_session = session_store.find_in_progress_by_item(
        input.roadmap_item_id,
    )
    if existing_session is not None:
        return StartSessionResult(
            session_id=existing_session.id,
            resume_required=True,
            resume_session_id=existing_session.id,
        )

    try:
        session = session_store.create_session(input.roadmap_item_id)
    except Exception as exception:
        _log_start_failure(
            roadmap_item_id=input.roadmap_item_id,
            error_code=_START_PERSISTENCE_FAILED_ERROR_CODE,
            exception=exception,
        )
        raise QuizSessionLifecycleError(
            error_code=_START_PERSISTENCE_FAILED_ERROR_CODE,
            message=_format_lifecycle_error_message(
                "quiz session start persistence failed",
                roadmap_item_id=input.roadmap_item_id,
            ),
        ) from exception

    _start_session_graph_or_raise(
        session=session,
        roadmap_item_id=input.roadmap_item_id,
        item_reader=item_reader,
        dependencies=_StartGraphDependencies(
            session_store=session_store,
            graph_runner=graph_runner,
        ),
    )

    return StartSessionResult(
        session_id=session.id,
        resume_required=False,
        resume_session_id=None,
    )


def record_answer(
    session_id: str,
    answer: QuizAnswerRecordLike,
    *,
    answer_store: QuizAnswerStore,
) -> None:
    answer_store.save_answer(session_id, answer)


def complete_session(
    session_id: str,
    score: int,
    *,
    session_store: QuizSessionStore,
) -> None:
    session = session_store.find_session(session_id)
    session_store.complete_session(
        session.id,
        session.roadmap_item_id,
        score,
        datetime.now(UTC).isoformat(),
    )


def resume_session(
    input: ResumeSessionInput,  # noqa: A002
    **dependency_arguments: Unpack[_ResumeSessionDependencyArguments],
) -> SessionState:
    dependencies = _ResumeSessionDependencies(
        session_store=dependency_arguments["session_store"],
        answer_store=dependency_arguments["answer_store"],
        item_reader=dependency_arguments["item_reader"],
        graph_runner=dependency_arguments["graph_runner"],
    )

    session = dependencies.session_store.find_session(input.session_id)
    roadmap_item: _RoadmapItemStateSource = _to_roadmap_item_state_source(
        dependencies.item_reader.find_item(session.roadmap_item_id),
    )

    try:
        answers = [
            _to_answer_record(answer)
            for answer in dependencies.answer_store.find_by_session(session.id)
        ]
    except Exception as exception:
        logger.exception(
            _RESUME_HISTORY_LOAD_FAILED_EVENT,
            session_id=session.id,
            roadmap_item_id=roadmap_item.id,
            error_code=_RESUME_HISTORY_LOAD_FAILED_ERROR_CODE,
            error_type=type(exception).__name__,
        )
        raise QuizSessionLifecycleError(
            error_code=_RESUME_HISTORY_LOAD_FAILED_ERROR_CODE,
            message=_format_lifecycle_error_message(
                "quiz session resume history load failed",
                session_id=session.id,
                roadmap_item_id=roadmap_item.id,
            ),
        ) from exception

    state = _build_session_state(
        session_id=session.id,
        roadmap_item=roadmap_item,
        is_resumed=True,
        answers=answers,
    )
    try:
        dependencies.graph_runner.resume_graph(state)
    except Exception as exception:
        logger.exception(
            _RESUME_LLM_START_FAILED_EVENT,
            session_id=session.id,
            roadmap_item_id=roadmap_item.id,
            error_code=_RESUME_LLM_START_FAILED_ERROR_CODE,
            error_type=type(exception).__name__,
        )
        raise QuizSessionLifecycleError(
            error_code=_RESUME_LLM_START_FAILED_ERROR_CODE,
            message=_format_lifecycle_error_message(
                "quiz session resume llm start failed",
                session_id=session.id,
                roadmap_item_id=roadmap_item.id,
            ),
        ) from exception

    return state


cast("Any", start_session).__signature__ = Signature(
    parameters=[
        Parameter(
            "input",
            kind=Parameter.POSITIONAL_OR_KEYWORD,
            annotation=StartSessionInput,
        ),
        Parameter(
            "session_store",
            kind=Parameter.KEYWORD_ONLY,
            annotation=QuizSessionStore,
        ),
        Parameter(
            "item_reader",
            kind=Parameter.KEYWORD_ONLY,
            annotation=RoadmapItemReader,
        ),
        Parameter(
            "graph_runner",
            kind=Parameter.KEYWORD_ONLY,
            annotation=GraphRunner,
        ),
    ],
    return_annotation=StartSessionResult,
)

cast("Any", resume_session).__signature__ = Signature(
    parameters=[
        Parameter(
            "input",
            kind=Parameter.POSITIONAL_OR_KEYWORD,
            annotation=ResumeSessionInput,
        ),
        Parameter(
            "session_store",
            kind=Parameter.KEYWORD_ONLY,
            annotation=QuizSessionStore,
        ),
        Parameter(
            "answer_store",
            kind=Parameter.KEYWORD_ONLY,
            annotation=QuizAnswerStore,
        ),
        Parameter(
            "item_reader",
            kind=Parameter.KEYWORD_ONLY,
            annotation=RoadmapItemReader,
        ),
        Parameter(
            "graph_runner",
            kind=Parameter.KEYWORD_ONLY,
            annotation=GraphRunner,
        ),
    ],
    return_annotation=SessionState,
)


def _build_session_state(
    *,
    session_id: str,
    roadmap_item: _RoadmapItemStateSource,
    is_resumed: bool,
    answers: list[QuizAnswerRecord] | None = None,
) -> SessionState:
    state: SessionState = {
        "session_id": session_id,
        "roadmap_item_id": roadmap_item.id,
        "roadmap_item_level": roadmap_item.level,
        "roadmap_item_title": roadmap_item.title,
        "roadmap_item_description": roadmap_item.description,
        "is_resumed": is_resumed,
    }
    if answers is not None:
        state["answers"] = answers
    return state


def _format_lifecycle_error_message(
    base_message: str,
    *,
    roadmap_item_id: str,
    session_id: str | None = None,
) -> str:
    context = [f"roadmap_item_id={roadmap_item_id}"]
    if session_id is not None:
        context.insert(0, f"session_id={session_id}")
    return f"{base_message}: {', '.join(context)}"


def _to_answer_record(answer: QuizAnswerRecordLike) -> QuizAnswerRecord:
    return {
        "question_number": answer.question_number,
        "question_text": answer.question_text,
        "answer_text": answer.answer_text,
        "answer_type": _to_quiz_answer_type(answer.answer_type),
        "score": answer.score,
        "feedback": answer.feedback,
        "confirmation_point_id": answer.confirmation_point_id,
    }


def _to_quiz_answer_type(answer_type: str) -> QuizAnswerType:
    if answer_type in _QUIZ_ANSWER_TYPE_VALUES:
        return cast("QuizAnswerType", answer_type)
    message = f"invalid quiz answer type: {answer_type}"
    raise ValueError(message)


def _to_roadmap_item_state_source(roadmap_item: object) -> _RoadmapItemStateSource:
    source = cast("_RoadmapItemSourceLike", roadmap_item)
    return _RoadmapItemStateSource(
        id=source.id,
        level=source.level,
        title=source.title,
        description=source.description,
    )


def _start_session_graph_or_raise(
    *,
    session: object,
    roadmap_item_id: str,
    item_reader: RoadmapItemReader,
    dependencies: _StartGraphDependencies,
) -> None:
    try:
        source = cast("Any", session)
        roadmap_item = _to_roadmap_item_state_source(
            item_reader.find_item(source.roadmap_item_id),
        )
        state = _build_session_state(
            session_id=source.id,
            roadmap_item=roadmap_item,
            is_resumed=False,
        )
        dependencies.graph_runner.start_graph(state)
    except Exception as exception:
        try:
            dependencies.session_store.discard_session(cast("Any", session).id)
        except Exception as cleanup_exception:
            logger.exception(
                _START_GRAPH_CLEANUP_FAILED_EVENT,
                session_id=cast("Any", session).id,
                roadmap_item_id=roadmap_item_id,
                error_code=_START_CLEANUP_FAILED_ERROR_CODE,
                start_error_type=type(exception).__name__,
                start_error_message=str(exception),
                cleanup_error_type=type(cleanup_exception).__name__,
            )
            raise QuizSessionLifecycleError(
                error_code=_START_CLEANUP_FAILED_ERROR_CODE,
                message=_format_lifecycle_error_message(
                    "quiz session start cleanup failed",
                    session_id=cast("Any", session).id,
                    roadmap_item_id=roadmap_item_id,
                ),
            ) from cleanup_exception
        _log_start_failure(
            roadmap_item_id=roadmap_item_id,
            error_code=_START_GRAPH_FAILED_ERROR_CODE,
            exception=exception,
        )
        raise QuizSessionLifecycleError(
            error_code=_START_GRAPH_FAILED_ERROR_CODE,
            message=_format_lifecycle_error_message(
                "quiz session start graph failed",
                session_id=cast("Any", session).id,
                roadmap_item_id=roadmap_item_id,
            ),
        ) from exception


def _log_start_failure(
    *,
    roadmap_item_id: str,
    error_code: str,
    exception: Exception,
) -> None:
    logger.exception(
        _START_FAILED_EVENT,
        roadmap_item_id=roadmap_item_id,
        error_code=error_code,
        error_type=type(exception).__name__,
    )


__all__ = [
    "complete_session",
    "record_answer",
    "resume_session",
    "start_session",
]
