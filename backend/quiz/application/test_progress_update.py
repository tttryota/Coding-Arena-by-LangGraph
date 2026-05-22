from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from structlog.testing import capture_logs

from quiz.application.progress_update import update_progress
from quiz.application.progress_update_types import (
    ProgressOutput,
    ProgressUpdateError,
)
from shared.log_assertions import find_log_events

if TYPE_CHECKING:
    from datetime import datetime

    from quiz.domain.session_state import (
        ConfirmationPoint,
        QuizAnswerRecord,
        RoadmapItemLevel,
        SessionState,
    )


_FAILED_EVENT = "progress_update_failed"


class _RecordingProgressUpdateLlm:
    def __init__(
        self,
        *,
        output: ProgressOutput | None = None,
        error: ProgressUpdateError | None = None,
    ) -> None:
        self._output = output
        self._error = error
        self.calls: list[
            tuple[str, str, list[str], list[QuizAnswerRecord]]
        ] = []

    def evaluate_session(
        self,
        roadmap_item_title: str,
        roadmap_item_description: str,
        checkpoints: list[str],
        answers: list[QuizAnswerRecord],
    ) -> ProgressOutput:
        self.calls.append(
            (roadmap_item_title, roadmap_item_description, checkpoints, answers),
        )
        if self._error is not None:
            raise self._error
        assert self._output is not None
        return self._output


class _RecordingProgressUpdateStore:
    def __init__(
        self,
        *,
        error_on_update: ProgressUpdateError | None = None,
        error_on_save: ProgressUpdateError | None = None,
    ) -> None:
        self._error_on_update = error_on_update
        self._error_on_save = error_on_save
        self.update_calls: list[tuple[str, int, datetime]] = []
        self.save_calls: list[tuple[str, str, int, str]] = []
        self.complete_calls: list[str] = []

    def update_roadmap_item_progress(
        self,
        item_id: str,
        score: int,
        last_quiz_at: datetime,
    ) -> None:
        self.update_calls.append((item_id, score, last_quiz_at))
        if self._error_on_update is not None:
            raise self._error_on_update

    def save_summary_test_result(
        self,
        session_id: str,
        item_id: str,
        score: int,
        comment: str,
    ) -> None:
        self.save_calls.append((session_id, item_id, score, comment))
        if self._error_on_save is not None:
            raise self._error_on_save

    def complete_session(self, session_id: str) -> None:
        self.complete_calls.append(session_id)


def _confirmation_points(*contents: str) -> list[ConfirmationPoint]:
    return [
        {
            "id": f"cp_{index:03d}",
            "content": content,
            "format": "knowledge",
        }
        for index, content in enumerate(contents, start=1)
    ]


def _answers(count: int = 5) -> list[QuizAnswerRecord]:
    return [
        {
            "question_number": i,
            "confirmation_point_id": f"cp_{i:03d}",
            "question_text": f"質問 {i}",
            "answer_type": "textarea",
            "answer_text": f"回答 {i}",
            "score": 70 + i * 5,
            "feedback": f"フィードバック {i}",
        }
        for i in range(1, count + 1)
    ]


def _state(
    *,
    session_id: str = "sess_001",
    roadmap_item_id: str = "detail_001",
    roadmap_item_level: RoadmapItemLevel = "detail",
    roadmap_item_title: str = "Union型の narrowing とガード条件",
    roadmap_item_description: str = "TypeScript の型 narrowing を理解する",
    confirmation_points: list[ConfirmationPoint] | None = None,
    answers: list[QuizAnswerRecord] | None = None,
) -> SessionState:
    return {
        "session_id": session_id,
        "roadmap_item_id": roadmap_item_id,
        "roadmap_item_level": roadmap_item_level,
        "roadmap_item_title": roadmap_item_title,
        "roadmap_item_description": roadmap_item_description,
        "confirmation_points": (
            _confirmation_points("型ガードの使い方", "narrowingの仕組み", "判別共用体の利点")
            if confirmation_points is None
            else confirmation_points
        ),
        "answers": _answers() if answers is None else answers,
    }


def _progress_update_error(
    *,
    error_code: str,
    message: str,
    cause: Exception,
) -> ProgressUpdateError:
    error = ProgressUpdateError(error_code=error_code, message=message)
    error.__cause__ = cause
    return error


