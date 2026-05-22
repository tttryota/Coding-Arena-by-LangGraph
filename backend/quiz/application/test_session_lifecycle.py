from __future__ import annotations

from dataclasses import dataclass, replace
from typing import TYPE_CHECKING, Any

import pytest
from structlog.testing import capture_logs

from quiz.application.session_lifecycle import (
    complete_session,
    record_answer,
    resume_session,
    start_session,
)
from quiz.application.session_lifecycle_types import (
    QuizSessionLifecycleError,
    ResumeSessionInput,
    StartSessionInput,
    StartSessionResult,
)
from shared.log_assertions import assert_no_log_event
from shared.log_assertions import assert_single_log_event as _assert_single_log_event

if TYPE_CHECKING:
    from collections.abc import MutableMapping

    from quiz.application.session_lifecycle_types import QuizAnswerRecordLike
    from quiz.domain.session_state import SessionState


_START_FAILED_EVENT = "quiz_session_start_failed"
_START_CLEANUP_FAILED_EVENT = "quiz_session_start_cleanup_failed"
_RESUME_HISTORY_LOAD_FAILED_EVENT = "quiz_session_resume_history_load_failed"
_RESUME_LLM_START_FAILED_EVENT = "quiz_session_resume_llm_start_failed"


@dataclass(frozen=True)
class _SessionRecord:
    id: str
    roadmap_item_id: str
    status: str
    completed_at: str | None
    started_at: str | None = None


@dataclass
class _AnswerHistoryRecord:
    question_number: int
    question_text: str
    answer_text: str
    answer_type: str
    score: int
    feedback: str
    confirmation_point_id: str


@dataclass(frozen=True)
class _RoadmapItemRecord:
    id: str
    level: str
    title: str
    description: str


class _RecordingSessionStore:
    def __init__(
        self,
        *,
        existing_in_progress: dict[str, _SessionRecord] | None = None,
        sessions: dict[str, _SessionRecord] | None = None,
        roadmap_item_scores: dict[str, int] | None = None,
        created_session: _SessionRecord | None = None,
        create_error: Exception | None = None,
        create_error_session: _SessionRecord | None = None,
        rollback_create_error_write: bool = False,
        complete_error: Exception | None = None,
        discard_error: Exception | None = None,
        discard_persists_session: bool = False,
        find_session_error: Exception | None = None,
        operation_log: list[str] | None = None,
    ) -> None:
        self._existing_in_progress = dict(existing_in_progress or {})
        self._sessions = dict(sessions or {})
        self._roadmap_item_scores = dict(roadmap_item_scores or {})
        self._created_session = created_session
        self._create_error = create_error
        self._create_error_session = create_error_session
        self._rollback_create_error_write = rollback_create_error_write
        self._complete_error = complete_error
        self._discard_error = discard_error
        self._discard_persists_session = discard_persists_session
        self._find_session_error = find_session_error
        self._operation_log = operation_log
        self.find_in_progress_by_item_calls: list[str] = []
        self.create_session_calls: list[str] = []
        self.created_sessions: list[_SessionRecord] = []
        self.find_session_calls: list[str] = []
        self.complete_session_calls: list[tuple[str, str, int, str]] = []
        self.discard_session_calls: list[str] = []

    def find_in_progress_by_item(self, roadmap_item_id: str) -> _SessionRecord | None:
        self.find_in_progress_by_item_calls.append(roadmap_item_id)
        if self._operation_log is not None:
            self._operation_log.append("find_in_progress_by_item")
        session = self._existing_in_progress.get(roadmap_item_id)
        if session is None or session.status != "in_progress":
            return None
        return session

    def create_session(self, roadmap_item_id: str) -> _SessionRecord:
        self.create_session_calls.append(roadmap_item_id)
        if self._operation_log is not None:
            self._operation_log.append("create_session")
        if self._create_error is not None:
            if self._create_error_session is not None:
                created_session = replace(
                    self._create_error_session,
                    roadmap_item_id=roadmap_item_id,
                )
                self._sessions[created_session.id] = created_session
                self._existing_in_progress[created_session.roadmap_item_id] = (
                    created_session
                )
                if self._rollback_create_error_write:
                    del self._sessions[created_session.id]
                    del self._existing_in_progress[created_session.roadmap_item_id]
            raise self._create_error
        assert self._created_session is not None
        created_session = replace(
            self._created_session,
            roadmap_item_id=roadmap_item_id,
        )
        self.created_sessions.append(created_session)
        self._sessions[created_session.id] = created_session
        self._existing_in_progress[created_session.roadmap_item_id] = created_session
        return created_session

    def find_session(self, session_id: str) -> _SessionRecord:
        self.find_session_calls.append(session_id)
        if self._operation_log is not None:
            self._operation_log.append("find_session")
        if self._find_session_error is not None:
            raise self._find_session_error
        return self._sessions[session_id]

    def complete_session(
        self,
        session_id: str,
        roadmap_item_id: str,
        score: int,
        completed_at: str,
    ) -> None:
        self.complete_session_calls.append(
            (session_id, roadmap_item_id, score, completed_at),
        )
        if self._operation_log is not None:
            self._operation_log.append("complete_session")
        if self._complete_error is not None:
            raise self._complete_error
        session = self._sessions[session_id]
        completed_session = replace(
            session,
            status="completed",
            completed_at=completed_at,
        )
        self._sessions[session_id] = completed_session
        self._roadmap_item_scores[roadmap_item_id] = score
        if self._existing_in_progress.get(session.roadmap_item_id) is not None:
            self._existing_in_progress[session.roadmap_item_id] = completed_session

    def discard_session(self, session_id: str) -> None:
        self.discard_session_calls.append(session_id)
        if self._operation_log is not None:
            self._operation_log.append("discard_session")
        if self._discard_error is not None:
            raise self._discard_error
        session = self._sessions.get(session_id)
        if session is None:
            return
        if self._discard_persists_session:
            discarded_session = replace(
                session,
                status="start_failed",
                completed_at=None,
            )
            self._sessions[session_id] = discarded_session
            if self._existing_in_progress.get(session.roadmap_item_id) is not None:
                self._existing_in_progress[session.roadmap_item_id] = discarded_session
            return
        del self._sessions[session_id]
        current_in_progress = self._existing_in_progress.get(session.roadmap_item_id)
        if current_in_progress is not None and current_in_progress.id == session_id:
            del self._existing_in_progress[session.roadmap_item_id]

    def persisted_session(self, session_id: str) -> _SessionRecord | None:
        return self._sessions.get(session_id)

    def score_for_item(self, roadmap_item_id: str) -> int | None:
        return self._roadmap_item_scores.get(roadmap_item_id)


