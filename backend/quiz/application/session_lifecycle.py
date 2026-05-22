from __future__ import annotations

from datetime import UTC, datetime
from typing import Protocol, cast

import structlog

from quiz.application.session_lifecycle_types import (
    GraphRunner,
    QuizAnswerStore,
    QuizSessionLifecycleError,
    QuizSessionStore,
    ResumeSessionInput,
    RoadmapItemReader,
    StartSessionInput,
    StartSessionResult,
)
from quiz.domain.session_state import QuizAnswerRecord, QuizAnswerType

logger = structlog.get_logger(__name__)

_START_FAILED_EVENT = "quiz_session_start_failed"
_RESUME_HISTORY_LOAD_FAILED_EVENT = "quiz_session_resume_history_load_failed"
_RESUME_LLM_START_FAILED_EVENT = "quiz_session_resume_llm_start_failed"


class QuizAnswerRecordLike(Protocol):
    question_number: int
    question_text: str
    answer_text: str
    answer_type: str
    score: int
    feedback: str
    confirmation_point_id: str


def start_session(
    input: StartSessionInput,
    *,
    session_store: QuizSessionStore,
    item_reader: RoadmapItemReader,
    graph_runner: GraphRunner,
) -> StartSessionResult:
    existing_session = session_store.find_in_progress_by_item(input.roadmap_item_id)
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
            error_code="session_start_persistence_failed",
            exception=exception,
        )
        raise QuizSessionLifecycleError(
            error_code="session_start_persistence_failed",
            message="quiz session start persistence failed",
        ) from exception

    roadmap_item = item_reader.find_item(session.roadmap_item_id)
    state: dict[str, object] = {
        "session_id": session.id,
        "roadmap_item_id": roadmap_item.id,
        "roadmap_item_level": roadmap_item.level,
        "roadmap_item_title": roadmap_item.title,
        "roadmap_item_description": roadmap_item.description,
        "is_resumed": False,
    }
    try:
        graph_runner.start_graph(state)
    except Exception as exception:
        session_store.delete_session(session.id)
        _log_start_failure(
            roadmap_item_id=input.roadmap_item_id,
            error_code="session_start_graph_failed",
            exception=exception,
        )
        raise QuizSessionLifecycleError(
            error_code="session_start_graph_failed",
            message="quiz session start graph failed",
        ) from exception

    return StartSessionResult(
        session_id=session.id,
        resume_required=False,
        resume_session_id=None,
    )


def record_answer(
    session_id: str,
    answer: object,
    *,
    answer_store: QuizAnswerStore,
) -> None:
    answer_store.save_answer(session_id, answer)


def complete_session(
    session_id: str,
    score: int,
    *,
    session_store: QuizSessionStore,
    item_reader: RoadmapItemReader,
) -> None:
    session = session_store.find_session(session_id)
    item_reader.update_score(session.roadmap_item_id, score)
    session_store.mark_completed(session.id, datetime.now(UTC).isoformat())


def resume_session(
    input: ResumeSessionInput,
    *,
    session_store: QuizSessionStore,
    answer_store: QuizAnswerStore,
    item_reader: RoadmapItemReader,
    graph_runner: GraphRunner,
) -> dict[str, object]:
    session = session_store.find_session(input.session_id)
    roadmap_item = item_reader.find_item(session.roadmap_item_id)

    try:
        answers = answer_store.find_by_session(session.id)
    except Exception as exception:
        logger.exception(
            _RESUME_HISTORY_LOAD_FAILED_EVENT,
            session_id=session.id,
            roadmap_item_id=roadmap_item.id,
            error_code="session_resume_history_load_failed",
            error_type=type(exception).__name__,
        )
        raise QuizSessionLifecycleError(
            error_code="session_resume_history_load_failed",
            message="quiz session resume history load failed",
        ) from exception

    state: dict[str, object] = {
        "session_id": session.id,
        "roadmap_item_id": roadmap_item.id,
        "roadmap_item_level": roadmap_item.level,
        "roadmap_item_title": roadmap_item.title,
        "roadmap_item_description": roadmap_item.description,
        "is_resumed": True,
        "answers": [_to_answer_record(answer) for answer in answers],
    }
    try:
        graph_runner.resume_graph(state)
    except Exception as exception:
        logger.exception(
            _RESUME_LLM_START_FAILED_EVENT,
            session_id=session.id,
            roadmap_item_id=roadmap_item.id,
            error_code="session_resume_llm_start_failed",
            error_type=type(exception).__name__,
        )
        raise QuizSessionLifecycleError(
            error_code="session_resume_llm_start_failed",
            message="quiz session resume llm start failed",
        ) from exception

    return state


def _to_answer_record(answer: object) -> QuizAnswerRecord:
    answer_record = cast("QuizAnswerRecordLike", answer)
    return {
        "question_number": answer_record.question_number,
        "question_text": answer_record.question_text,
        "answer_text": answer_record.answer_text,
        "answer_type": cast("QuizAnswerType", answer_record.answer_type),
        "score": answer_record.score,
        "feedback": answer_record.feedback,
        "confirmation_point_id": answer_record.confirmation_point_id,
    }


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