def test_tc_01_detail_session_updates_roadmap_item_score_and_last_quiz_at() -> None:
    # Arrange
    state = _state(
        roadmap_item_level="detail",
        roadmap_item_id="detail_001",
        answers=_answers(5),
    )
    llm = _RecordingProgressUpdateLlm(
        output=ProgressOutput(
            score=81,
            comment="条件分岐ごとの型の絞り込みは概ね安定している。"
            "一方で user-defined type guard の戻り値設計には曖昧さが残る。",
        ),
    )
    store = _RecordingProgressUpdateStore()

    # Act
    with capture_logs() as log_output:
        update_progress(state, llm=llm, store=store)

    # Assert
    assert len(llm.calls) == 1
    assert len(store.update_calls) == 1
    assert store.update_calls[0][0] == "detail_001"
    assert store.update_calls[0][1] == 81
    assert store.update_calls[0][2] is not None
    assert len(store.complete_calls) == 1
    assert store.complete_calls[0] == "sess_001"
    assert len(store.save_calls) == 0
    assert find_log_events(log_output, _FAILED_EVENT) == []


@pytest.mark.parametrize("level", ["middle", "major"])
def test_tc_02_summary_test_saves_result_without_updating_roadmap_item(
    level: RoadmapItemLevel,
) -> None:
    # Arrange
    state = _state(
        session_id="sess_summary_001",
        roadmap_item_id="item_summary_001",
        roadmap_item_level=level,
        answers=_answers(3),
    )
    llm = _RecordingProgressUpdateLlm(
        output=ProgressOutput(
            score=73,
            comment="関連項目を横断した理解はあるが、説明の一貫性に揺れがある。",
        ),
    )
    store = _RecordingProgressUpdateStore()

    # Act
    with capture_logs() as log_output:
        update_progress(state, llm=llm, store=store)

    # Assert
    assert len(llm.calls) == 1
    assert len(store.update_calls) == 0
    assert len(store.save_calls) == 1
    assert store.save_calls[0] == (
        "sess_summary_001",
        "item_summary_001",
        73,
        "関連項目を横断した理解はあるが、説明の一貫性に揺れがある。",
    )
    assert len(store.complete_calls) == 1
    assert store.complete_calls[0] == "sess_summary_001"
    assert find_log_events(log_output, _FAILED_EVENT) == []


def test_tc_10_llm_receives_full_context_including_checkpoints_and_answers() -> None:
    # Arrange
    cps = _confirmation_points("型ガードの使い方", "narrowingの仕組み", "判別共用体の利点")
    answers: list[QuizAnswerRecord] = [
        {
            "question_number": 1,
            "confirmation_point_id": "cp_001",
            "question_text": "型ガードとは何ですか",
            "answer_type": "textarea",
            "answer_text": "型を絞り込む仕組みです",
            "score": 75,
            "feedback": "概念は理解できています",
        },
        {
            "question_number": 2,
            "confirmation_point_id": "cp_002",
            "question_text": "narrowingの具体例を教えてください",
            "answer_type": "textarea",
            "answer_text": "typeof や instanceof を使います",
            "score": 82,
            "feedback": "具体例が的確です",
        },
        {
            "question_number": 3,
            "confirmation_point_id": "cp_001",
            "question_text": "解説してください",
            "answer_type": "textarea",
            "answer_text": "解説を見て理解しました",
            "score": 60,
            "feedback": "解説後の理解を確認します",
        },
        {
            "question_number": 4,
            "confirmation_point_id": "cp_003",
            "question_text": "判別共用体のメリットは何ですか",
            "answer_type": "textarea",
            "answer_text": "型安全な分岐ができます",
            "score": 88,
            "feedback": "的確に説明できています",
        },
    ]
    state = _state(
        roadmap_item_title="Union型の narrowing とガード条件",
        roadmap_item_description="TypeScript の型 narrowing を理解する",
        confirmation_points=cps,
        answers=answers,
    )
    llm = _RecordingProgressUpdateLlm(
        output=ProgressOutput(
            score=78,
            comment="型ガードの基本は安定している。",
        ),
    )
    store = _RecordingProgressUpdateStore()

    # Act
    update_progress(state, llm=llm, store=store)

    # Assert
    assert len(llm.calls) == 1
    call = llm.calls[0]
    assert call[0] == "Union型の narrowing とガード条件"
    assert call[1] == "TypeScript の型 narrowing を理解する"
    assert call[2] == ["型ガードの使い方", "narrowingの仕組み", "判別共用体の利点"]
    assert len(call[3]) == 4
    assert call[3] is answers