class _RecordingAnswerStore:
    def __init__(
        self,
        *,
        histories: dict[str, list[_AnswerHistoryRecord]] | None = None,
        readable_histories: dict[str, list[_AnswerHistoryRecord]] | None = None,
        publish_on_save: bool = True,
        save_error: Exception | None = None,
        find_error: Exception | None = None,
        operation_log: list[str] | None = None,
    ) -> None:
        self.histories: dict[str, list[QuizAnswerRecordLike]] = {
            session_id: list(records)
            for session_id, records in (histories or {}).items()
        }
        self._readable_histories: dict[str, list[QuizAnswerRecordLike]] = {
            session_id: list(records)
            for session_id, records in (
                readable_histories if readable_histories is not None else self.histories
            ).items()
        }
        self._publish_on_save = publish_on_save
        self._save_error = save_error
        self._find_error = find_error
        self._operation_log = operation_log
        self.save_answer_calls: list[tuple[str, QuizAnswerRecordLike]] = []
        self.find_by_session_calls: list[str] = []

    def save_answer(
        self,
        quiz_session_id: str,
        answer: QuizAnswerRecordLike,
    ) -> None:
        self.save_answer_calls.append((quiz_session_id, answer))
        if self._operation_log is not None:
            self._operation_log.append("save_answer")
        if self._save_error is not None:
            raise self._save_error
        self.histories.setdefault(quiz_session_id, []).append(answer)
        if self._publish_on_save:
            self._readable_histories.setdefault(quiz_session_id, []).append(answer)

    def find_by_session(self, session_id: str) -> list[QuizAnswerRecordLike]:
        self.find_by_session_calls.append(session_id)
        if self._operation_log is not None:
            self._operation_log.append("find_by_session")
        if self._find_error is not None:
            raise self._find_error
        return list(self._readable_histories.get(session_id, []))


class _RecordingItemReader:
    def __init__(
        self,
        *,
        items: dict[str, _RoadmapItemRecord] | None = None,
        find_error: Exception | None = None,
        operation_log: list[str] | None = None,
    ) -> None:
        self._items = dict(items or {})
        self._find_error = find_error
        self._operation_log = operation_log
        self.find_item_calls: list[str] = []

    def find_item(self, item_id: str) -> _RoadmapItemRecord:
        self.find_item_calls.append(item_id)
        if self._operation_log is not None:
            self._operation_log.append("find_item")
        if self._find_error is not None:
            raise self._find_error
        return self._items[item_id]


class _RecordingGraphRunner:
    def __init__(
        self,
        *,
        start_error: Exception | None = None,
        resume_error: Exception | None = None,
        operation_log: list[str] | None = None,
    ) -> None:
        self._start_error = start_error
        self._resume_error = resume_error
        self._operation_log = operation_log
        self.graph_call_sequence: list[str] = []
        self.start_graph_calls: list[dict[str, object]] = []
        self.resume_graph_calls: list[dict[str, object]] = []

    def start_graph(self, state: SessionState) -> None:
        snapshot: dict[str, object] = dict(state)
        self.graph_call_sequence.append("start_graph")
        self.start_graph_calls.append(snapshot)
        if self._operation_log is not None:
            self._operation_log.append("start_graph")
        if self._start_error is not None:
            raise self._start_error

    def resume_graph(self, state: SessionState) -> None:
        snapshot: dict[str, object] = dict(state)
        self.graph_call_sequence.append("resume_graph")
        self.resume_graph_calls.append(snapshot)
        if self._operation_log is not None:
            self._operation_log.append("resume_graph")
        if self._resume_error is not None:
            raise self._resume_error


def _session(
    *,
    session_id: str = "session-001",
    roadmap_item_id: str = "item-001",
    status: str = "in_progress",
    completed_at: str | None = None,
    started_at: str | None = None,
) -> _SessionRecord:
    return _SessionRecord(
        id=session_id,
        roadmap_item_id=roadmap_item_id,
        status=status,
        completed_at=completed_at,
        started_at=started_at,
    )


def _item(
    *,
    item_id: str = "item-001",
    level: str = "detail",
    title: str = "ジェネリクスの基本構文",
    description: str = "型パラメータと制約を扱う",
) -> _RoadmapItemRecord:
    return _RoadmapItemRecord(
        id=item_id,
        level=level,
        title=title,
        description=description,
    )


def _answer(
    *,
    question_number: int,
    question_text: str,
    answer_text: str,
    answer_type: str = "textarea",
    score: int = 0,
    feedback: str = "",
    confirmation_point_id: str = "cp-001",
) -> _AnswerHistoryRecord:
    return _AnswerHistoryRecord(
        question_number=question_number,
        question_text=question_text,
        answer_text=answer_text,
        answer_type=answer_type,
        score=score,
        feedback=feedback,
        confirmation_point_id=confirmation_point_id,
    )


def _expected_answer_state(
    *,
    question_number: int,
    question_text: str,
    answer_text: str,
    answer_type: str = "textarea",
    score: int = 0,
    feedback: str = "",
    confirmation_point_id: str = "cp-001",
) -> dict[str, object]:
    return {
        "question_number": question_number,
        "question_text": question_text,
        "answer_text": answer_text,
        "answer_type": answer_type,
        "score": score,
        "feedback": feedback,
        "confirmation_point_id": confirmation_point_id,
    }


def _assert_single_failure_log(
    log_output: list[MutableMapping[str, Any]],
    *,
    event_name: str,
    expected_fields: dict[str, object],
) -> None:
    assert len(log_output) == 1
    _assert_single_log_event(log_output, event_name, expected_fields)


