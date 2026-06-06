"""quiz セッションの開始・再開・完了を束ねる。"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from inspect import Parameter, Signature
from typing import Any, Protocol, TypedDict, Unpack, cast

import structlog
from langgraph.errors import InvalidUpdateError

from quiz.application.graph import TransientLlmNodeError
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
_RESUME_TRANSIENT_LLM_EVENT = "quiz_session_resume_transient_llm_error"
_START_CLEANUP_FAILED_ERROR_CODE = "session_start_cleanup_failed"
_START_PERSISTENCE_FAILED_ERROR_CODE = "session_start_persistence_failed"
_RESUME_HISTORY_LOAD_FAILED_ERROR_CODE = "session_resume_history_load_failed"
_RESUME_LLM_START_FAILED_ERROR_CODE = "session_resume_llm_start_failed"
_RESUME_TRANSIENT_LLM_ERROR_CODE = "session_resume_transient_llm_error"
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


class _SessionSourceLike(Protocol):
    id: str
    roadmap_item_id: str


@dataclass(frozen=True)
class _RoadmapItemStateSource:
    id: str
    level: RoadmapItemLevel
    title: str
    description: str


@dataclass(frozen=True)
class _ResumeSessionContext:
    session: _SessionSourceLike
    roadmap_item: _RoadmapItemStateSource


def start_session(
    input: StartSessionInput,  # noqa: A002
    **dependency_arguments: Unpack[_StartSessionDependencyArguments],
) -> StartSessionResult:
    """新規セッションを開始する。

    同じ roadmap item に in_progress セッションがあれば新規作成せず、
    既存セッションの再開を促す。重複開始を避けることで、
    graph 側の checkpointer と DB の履歴が食い違いにくくなる。
    """
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
    """回答を QuizAnswer に永続化する。"""
    answer_store.save_answer(session_id, answer)


def complete_session(
    session_id: str,
    score: int,
    *,
    session_store: QuizSessionStore,
) -> None:
    """セッションを完了し score を反映する。"""
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
    """in_progress セッションを QuizAnswer 履歴から再開する。"""
    dependencies = _ResumeSessionDependencies(
        session_store=dependency_arguments["session_store"],
        answer_store=dependency_arguments["answer_store"],
        item_reader=dependency_arguments["item_reader"],
        graph_runner=dependency_arguments["graph_runner"],
    )

    context = _load_resume_session_context(input.session_id, dependencies)
    # 履歴ロード自体は graph に渡さないが、再開前に失敗させることで
    # 「DB では回答履歴が壊れているのに graph だけ進む」状態を防ぐ。
    _load_answer_history_or_raise(context, dependencies.answer_store)

    _resume_graph_or_raise(
        dependencies.graph_runner,
        _build_resume_graph_input(input),
        session_id=context.session.id,
        roadmap_item_id=context.roadmap_item.id,
    )

    return dependencies.graph_runner.get_state(thread_id=context.session.id)


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
    """graph 開始に必要な最小状態を組み立てる。"""
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
    """セッション開始・再開エラーの文言に共通の文脈を付ける。"""
    context = [f"roadmap_item_id={roadmap_item_id}"]
    if session_id is not None:
        context.insert(0, f"session_id={session_id}")
    return f"{base_message}: {', '.join(context)}"


def _to_answer_record(answer: QuizAnswerRecordLike) -> QuizAnswerRecord:
    """store 返却値を graph 側の回答履歴形式へそろえる。"""
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
    """保存済み回答型を graph が理解する Literal へ変換する。"""
    if answer_type in _QUIZ_ANSWER_TYPE_VALUES:
        return cast("QuizAnswerType", answer_type)
    message = f"invalid quiz answer type: {answer_type}"
    raise ValueError(message)


def _to_roadmap_item_state_source(roadmap_item: object) -> _RoadmapItemStateSource:
    """reader の返却値から graph 開始に必要な項目だけを抜き出す。"""
    source = cast("_RoadmapItemSourceLike", roadmap_item)
    return _RoadmapItemStateSource(
        id=source.id,
        level=source.level,
        title=source.title,
        description=source.description,
    )


def _to_session_source(session: object) -> _SessionSourceLike:
    """store の返却値を最小限の Protocol へ狭める。"""
    return cast("_SessionSourceLike", session)


def _load_resume_session_context(
    session_id: str,
    dependencies: _ResumeSessionDependencies,
) -> _ResumeSessionContext:
    """再開に必要な session と roadmap item をまとめて取得する。"""
    session = _to_session_source(
        dependencies.session_store.find_session(session_id),
    )
    roadmap_item = _to_roadmap_item_state_source(
        dependencies.item_reader.find_item(session.roadmap_item_id),
    )
    return _ResumeSessionContext(session=session, roadmap_item=roadmap_item)


def _load_answer_history_or_raise(
    context: _ResumeSessionContext,
    answer_store: QuizAnswerStore,
) -> list[QuizAnswerRecord]:
    """回答履歴を読み込み、失敗時は lifecycle 用エラーへ変換する。"""
    try:
        return [
            _to_answer_record(answer)
            for answer in answer_store.find_by_session(context.session.id)
        ]
    except Exception as exception:
        logger.exception(
            _RESUME_HISTORY_LOAD_FAILED_EVENT,
            session_id=context.session.id,
            roadmap_item_id=context.roadmap_item.id,
            error_code=_RESUME_HISTORY_LOAD_FAILED_ERROR_CODE,
            error_type=type(exception).__name__,
        )
        raise QuizSessionLifecycleError(
            error_code=_RESUME_HISTORY_LOAD_FAILED_ERROR_CODE,
            message=_format_lifecycle_error_message(
                "quiz session resume history load failed",
                session_id=context.session.id,
                roadmap_item_id=context.roadmap_item.id,
            ),
        ) from exception


def _build_resume_graph_input(input: ResumeSessionInput) -> dict[str, object]:  # noqa: A002
    """resume_graph に渡す payload を組み立てる。"""
    return {
        "user_input": input.user_input,
        "input_source": input.input_source,
        "is_resumed": True,
    }


def _start_session_graph_or_raise(
    *,
    session: object,
    roadmap_item_id: str,
    item_reader: RoadmapItemReader,
    dependencies: _StartGraphDependencies,
) -> None:
    """新規セッション作成後に graph を開始し、失敗時は DB を巻き戻す。"""
    session_source = _to_session_source(session)
    try:
        roadmap_item = _to_roadmap_item_state_source(
            item_reader.find_item(session_source.roadmap_item_id),
        )
        state = _build_session_state(
            session_id=session_source.id,
            roadmap_item=roadmap_item,
            is_resumed=False,
        )
        dependencies.graph_runner.start_graph(state, thread_id=session_source.id)
    except Exception as exception:
        # graph 開始失敗後に空の in_progress セッションだけ残すと、
        # 次回開始時に誤って「再開可能」と判定されるため必ず cleanup する。
        try:
            dependencies.session_store.discard_session(session_source.id)
        except Exception as cleanup_exception:
            logger.exception(
                _START_GRAPH_CLEANUP_FAILED_EVENT,
                session_id=session_source.id,
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
                    session_id=session_source.id,
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
                session_id=session_source.id,
                roadmap_item_id=roadmap_item_id,
            ),
        ) from exception


def _resume_graph_or_raise(
    graph_runner: GraphRunner,
    user_input: dict[str, object],
    *,
    session_id: str,
    roadmap_item_id: str,
) -> None:
    """resume_graph を試み、一過性エラーや interrupt 消化済みの場合を処理する。"""
    try:
        graph_runner.resume_graph(user_input, thread_id=session_id)
    except TransientLlmNodeError as exc:
        _raise_transient_resume_error(
            exc,
            session_id=session_id,
            roadmap_item_id=roadmap_item_id,
        )
    except InvalidUpdateError:
        # interrupt がすでに消化済みのときは resume ではなく retry が正しい。
        # ここで retry に寄せると、一過性 LLM エラー後の再試行と
        # 同じ復旧経路にまとめられる。
        _retry_graph_or_raise(
            graph_runner,
            session_id=session_id,
            roadmap_item_id=roadmap_item_id,
        )
    except Exception as exception:  # noqa: BLE001
        _raise_resume_llm_start_error(
            exception,
            session_id=session_id,
            roadmap_item_id=roadmap_item_id,
        )


def _retry_graph_or_raise(
    graph_runner: GraphRunner,
    *,
    session_id: str,
    roadmap_item_id: str,
) -> None:
    """前回一過性エラーで中断したグラフを再実行する。"""
    try:
        graph_runner.retry_graph(thread_id=session_id)
    except TransientLlmNodeError as exc:
        _raise_transient_resume_error(
            exc,
            session_id=session_id,
            roadmap_item_id=roadmap_item_id,
        )
    except Exception as exception:  # noqa: BLE001
        _raise_resume_llm_start_error(
            exception,
            session_id=session_id,
            roadmap_item_id=roadmap_item_id,
        )


def _raise_transient_resume_error(
    exception: TransientLlmNodeError,
    *,
    session_id: str,
    roadmap_item_id: str,
) -> None:
    """再試行可能な LLM 失敗を lifecycle 用エラーへ変換する。"""
    logger.warning(
        _RESUME_TRANSIENT_LLM_EVENT,
        session_id=session_id,
        roadmap_item_id=roadmap_item_id,
        error_type=type(exception.node_error).__name__,
    )
    raise QuizSessionLifecycleError(
        error_code=_RESUME_TRANSIENT_LLM_ERROR_CODE,
        message=_format_lifecycle_error_message(
            "quiz session resume transient llm error",
            session_id=session_id,
            roadmap_item_id=roadmap_item_id,
        ),
    ) from exception


def _raise_resume_llm_start_error(
    exception: Exception,
    *,
    session_id: str,
    roadmap_item_id: str,
) -> None:
    """再開失敗を lifecycle 用エラーへ変換する。"""
    logger.exception(
        _RESUME_LLM_START_FAILED_EVENT,
        session_id=session_id,
        roadmap_item_id=roadmap_item_id,
        error_code=_RESUME_LLM_START_FAILED_ERROR_CODE,
        error_type=type(exception).__name__,
    )
    raise QuizSessionLifecycleError(
        error_code=_RESUME_LLM_START_FAILED_ERROR_CODE,
        message=_format_lifecycle_error_message(
            "quiz session resume llm start failed",
            session_id=session_id,
            roadmap_item_id=roadmap_item_id,
        ),
    ) from exception


def _log_start_failure(
    *,
    roadmap_item_id: str,
    error_code: str,
    exception: Exception,
) -> None:
    """開始失敗時の共通ログを出す。"""
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