def test_tc_11_lower_score_overwrites_previous_higher_score() -> None:
    # Arrange
    state = _state(
        roadmap_item_level="detail",
        roadmap_item_id="detail_002",
        answers=_answers(3),
    )
    llm = _RecordingProgressUpdateLlm(
        output=ProgressOutput(
            score=61,
            comment="概念理解はあるが、実装時の再現性に大きな揺れがある。",
        ),
    )
    store = _RecordingProgressUpdateStore()

    # Act
    update_progress(state, llm=llm, store=store)

    # Assert
    assert len(store.update_calls) == 1
    assert store.update_calls[0][0] == "detail_002"
    assert store.update_calls[0][1] == 61
    assert store.update_calls[0][2] is not None
    assert len(store.complete_calls) == 1


def test_tc_20_zero_answers_skips_llm_and_only_completes_session() -> None:
    # Arrange
    state = _state(
        session_id="sess_zero",
        roadmap_item_level="detail",
        answers=[],
    )
    llm = _RecordingProgressUpdateLlm(
        output=ProgressOutput(score=0, comment="should not be used"),
    )
    store = _RecordingProgressUpdateStore()

    # Act
    update_progress(state, llm=llm, store=store)

    # Assert
    assert len(llm.calls) == 0
    assert len(store.update_calls) == 0
    assert len(store.save_calls) == 0
    assert len(store.complete_calls) == 1
    assert store.complete_calls[0] == "sess_zero"


def test_tc_30_success_path_calls_dependencies_once_each_and_logs_no_failure() -> None:
    # Arrange
    state = _state(
        roadmap_item_level="detail",
        answers=_answers(2),
    )
    llm = _RecordingProgressUpdateLlm(
        output=ProgressOutput(score=80, comment="理解は概ね安定している。"),
    )
    store = _RecordingProgressUpdateStore()

    # Act
    with capture_logs() as log_output:
        update_progress(state, llm=llm, store=store)

    # Assert
    assert len(llm.calls) == 1
    assert len(store.update_calls) == 1
    assert len(store.save_calls) == 0
    assert len(store.complete_calls) == 1
    assert find_log_events(log_output, _FAILED_EVENT) == []


def test_tc_31_llm_request_failure_is_logged_once_and_reraised() -> None:
    # Arrange
    cause = RuntimeError("request failed")
    error = _progress_update_error(
        error_code="llm_request_failed",
        message="progress update llm request failed",
        cause=cause,
    )
    state = _state(answers=_answers(1))
    llm = _RecordingProgressUpdateLlm(error=error)
    store = _RecordingProgressUpdateStore()

    # Act / Assert
    with (
        capture_logs() as log_output,
        pytest.raises(ProgressUpdateError) as exc_info,
    ):
        update_progress(state, llm=llm, store=store)

    assert exc_info.value is error
    assert exc_info.value.error_code == "llm_request_failed"
    assert exc_info.value.message == "progress update llm request failed"
    assert exc_info.value.__cause__ is cause
    assert len(llm.calls) == 1
    assert len(store.update_calls) == 0
    assert len(store.save_calls) == 0
    assert len(store.complete_calls) == 0
    assert len(log_output) == 1
    assert find_log_events(log_output, _FAILED_EVENT) == [log_output[0]]
    assert log_output[0]["event"] == _FAILED_EVENT
    assert log_output[0]["error_code"] == "llm_request_failed"
    assert log_output[0]["message"] == "progress update llm request failed"


def test_tc_32_llm_response_parse_failure_is_logged_once_and_reraised() -> None:
    # Arrange
    cause = ValueError("parse failed")
    error = _progress_update_error(
        error_code="llm_response_parse_failed",
        message="progress update llm response parse failed",
        cause=cause,
    )
    state = _state(answers=_answers(1))
    llm = _RecordingProgressUpdateLlm(error=error)
    store = _RecordingProgressUpdateStore()

    # Act / Assert
    with (
        capture_logs() as log_output,
        pytest.raises(ProgressUpdateError) as exc_info,
    ):
        update_progress(state, llm=llm, store=store)

    assert exc_info.value is error
    assert exc_info.value.error_code == "llm_response_parse_failed"
    assert exc_info.value.message == "progress update llm response parse failed"
    assert exc_info.value.__cause__ is cause
    assert len(llm.calls) == 1
    assert len(store.update_calls) == 0
    assert len(store.save_calls) == 0
    assert len(store.complete_calls) == 0
    assert len(log_output) == 1
    assert find_log_events(log_output, _FAILED_EVENT) == [log_output[0]]
    assert log_output[0]["event"] == _FAILED_EVENT
    assert log_output[0]["error_code"] == "llm_response_parse_failed"
    assert log_output[0]["message"] == "progress update llm response parse failed"