def test_tc_01_start_session_creates_session_and_starts_graph_with_c1_state() -> None:
    # Arrange
    requested_roadmap_item_id = "item-requested"
    created_session = _session(
        session_id="session-created",
        roadmap_item_id="item-created-default",
    )
    roadmap_item = _item(item_id=requested_roadmap_item_id)
    session_store = _RecordingSessionStore(
        created_session=created_session,
    )
    item_reader = _RecordingItemReader(
        items={roadmap_item.id: roadmap_item},
    )
    graph_runner = _RecordingGraphRunner()
    start_input = StartSessionInput(roadmap_item_id=requested_roadmap_item_id)

    # Act
    result = start_session(
        start_input,
        session_store=session_store,
        item_reader=item_reader,
        graph_runner=graph_runner,
    )

    # Assert
    assert result == StartSessionResult(
        session_id=created_session.id,
        resume_required=False,
        resume_session_id=None,
    )
    expected_state = {
        "session_id": created_session.id,
        "roadmap_item_id": roadmap_item.id,
        "roadmap_item_level": roadmap_item.level,
        "roadmap_item_title": roadmap_item.title,
        "roadmap_item_description": roadmap_item.description,
        "is_resumed": False,
    }
    persisted_session = session_store.persisted_session(created_session.id)
    assert requested_roadmap_item_id in session_store.create_session_calls
    assert session_store.created_sessions == [
        _session(
            session_id="session-created",
            roadmap_item_id=requested_roadmap_item_id,
        ),
    ]
    assert requested_roadmap_item_id in item_reader.find_item_calls
    assert persisted_session is not None
    assert persisted_session.roadmap_item_id == requested_roadmap_item_id
    assert persisted_session.status == "in_progress"
    assert persisted_session.completed_at is None
    assert expected_state in graph_runner.start_graph_calls
    assert session_store.discard_session_calls == []


def test_tc_11_existing_in_progress_returns_resume_target_without_new_session() -> None:
    # Arrange
    existing_session = _session(session_id="session-keep")
    session_store = _RecordingSessionStore(
        existing_in_progress={existing_session.roadmap_item_id: existing_session},
    )
    item_reader = _RecordingItemReader()
    graph_runner = _RecordingGraphRunner()
    start_input = StartSessionInput(roadmap_item_id=existing_session.roadmap_item_id)

    # Act
    result = start_session(
        start_input,
        session_store=session_store,
        item_reader=item_reader,
        graph_runner=graph_runner,
    )

    # Assert
    assert result.resume_required is True
    assert result.resume_session_id == existing_session.id
    assert session_store.find_in_progress_by_item_calls == [
        existing_session.roadmap_item_id,
    ]
    assert session_store.create_session_calls == []
    assert item_reader.find_item_calls == []
    assert graph_runner.start_graph_calls == []
    assert session_store.discard_session_calls == []


def test_tc_02_record_answer_persists_raw_answer_before_returning() -> None:
    # Arrange
    raw_answer = _answer(
        question_number=1,
        question_text="型制約は何のために使いますか。",
        answer_text="  制約\nA extends B  ",
        score=61,
        feedback="raw のまま残す",
    )
    answer_store = _RecordingAnswerStore()

    # Act
    record_answer(
        "session-001",
        raw_answer,
        answer_store=answer_store,
    )

    # Assert
    persisted_answers = answer_store.find_by_session("session-001")
    assert answer_store.save_answer_calls == [("session-001", raw_answer)]
    assert persisted_answers == [raw_answer]
    assert answer_store.find_by_session_calls == ["session-001"]
    saved_answer = persisted_answers[0]
    assert saved_answer.answer_text == "  制約\nA extends B  "


def test_tc_03_complete_session_marks_completed_and_updates_score() -> None:
    # Arrange
    session = _session()
    session_store = _RecordingSessionStore(sessions={session.id: session})

    # Act
    complete_session(
        session.id,
        88,
        session_store=session_store,
    )

    # Assert
    assert len(session_store.complete_session_calls) == 1
    completed_call = session_store.complete_session_calls[0]
    assert completed_call[:3] == (session.id, session.roadmap_item_id, 88)
    assert completed_call[3] != ""
    persisted_session = session_store.persisted_session(session.id)
    assert persisted_session is not None
    assert persisted_session.status == "completed"
    assert persisted_session.completed_at is not None
    assert persisted_session.completed_at != ""
    assert session_store.score_for_item(session.roadmap_item_id) == 88
    assert session_store.discard_session_calls == []


def test_tc_04_complete_session_failure_keeps_session_and_score_consistent() -> None:
    # Arrange
    session = _session(session_id="session-complete-failed")
    original_error = RuntimeError("completion persistence failed")
    session_store = _RecordingSessionStore(
        sessions={session.id: session},
        roadmap_item_scores={session.roadmap_item_id: 41},
        complete_error=original_error,
    )

    # Act / Assert
    with pytest.raises(RuntimeError) as exc_info:
        complete_session(
            session.id,
            88,
            session_store=session_store,
        )

    assert exc_info.value is original_error
    assert len(session_store.complete_session_calls) == 1
    completed_call = session_store.complete_session_calls[0]
    assert completed_call[:3] == (session.id, session.roadmap_item_id, 88)
    persisted_session = session_store.persisted_session(session.id)
    assert persisted_session is not None
    assert persisted_session.status == "in_progress"
    assert persisted_session.completed_at is None
    assert session_store.score_for_item(session.roadmap_item_id) == 41


def test_tc_10_resume_session_rehydrates_ordered_pairs_and_continues_from_question_4() -> (
    None
):
    # Arrange
    session = _session()
    roadmap_item = _item()
    persisted_answers = [
        _answer(
            question_number=1,
            question_text="ジェネリクスは何を解決しますか。",
            answer_text="型安全に共通化できます。",
            score=72,
            feedback="型安全性に触れられています。",
            confirmation_point_id="cp-001",
        ),
        _answer(
            question_number=2,
            question_text="制約付き型パラメータの例を挙げてください。",
            answer_text="T extends HasId のように使います。",
            score=80,
            feedback="具体例が明確です。",
            confirmation_point_id="cp-002",
        ),
        _answer(
            question_number=3,
            question_text="ワイルドカードはいつ使いますか。",
            answer_text="読み取り専用の境界を表したいときに使います。",
            score=84,
            feedback="用途が具体的です。",
            confirmation_point_id="cp-003",
        ),
    ]
    session_store = _RecordingSessionStore(sessions={session.id: session})
    answer_store = _RecordingAnswerStore(
        histories={session.id: persisted_answers},
    )
    item_reader = _RecordingItemReader(
        items={roadmap_item.id: roadmap_item},
    )
    graph_runner = _RecordingGraphRunner()
    resume_input = ResumeSessionInput(session_id=session.id)

    # Act
    state = resume_session(
        resume_input,
        session_store=session_store,
        answer_store=answer_store,
        item_reader=item_reader,
        graph_runner=graph_runner,
    )

    # Assert
    expected_resumed_answers = [
        _expected_answer_state(
            question_number=1,
            question_text="ジェネリクスは何を解決しますか。",
            answer_text="型安全に共通化できます。",
            score=72,
            feedback="型安全性に触れられています。",
            confirmation_point_id="cp-001",
        ),
        _expected_answer_state(
            question_number=2,
            question_text="制約付き型パラメータの例を挙げてください。",
            answer_text="T extends HasId のように使います。",
            score=80,
            feedback="具体例が明確です。",
            confirmation_point_id="cp-002",
        ),
        _expected_answer_state(
            question_number=3,
            question_text="ワイルドカードはいつ使いますか。",
            answer_text="読み取り専用の境界を表したいときに使います。",
            score=84,
            feedback="用途が具体的です。",
            confirmation_point_id="cp-003",
        ),
    ]
    expected_state = {
        "session_id": session.id,
        "roadmap_item_id": roadmap_item.id,
        "roadmap_item_level": roadmap_item.level,
        "roadmap_item_title": roadmap_item.title,
        "roadmap_item_description": roadmap_item.description,
        "is_resumed": True,
        "answers": expected_resumed_answers,
    }
    resumed_question_numbers = [
        answer["question_number"] for answer in state["answers"]
    ]
    expected_next_question_number = 4
    assert state == expected_state
    assert graph_runner.resume_graph_calls == [expected_state]
    assert resumed_question_numbers == [1, 2, 3]
    assert resumed_question_numbers[-1] + 1 == expected_next_question_number
    assert session_store.create_session_calls == []
    assert session_store.complete_session_calls == []
    assert session_store.discard_session_calls == []


def test_tc_30_resume_session_loads_all_persisted_answers_and_passes_them_to_graph() -> (
    None
):
    # Arrange
    session = _session(session_id="session-db-history")
    roadmap_item = _item()
    persisted_answers = [
        _answer(
            question_number=1,
            question_text="ジェネリクスは何を解決しますか。",
            answer_text="型安全に共通化できます。",
            score=72,
            feedback="型安全性に触れられています。",
            confirmation_point_id="cp-001",
        ),
        _answer(
            question_number=2,
            question_text="制約付き型パラメータの例を挙げてください。",
            answer_text="T extends HasId のように使います。",
            score=80,
            feedback="具体例が明確です。",
            confirmation_point_id="cp-002",
        ),
        _answer(
            question_number=3,
            question_text="ワイルドカードはいつ使いますか。",
            answer_text="読み取り専用の境界を表したいときに使います。",
            score=84,
            feedback="用途が具体的です。",
            confirmation_point_id="cp-003",
        ),
    ]
    session_store = _RecordingSessionStore(sessions={session.id: session})
    answer_store = _RecordingAnswerStore(histories={session.id: persisted_answers})
    item_reader = _RecordingItemReader(items={roadmap_item.id: roadmap_item})
    graph_runner = _RecordingGraphRunner()

    # Act
    state = resume_session(
        ResumeSessionInput(session_id=session.id),
        session_store=session_store,
        answer_store=answer_store,
        item_reader=item_reader,
        graph_runner=graph_runner,
    )

    # Assert
    persisted_count = len(persisted_answers)
    expected_resumed_answers = [
        _expected_answer_state(
            question_number=1,
            question_text="ジェネリクスは何を解決しますか。",
            answer_text="型安全に共通化できます。",
            score=72,
            feedback="型安全性に触れられています。",
            confirmation_point_id="cp-001",
        ),
        _expected_answer_state(
            question_number=2,
            question_text="制約付き型パラメータの例を挙げてください。",
            answer_text="T extends HasId のように使います。",
            score=80,
            feedback="具体例が明確です。",
            confirmation_point_id="cp-002",
        ),
        _expected_answer_state(
            question_number=3,
            question_text="ワイルドカードはいつ使いますか。",
            answer_text="読み取り専用の境界を表したいときに使います。",
            score=84,
            feedback="用途が具体的です。",
            confirmation_point_id="cp-003",
        ),
    ]
    assert session.id in answer_store.find_by_session_calls
    assert len(answer_store.histories[session.id]) == persisted_count
    assert isinstance(state["answers"], list)
    assert len(state["answers"]) == persisted_count
    assert state["answers"] == expected_resumed_answers
    assert graph_runner.resume_graph_calls
    assert graph_runner.resume_graph_calls[0]["answers"] == expected_resumed_answers
    assert session_store.create_session_calls == []
    assert session_store.complete_session_calls == []
    assert session_store.discard_session_calls == []


def test_tc_12_resume_session_with_zero_answers_uses_empty_history() -> None:
    # Arrange
    session = _session(session_id="session-empty")
    roadmap_item = _item()
    session_store = _RecordingSessionStore(sessions={session.id: session})
    answer_store = _RecordingAnswerStore(histories={session.id: []})
    item_reader = _RecordingItemReader(items={roadmap_item.id: roadmap_item})
    graph_runner = _RecordingGraphRunner()
    fresh_session = _session(
        session_id="session-fresh",
        roadmap_item_id=roadmap_item.id,
    )
    fresh_session_store = _RecordingSessionStore(created_session=fresh_session)
    fresh_graph_runner = _RecordingGraphRunner()
    resume_input = ResumeSessionInput(session_id=session.id)

    # Act
    state = resume_session(
        resume_input,
        session_store=session_store,
        answer_store=answer_store,
        item_reader=item_reader,
        graph_runner=graph_runner,
    )
    fresh_result = start_session(
        StartSessionInput(roadmap_item_id=roadmap_item.id),
        session_store=fresh_session_store,
        item_reader=_RecordingItemReader(items={roadmap_item.id: roadmap_item}),
        graph_runner=fresh_graph_runner,
    )

    # Assert
    expected_state = {
        "session_id": session.id,
        "roadmap_item_id": roadmap_item.id,
        "roadmap_item_level": roadmap_item.level,
        "roadmap_item_title": roadmap_item.title,
        "roadmap_item_description": roadmap_item.description,
        "is_resumed": True,
        "answers": [],
    }
    expected_fresh_graph_state = {
        "session_id": fresh_session.id,
        "roadmap_item_id": roadmap_item.id,
        "roadmap_item_level": roadmap_item.level,
        "roadmap_item_title": roadmap_item.title,
        "roadmap_item_description": roadmap_item.description,
        "is_resumed": False,
    }
    assert fresh_result.resume_required is False
    assert state == expected_state
    assert graph_runner.resume_graph_calls == [expected_state]
    assert fresh_graph_runner.start_graph_calls == [expected_fresh_graph_state]
    resume_graph_state = graph_runner.resume_graph_calls[0]
    fresh_graph_state = fresh_graph_runner.start_graph_calls[0]
    assert resume_graph_state["answers"] == []
    assert set(resume_graph_state) - set(fresh_graph_state) == {
        "answers",
    }
    comparable_resume_state = {
        key: value
        for key, value in resume_graph_state.items()
        if key not in {"session_id", "is_resumed", "answers"}
    }
    comparable_fresh_state = {
        key: value
        for key, value in fresh_graph_state.items()
        if key not in {"session_id", "is_resumed"}
    }
    assert comparable_resume_state == comparable_fresh_state
    assert session_store.create_session_calls == []
    assert session_store.complete_session_calls == []
    assert session_store.discard_session_calls == []


def test_tc_20_interrupted_in_progress_session_keeps_persisted_state() -> None:
    # Arrange
    session = _session(session_id="session-interrupted")
    roadmap_item = _item(item_id=session.roadmap_item_id)
    session_store = _RecordingSessionStore(
        sessions={session.id: session},
    )
    answer_store = _RecordingAnswerStore()
    item_reader = _RecordingItemReader(items={roadmap_item.id: roadmap_item})
    graph_runner = _RecordingGraphRunner()
    first_answer = _answer(
        question_number=1,
        question_text="1問目",
        answer_text="1つ目の回答",
    )
    second_answer = _answer(
        question_number=2,
        question_text="2問目",
        answer_text="2つ目の回答",
    )

    # Act
    record_answer(session.id, first_answer, answer_store=answer_store)
    record_answer(session.id, second_answer, answer_store=answer_store)
    # 中断イベント自体は module 外の責務であり、この module では中断後の persisted state を観測する。
    persisted_answers = answer_store.find_by_session(session.id)
    resumed_state = resume_session(
        ResumeSessionInput(session_id=session.id),
        session_store=session_store,
        answer_store=answer_store,
        item_reader=item_reader,
        graph_runner=graph_runner,
    )

    # Assert
    persisted_session = session_store.persisted_session(session.id)
    expected_resumed_answers = [
        _expected_answer_state(
            question_number=1,
            question_text="1問目",
            answer_text="1つ目の回答",
        ),
        _expected_answer_state(
            question_number=2,
            question_text="2問目",
            answer_text="2つ目の回答",
        ),
    ]
    assert persisted_session is not None
    assert persisted_session.status == "in_progress"
    assert persisted_session.completed_at is None
    assert persisted_answers == [first_answer, second_answer]
    assert resumed_state["session_id"] == session.id
    assert resumed_state["answers"] == expected_resumed_answers
    assert graph_runner.resume_graph_calls == [
        {
            "session_id": session.id,
            "roadmap_item_id": roadmap_item.id,
            "roadmap_item_level": roadmap_item.level,
            "roadmap_item_title": roadmap_item.title,
            "roadmap_item_description": roadmap_item.description,
            "is_resumed": True,
            "answers": expected_resumed_answers,
        },
    ]
    assert answer_store.save_answer_calls == [
        (session.id, first_answer),
        (session.id, second_answer),
    ]
    assert answer_store.find_by_session_calls == [session.id, session.id]
    assert session_store.find_session_calls == [session.id]
    assert session_store.create_session_calls == []
    assert session_store.complete_session_calls == []
    assert session_store.discard_session_calls == []


def test_tc_21_browser_close_then_explicit_resume_preserves_history_and_continues_from_question_4() -> (
    None
):
    # Arrange
    session = _session(session_id="session-browser-close")
    roadmap_item = _item()
    answers = [
        _answer(question_number=1, question_text="1問目", answer_text="1つ目の回答"),
        _answer(question_number=2, question_text="2問目", answer_text="2つ目の回答"),
        _answer(question_number=3, question_text="3問目", answer_text="3つ目の回答"),
    ]
    session_store = _RecordingSessionStore(
        existing_in_progress={session.roadmap_item_id: session},
        sessions={session.id: session},
    )
    answer_store = _RecordingAnswerStore(histories={session.id: answers})
    item_reader = _RecordingItemReader(items={roadmap_item.id: roadmap_item})
    graph_runner = _RecordingGraphRunner()

    # Act
    start_result = start_session(
        StartSessionInput(roadmap_item_id=session.roadmap_item_id),
        session_store=session_store,
        item_reader=_RecordingItemReader(),
        graph_runner=_RecordingGraphRunner(),
    )
    state = resume_session(
        ResumeSessionInput(session_id=session.id),
        session_store=session_store,
        answer_store=answer_store,
        item_reader=item_reader,
        graph_runner=graph_runner,
    )

    # Assert
    persisted_session = session_store.persisted_session(session.id)
    expected_resumed_answers = [
        _expected_answer_state(
            question_number=1,
            question_text="1問目",
            answer_text="1つ目の回答",
        ),
        _expected_answer_state(
            question_number=2,
            question_text="2問目",
            answer_text="2つ目の回答",
        ),
        _expected_answer_state(
            question_number=3,
            question_text="3問目",
            answer_text="3つ目の回答",
        ),
    ]
    resumed_question_numbers = [
        answer["question_number"] for answer in state["answers"]
    ]
    expected_next_question_number = 4
    assert start_result.resume_required is True
    assert start_result.resume_session_id == session.id
    assert state["session_id"] == session.id
    assert state["answers"] == expected_resumed_answers
    assert resumed_question_numbers == [1, 2, 3]
    assert resumed_question_numbers[-1] + 1 == expected_next_question_number
    assert graph_runner.resume_graph_calls == [
        {
            "session_id": session.id,
            "roadmap_item_id": roadmap_item.id,
            "roadmap_item_level": roadmap_item.level,
            "roadmap_item_title": roadmap_item.title,
            "roadmap_item_description": roadmap_item.description,
            "is_resumed": True,
            "answers": expected_resumed_answers,
        },
    ]
    assert persisted_session is not None
    assert persisted_session.status == "in_progress"
    assert persisted_session.completed_at is None
    assert answer_store.histories[session.id] == answers
    assert session_store.create_session_calls == []
    assert session_store.complete_session_calls == []
    assert session_store.discard_session_calls == []


def test_tc_22_long_idle_in_progress_session_resumes_without_expiry_rejection() -> None:
    # Arrange
    session = _session(
        session_id="session-long-idle",
        started_at="2024-01-01T00:00:00+00:00",
    )
    roadmap_item = _item()
    answers = [
        _answer(
            question_number=1,
            question_text="既存の質問",
            answer_text="既存の回答",
        ),
    ]
    session_store = _RecordingSessionStore(sessions={session.id: session})
    answer_store = _RecordingAnswerStore(histories={session.id: answers})
    item_reader = _RecordingItemReader(items={roadmap_item.id: roadmap_item})
    graph_runner = _RecordingGraphRunner()

    # Act
    state = resume_session(
        ResumeSessionInput(session_id=session.id),
        session_store=session_store,
        answer_store=answer_store,
        item_reader=item_reader,
        graph_runner=graph_runner,
    )

    # Assert
    persisted_session = session_store.persisted_session(session.id)
    expected_resumed_answers = [
        _expected_answer_state(
            question_number=1,
            question_text="既存の質問",
            answer_text="既存の回答",
        ),
    ]
    assert state["session_id"] == session.id
    assert state["answers"] == expected_resumed_answers
    resumed_question_numbers = [
        answer["question_number"] for answer in state["answers"]
    ]
    assert resumed_question_numbers == [1]
    assert resumed_question_numbers[-1] + 1 == 2
    assert graph_runner.resume_graph_calls
    assert graph_runner.resume_graph_calls[0]["answers"] == expected_resumed_answers
    assert persisted_session is not None
    assert persisted_session.status == "in_progress"
    assert persisted_session.completed_at is None
    assert session_store.create_session_calls == []
    assert session_store.complete_session_calls == []
    assert session_store.discard_session_calls == []


def test_tc_31_start_session_create_failure_preserves_atomicity_and_error_contract() -> (
    None
):
    # Arrange
    attempted_session = _session(session_id="session-create-failed")
    original_error = RuntimeError("db unavailable")
    session_store = _RecordingSessionStore(
        create_error=original_error,
        create_error_session=attempted_session,
        rollback_create_error_write=True,
    )
    item_reader = _RecordingItemReader()
    graph_runner = _RecordingGraphRunner()
    start_input = StartSessionInput(roadmap_item_id="item-001")

    # Act / Assert
    with (
        capture_logs() as log_output,
        pytest.raises(QuizSessionLifecycleError) as exc_info,
    ):
        start_session(
            start_input,
            session_store=session_store,
            item_reader=item_reader,
            graph_runner=graph_runner,
        )

    assert exc_info.value.error_code == "session_start_persistence_failed"
    assert (
        exc_info.value.message
        == "quiz session start persistence failed: roadmap_item_id=item-001"
    )
    assert exc_info.value.__cause__ is original_error
    assert session_store.create_session_calls == ["item-001"]
    assert session_store.persisted_session(attempted_session.id) is None
    assert session_store.find_in_progress_by_item("item-001") is None
    assert graph_runner.start_graph_calls == []
    assert session_store.discard_session_calls == []
    _assert_single_failure_log(
        log_output,
        event_name=_START_FAILED_EVENT,
        expected_fields={
            "roadmap_item_id": "item-001",
            "error_code": "session_start_persistence_failed",
            "error_type": "RuntimeError",
        },
    )
    assert_no_log_event(log_output, _RESUME_HISTORY_LOAD_FAILED_EVENT)
    assert_no_log_event(log_output, _RESUME_LLM_START_FAILED_EVENT)


def test_tc_31_start_session_graph_failure_rolls_back_and_raises_contract_error() -> (
    None
):
    # Arrange
    created_session = _session()
    roadmap_item = _item()
    original_error = RuntimeError("graph start failed")
    session_store = _RecordingSessionStore(created_session=created_session)
    item_reader = _RecordingItemReader(items={roadmap_item.id: roadmap_item})
    graph_runner = _RecordingGraphRunner(start_error=original_error)
    start_input = StartSessionInput(roadmap_item_id=roadmap_item.id)

    # Act / Assert
    with (
        capture_logs() as log_output,
        pytest.raises(QuizSessionLifecycleError) as exc_info,
    ):
        start_session(
            start_input,
            session_store=session_store,
            item_reader=item_reader,
            graph_runner=graph_runner,
        )

    assert exc_info.value.error_code == "session_start_graph_failed"
    assert (
        exc_info.value.message
        == "quiz session start graph failed: session_id=session-001, "
        "roadmap_item_id=item-001"
    )
    assert exc_info.value.__cause__ is original_error
    assert session_store.create_session_calls == [roadmap_item.id]
    assert len(graph_runner.start_graph_calls) == 1
    assert session_store.discard_session_calls == [created_session.id]
    assert session_store.persisted_session(created_session.id) is None
    _assert_single_failure_log(
        log_output,
        event_name=_START_FAILED_EVENT,
        expected_fields={
            "roadmap_item_id": roadmap_item.id,
            "error_code": "session_start_graph_failed",
            "error_type": "RuntimeError",
        },
    )


def test_tc_31_start_session_item_load_failure_rolls_back_and_does_not_leave_resume_target() -> (
    None
):
    # Arrange
    created_session = _session(session_id="session-item-load-failed")
    original_error = RuntimeError("roadmap item lookup failed")
    session_store = _RecordingSessionStore(created_session=created_session)
    item_reader = _RecordingItemReader(find_error=original_error)
    graph_runner = _RecordingGraphRunner()
    start_input = StartSessionInput(roadmap_item_id=created_session.roadmap_item_id)

    # Act / Assert
    with (
        capture_logs() as log_output,
        pytest.raises(QuizSessionLifecycleError) as exc_info,
    ):
        start_session(
            start_input,
            session_store=session_store,
            item_reader=item_reader,
            graph_runner=graph_runner,
        )

    assert exc_info.value.error_code == "session_start_graph_failed"
    assert (
        exc_info.value.message == "quiz session start graph failed: "
        "session_id=session-item-load-failed, roadmap_item_id=item-001"
    )
    assert exc_info.value.__cause__ is original_error
    assert session_store.create_session_calls == [created_session.roadmap_item_id]
    assert item_reader.find_item_calls == [created_session.roadmap_item_id]
    assert graph_runner.start_graph_calls == []
    assert session_store.discard_session_calls == [created_session.id]
    assert session_store.persisted_session(created_session.id) is None
    assert (
        session_store.find_in_progress_by_item(created_session.roadmap_item_id) is None
    )
    _assert_single_failure_log(
        log_output,
        event_name=_START_FAILED_EVENT,
        expected_fields={
            "roadmap_item_id": created_session.roadmap_item_id,
            "error_code": "session_start_graph_failed",
            "error_type": "RuntimeError",
        },
    )


def test_tc_31_start_session_graph_failure_keeps_orphan_non_resumable_when_discard_persists_record() -> (
    None
):
    # Arrange
    created_session = _session(session_id="session-discarded-record")
    roadmap_item = _item(item_id=created_session.roadmap_item_id)
    original_error = RuntimeError("graph start failed")
    session_store = _RecordingSessionStore(
        created_session=created_session,
        discard_persists_session=True,
    )
    item_reader = _RecordingItemReader(items={roadmap_item.id: roadmap_item})
    graph_runner = _RecordingGraphRunner(start_error=original_error)

    # Act / Assert
    with (
        capture_logs() as log_output,
        pytest.raises(QuizSessionLifecycleError) as exc_info,
    ):
        start_session(
            StartSessionInput(roadmap_item_id=roadmap_item.id),
            session_store=session_store,
            item_reader=item_reader,
            graph_runner=graph_runner,
        )

    assert exc_info.value.error_code == "session_start_graph_failed"
    assert exc_info.value.__cause__ is original_error
    persisted_session = session_store.persisted_session(created_session.id)
    assert persisted_session is not None
    assert persisted_session.status == "start_failed"
    assert (
        session_store.find_in_progress_by_item(created_session.roadmap_item_id) is None
    )
    assert session_store.discard_session_calls == [created_session.id]
    _assert_single_failure_log(
        log_output,
        event_name=_START_FAILED_EVENT,
        expected_fields={
            "roadmap_item_id": roadmap_item.id,
            "error_code": "session_start_graph_failed",
            "error_type": "RuntimeError",
        },
    )
    assert_no_log_event(log_output, _START_CLEANUP_FAILED_EVENT)


def test_tc_31_start_session_cleanup_failure_raises_dedicated_error_contract() -> None:
    # Arrange
    created_session = _session(session_id="session-cleanup-failed")
    roadmap_item = _item(item_id=created_session.roadmap_item_id)
    start_error = RuntimeError("graph start failed")
    cleanup_error = RuntimeError("discard failed")
    session_store = _RecordingSessionStore(
        created_session=created_session,
        discard_error=cleanup_error,
    )
    item_reader = _RecordingItemReader(items={roadmap_item.id: roadmap_item})
    graph_runner = _RecordingGraphRunner(start_error=start_error)

    # Act / Assert
    with (
        capture_logs() as log_output,
        pytest.raises(QuizSessionLifecycleError) as exc_info,
    ):
        start_session(
            StartSessionInput(roadmap_item_id=roadmap_item.id),
            session_store=session_store,
            item_reader=item_reader,
            graph_runner=graph_runner,
        )

    assert exc_info.value.error_code == "session_start_cleanup_failed"
    assert (
        exc_info.value.message == "quiz session start cleanup failed: "
        "session_id=session-cleanup-failed, roadmap_item_id=item-001"
    )
    assert exc_info.value.__cause__ is cleanup_error
    persisted_session = session_store.persisted_session(created_session.id)
    assert persisted_session is not None
    assert persisted_session.status == "in_progress"
    assert session_store.discard_session_calls == [created_session.id]
    _assert_single_failure_log(
        log_output,
        event_name=_START_CLEANUP_FAILED_EVENT,
        expected_fields={
            "session_id": created_session.id,
            "roadmap_item_id": roadmap_item.id,
            "error_code": "session_start_cleanup_failed",
            "start_error_type": "RuntimeError",
            "start_error_message": "graph start failed",
            "cleanup_error_type": "RuntimeError",
        },
    )
    assert_no_log_event(log_output, _START_FAILED_EVENT)


def test_tc_32_resume_session_history_load_failure_keeps_state_unchanged_and_logs_once() -> (
    None
):
    # Arrange
    session = _session()
    roadmap_item = _item()
    existing_answers = [
        _answer(
            question_number=1,
            question_text="既存の質問",
            answer_text="既存の回答",
        ),
    ]
    original_error = RuntimeError("history read failed")
    session_store = _RecordingSessionStore(sessions={session.id: session})
    answer_store = _RecordingAnswerStore(
        histories={session.id: existing_answers},
        find_error=original_error,
    )
    item_reader = _RecordingItemReader(items={roadmap_item.id: roadmap_item})
    graph_runner = _RecordingGraphRunner()
    resume_input = ResumeSessionInput(session_id=session.id)

    # Act / Assert
    with (
        capture_logs() as log_output,
        pytest.raises(QuizSessionLifecycleError) as exc_info,
    ):
        resume_session(
            resume_input,
            session_store=session_store,
            answer_store=answer_store,
            item_reader=item_reader,
            graph_runner=graph_runner,
        )

    assert exc_info.value.error_code == "session_resume_history_load_failed"
    assert (
        exc_info.value.message == "quiz session resume history load failed: "
        "session_id=session-001, roadmap_item_id=item-001"
    )
    assert exc_info.value.__cause__ is original_error
    assert answer_store.histories[session.id] == existing_answers
    assert answer_store.find_by_session_calls == [session.id]
    assert session_store.create_session_calls == []
    assert session_store.complete_session_calls == []
    assert session_store.discard_session_calls == []
    assert graph_runner.resume_graph_calls == []
    persisted_session = session_store.persisted_session(session.id)
    assert persisted_session is not None
    assert persisted_session.status == "in_progress"
    assert persisted_session.completed_at is None
    _assert_single_failure_log(
        log_output,
        event_name=_RESUME_HISTORY_LOAD_FAILED_EVENT,
        expected_fields={
            "session_id": session.id,
            "roadmap_item_id": roadmap_item.id,
            "error_code": "session_resume_history_load_failed",
            "error_type": "RuntimeError",
        },
    )
    assert_no_log_event(log_output, _START_FAILED_EVENT)
    assert_no_log_event(log_output, _RESUME_LLM_START_FAILED_EVENT)


def test_tc_32_resume_session_invalid_answer_type_uses_history_failure_contract_and_skips_graph_resume() -> (
    None
):
    # Arrange
    session = _session(session_id="session-invalid-answer-type")
    roadmap_item = _item()
    persisted_answers = [
        _answer(
            question_number=1,
            question_text="既存の質問",
            answer_text="既存の回答",
            answer_type="invalid-type",
        ),
    ]
    session_store = _RecordingSessionStore(sessions={session.id: session})
    answer_store = _RecordingAnswerStore(histories={session.id: persisted_answers})
    item_reader = _RecordingItemReader(items={roadmap_item.id: roadmap_item})
    graph_runner = _RecordingGraphRunner()
    resume_input = ResumeSessionInput(session_id=session.id)

    # Act / Assert
    with (
        capture_logs() as log_output,
        pytest.raises(QuizSessionLifecycleError) as exc_info,
    ):
        resume_session(
            resume_input,
            session_store=session_store,
            answer_store=answer_store,
            item_reader=item_reader,
            graph_runner=graph_runner,
        )

    assert exc_info.value.error_code == "session_resume_history_load_failed"
    assert (
        exc_info.value.message == "quiz session resume history load failed: "
        "session_id=session-invalid-answer-type, roadmap_item_id=item-001"
    )
    assert isinstance(exc_info.value.__cause__, ValueError)
    assert str(exc_info.value.__cause__) == "invalid quiz answer type: invalid-type"
    assert answer_store.find_by_session_calls == [session.id]
    assert graph_runner.resume_graph_calls == []
    assert session_store.create_session_calls == []
    assert session_store.complete_session_calls == []
    assert session_store.discard_session_calls == []
    persisted_session = session_store.persisted_session(session.id)
    assert persisted_session is not None
    assert persisted_session.status == "in_progress"
    assert persisted_session.completed_at is None
    _assert_single_failure_log(
        log_output,
        event_name=_RESUME_HISTORY_LOAD_FAILED_EVENT,
        expected_fields={
            "session_id": session.id,
            "roadmap_item_id": roadmap_item.id,
            "error_code": "session_resume_history_load_failed",
            "error_type": "ValueError",
        },
    )
    assert_no_log_event(log_output, _START_FAILED_EVENT)
    assert_no_log_event(log_output, _RESUME_LLM_START_FAILED_EVENT)


def test_tc_32_resume_session_graph_failure_keeps_state_unchanged_and_logs_once() -> (
    None
):
    # Arrange
    session = _session(session_id="session-resume-fail")
    roadmap_item = _item()
    existing_answers = [
        _answer(
            question_number=1,
            question_text="前回の質問",
            answer_text="前回の回答",
            score=75,
            feedback="既存履歴",
        ),
    ]
    original_error = RuntimeError("resume graph failed")
    session_store = _RecordingSessionStore(sessions={session.id: session})
    answer_store = _RecordingAnswerStore(histories={session.id: existing_answers})
    item_reader = _RecordingItemReader(items={roadmap_item.id: roadmap_item})
    graph_runner = _RecordingGraphRunner(resume_error=original_error)
    resume_input = ResumeSessionInput(session_id=session.id)

    # Act / Assert
    with (
        capture_logs() as log_output,
        pytest.raises(QuizSessionLifecycleError) as exc_info,
    ):
        resume_session(
            resume_input,
            session_store=session_store,
            answer_store=answer_store,
            item_reader=item_reader,
            graph_runner=graph_runner,
        )

    assert exc_info.value.error_code == "session_resume_llm_start_failed"
    assert (
        exc_info.value.message == "quiz session resume llm start failed: "
        "session_id=session-resume-fail, roadmap_item_id=item-001"
    )
    assert exc_info.value.__cause__ is original_error
    assert answer_store.histories[session.id] == existing_answers
    assert session_store.create_session_calls == []
    assert session_store.complete_session_calls == []
    assert session_store.discard_session_calls == []
    assert len(graph_runner.resume_graph_calls) == 1
    persisted_session = session_store.persisted_session(session.id)
    assert persisted_session is not None
    assert persisted_session.status == "in_progress"
    assert persisted_session.completed_at is None
    _assert_single_failure_log(
        log_output,
        event_name=_RESUME_LLM_START_FAILED_EVENT,
        expected_fields={
            "session_id": session.id,
            "roadmap_item_id": roadmap_item.id,
            "error_code": "session_resume_llm_start_failed",
            "error_type": "RuntimeError",
        },
    )
    assert_no_log_event(log_output, _START_FAILED_EVENT)
    assert_no_log_event(log_output, _RESUME_HISTORY_LOAD_FAILED_EVENT)
