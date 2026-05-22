from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from structlog.testing import capture_logs

from quiz.application.summary_test_record import record_summary_test
from quiz.application.summary_test_record_types import (
    SummaryAnalysis,
    SummaryTestRecordError,
)
from shared.log_assertions import find_log_events

if TYPE_CHECKING:
    from quiz.domain.session_state import (
        QuizAnswerRecord,
        RoadmapItemLevel,
        SessionState,
    )


_FAILED_EVENT = "summary_test_record_failed"


class _RecordingSummaryTestLlm:
    def __init__(
        self,
        *,
        output: SummaryAnalysis | None = None,
        error: SummaryTestRecordError | None = None,
    ) -> None:
        self._output = output
        self._error = error
        self.calls: list[tuple[str, str, list[QuizAnswerRecord]]] = []

    def analyze_session(
        self,
        title: str,
        description: str,
        answers: list[QuizAnswerRecord],
    ) -> SummaryAnalysis:
        self.calls.append((title, description, answers))
        if self._error is not None:
            raise self._error
        assert self._output is not None
        return self._output


class _RecordingSummaryTestStore:
    def __init__(
        self,
        *,
        error: SummaryTestRecordError | None = None,
    ) -> None:
        self._error = error
        self.calls: list[tuple[str, str, int, str]] = []

    def save_result(
        self,
        session_id: str,
        roadmap_item_id: str,
        score: int,
        analysis: str,
    ) -> None:
        self.calls.append((session_id, roadmap_item_id, score, analysis))
        if self._error is not None:
            raise self._error


def _answers(count: int = 2) -> list[QuizAnswerRecord]:
    return [
        {
            "question_number": i,
            "confirmation_point_id": f"cp_{i:03d}",
            "question_text": f"質問 {i}",
            "answer_type": "textarea",
            "answer_text": f"回答 {i}",
            "score": 60 + i * 10,
            "feedback": f"フィードバック {i}",
        }
        for i in range(1, count + 1)
    ]


def _state(
    *,
    session_id: str = "sess_mid_001",
    roadmap_item_id: str = "rm_typescript_basic",
    roadmap_item_level: RoadmapItemLevel = "middle",
    roadmap_item_title: str = "TypeScript > 基礎",
    roadmap_item_description: str = "型注釈、型推論、ジェネリクスの基礎を扱う",
    answers: list[QuizAnswerRecord] | None = None,
) -> SessionState:
    return {
        "session_id": session_id,
        "roadmap_item_id": roadmap_item_id,
        "roadmap_item_level": roadmap_item_level,
        "roadmap_item_title": roadmap_item_title,
        "roadmap_item_description": roadmap_item_description,
        "answers": _answers() if answers is None else answers,
    }


def _summary_test_record_error(
    *,
    error_code: str,
    message: str,
    cause: Exception,
) -> SummaryTestRecordError:
    error = SummaryTestRecordError(error_code=error_code, message=message)
    error.__cause__ = cause
    return error


def test_tc_01_middle_level_saves_summary_test_result() -> None:
    # Arrange
    answers: list[QuizAnswerRecord] = [
        {
            "question_number": 1,
            "confirmation_point_id": "cp_001",
            "question_text": "型推論とは何ですか",
            "answer_type": "textarea",
            "answer_text": "文脈から型を決める仕組みです",
            "score": 72,
            "feedback": "概念は説明できています",
        },
        {
            "question_number": 2,
            "confirmation_point_id": "cp_002",
            "question_text": "ジェネリック関数を書いてください",
            "answer_type": "code",
            "answer_text": "function id<T>(value: T): T { return value }",
            "score": 58,
            "feedback": "基本形は書けています",
        },
    ]
    state = _state(
        session_id="sess_mid_001",
        roadmap_item_id="rm_typescript_basic",
        roadmap_item_level="middle",
        roadmap_item_title="TypeScript > 基礎",
        roadmap_item_description="型注釈、型推論、ジェネリクスの基礎を扱う",
        answers=answers,
    )
    analysis_text = (
        "型の基礎知識は十分ですが、ジェネリクスの実践的な使用に課題があります。"
        "特に型パラメータを使った関数を自力で書く場面で構文ミスが目立ちました。"
        "また、型推論の仕組みは理解していますが、いつ明示的に型を指定すべきかの判断基準が曖昧です。"
        "ジェネリクスの実践問題を重点的に復習することを推奨します。"
    )
    llm = _RecordingSummaryTestLlm(
        output=SummaryAnalysis(score=65, analysis=analysis_text),
    )
    store = _RecordingSummaryTestStore()

    # Act
    with capture_logs() as log_output:
        record_summary_test(state, llm=llm, store=store)

    # Assert
    assert len(llm.calls) == 1
    assert len(store.calls) == 1
    assert store.calls[0][0] == "sess_mid_001"
    assert store.calls[0][1] == "rm_typescript_basic"
    assert store.calls[0][2] == 65
    assert store.calls[0][3] == analysis_text
    assert find_log_events(log_output, _FAILED_EVENT) == []


def test_tc_10_major_level_passes_title_description_and_all_answers_to_llm() -> None:
    # Arrange
    answers: list[QuizAnswerRecord] = [
        {
            "question_number": 1,
            "confirmation_point_id": "cp_001",
            "question_text": "型推論の仕組みを説明してください",
            "answer_type": "textarea",
            "answer_text": "引数や代入先から型を推論します",
            "score": 84,
            "feedback": "概念は理解できています",
        },
        {
            "question_number": 2,
            "confirmation_point_id": "cp_002",
            "question_text": "境界付きジェネリクスを使った関数を書いてください",
            "answer_type": "code",
            "answer_text": "function pickId<T extends { id: string }>(value: T) { return value.id }",
            "score": 63,
            "feedback": "境界指定はできています",
        },
        {
            "question_number": 3,
            "confirmation_point_id": "cp_003",
            "question_text": "型引数を明示すべき場面を説明してください",
            "answer_type": "textarea",
            "answer_text": "推論が曖昧な時です",
            "score": 56,
            "feedback": "判断基準がまだ曖昧です",
        },
    ]
    analysis_text = (
        "概念理解は安定していますが、実践問題になるとジェネリクス境界と"
        "明示的な型指定の判断に揺れがあります。知識問題より実装問題の得点が低く、"
        "具体項目間で理解度に偏りがあります。次は境界付きジェネリクスと"
        "型引数を明示する場面を重点的に復習してください。"
    )
    state = _state(
        session_id="sess_major_001",
        roadmap_item_id="rm_typescript",
        roadmap_item_level="major",
        roadmap_item_title="TypeScript",
        roadmap_item_description="型システム全体の理解を確認するまとめテスト",
        answers=answers,
    )
    llm = _RecordingSummaryTestLlm(
        output=SummaryAnalysis(score=78, analysis=analysis_text),
    )
    store = _RecordingSummaryTestStore()

    # Act
    record_summary_test(state, llm=llm, store=store)

    # Assert
    assert len(llm.calls) == 1
    call = llm.calls[0]
    assert call[0] == "TypeScript"
    assert call[1] == "型システム全体の理解を確認するまとめテスト"
    assert len(call[2]) == 3
    assert call[2] is answers
    assert len(store.calls) == 1
    assert store.calls[0][3] == analysis_text


def test_tc_20_detail_level_early_returns_without_calling_llm_or_store() -> None:
    # Arrange
    state = _state(
        session_id="sess_detail_001",
        roadmap_item_id="rm_ts_generics_detail",
        roadmap_item_level="detail",
        roadmap_item_title="TypeScript > ジェネリクス > 基本",
        roadmap_item_description="detail項目の確認",
        answers=_answers(1),
    )
    llm = _RecordingSummaryTestLlm(
        output=SummaryAnalysis(score=0, analysis="should not be used"),
    )
    store = _RecordingSummaryTestStore()

    # Act
    with capture_logs() as log_output:
        record_summary_test(state, llm=llm, store=store)

    # Assert
    assert len(llm.calls) == 0
    assert len(store.calls) == 0
    assert find_log_events(log_output, _FAILED_EVENT) == []


def test_tc_21_multiple_sessions_for_same_item_produce_separate_save_requests() -> (
    None
):
    # Arrange
    llm_1 = _RecordingSummaryTestLlm(
        output=SummaryAnalysis(score=55, analysis="1回目の分析結果"),
    )
    store_1 = _RecordingSummaryTestStore()
    state_1 = _state(
        session_id="sess_hist_001",
        roadmap_item_id="rm_typescript_basic",
        roadmap_item_level="middle",
    )

    llm_2 = _RecordingSummaryTestLlm(
        output=SummaryAnalysis(score=72, analysis="2回目の分析結果"),
    )
    store_2 = _RecordingSummaryTestStore()
    state_2 = _state(
        session_id="sess_hist_002",
        roadmap_item_id="rm_typescript_basic",
        roadmap_item_level="middle",
    )

    # Act
    record_summary_test(state_1, llm=llm_1, store=store_1)
    record_summary_test(state_2, llm=llm_2, store=store_2)

    # Assert
    assert len(store_1.calls) == 1
    assert store_1.calls[0][0] == "sess_hist_001"
    assert store_1.calls[0][1] == "rm_typescript_basic"

    assert len(store_2.calls) == 1
    assert store_2.calls[0][0] == "sess_hist_002"
    assert store_2.calls[0][1] == "rm_typescript_basic"


def test_tc_22_boundary_scores_zero_and_hundred_are_passed_through() -> None:
    # Arrange — score=0
    llm_zero = _RecordingSummaryTestLlm(
        output=SummaryAnalysis(
            score=0,
            analysis="基礎概念の取り違えが多く、全体的に再学習が必要です。",
        ),
    )
    store_zero = _RecordingSummaryTestStore()
    state_zero = _state(
        session_id="sess_score_0",
        roadmap_item_level="middle",
    )

    # Arrange — score=100
    llm_hundred = _RecordingSummaryTestLlm(
        output=SummaryAnalysis(
            score=100,
            analysis="知識問題・実践問題ともに安定しており、全体理解は十分です。",
        ),
    )
    store_hundred = _RecordingSummaryTestStore()
    state_hundred = _state(
        session_id="sess_score_100",
        roadmap_item_level="major",
    )

    # Act
    record_summary_test(state_zero, llm=llm_zero, store=store_zero)
    record_summary_test(state_hundred, llm=llm_hundred, store=store_hundred)

    # Assert
    assert store_zero.calls[0][2] == 0
    assert store_hundred.calls[0][2] == 100


def test_tc_30_success_path_calls_llm_and_store_once_each_without_failure_log() -> (
    None
):
    # Arrange
    llm = _RecordingSummaryTestLlm(
        output=SummaryAnalysis(score=70, analysis="全体的に安定した理解を示しています。"),
    )
    store = _RecordingSummaryTestStore()
    state = _state(roadmap_item_level="middle")

    # Act
    with capture_logs() as log_output:
        record_summary_test(state, llm=llm, store=store)

    # Assert
    assert len(llm.calls) == 1
    assert len(store.calls) == 1
    assert find_log_events(log_output, _FAILED_EVENT) == []


def test_tc_31_llm_request_failure_is_logged_once_and_reraised() -> None:
    # Arrange
    cause = RuntimeError("llm request failed")
    error = _summary_test_record_error(
        error_code="llm_request_failed",
        message="summary test record llm request failed",
        cause=cause,
    )
    llm = _RecordingSummaryTestLlm(error=error)
    store = _RecordingSummaryTestStore()
    state = _state(roadmap_item_level="middle")

    # Act / Assert
    with (
        capture_logs() as log_output,
        pytest.raises(SummaryTestRecordError) as exc_info,
    ):
        record_summary_test(state, llm=llm, store=store)

    assert exc_info.value is error
    assert exc_info.value.error_code == "llm_request_failed"
    assert exc_info.value.message == "summary test record llm request failed"
    assert exc_info.value.__cause__ is cause
    assert len(llm.calls) == 1
    assert len(store.calls) == 0
    assert len(log_output) == 1
    assert find_log_events(log_output, _FAILED_EVENT) == [log_output[0]]
    assert log_output[0]["event"] == _FAILED_EVENT


def test_tc_32_llm_response_parse_failure_is_logged_once_and_reraised() -> None:
    # Arrange
    cause = ValueError("parse failed")
    error = _summary_test_record_error(
        error_code="llm_response_parse_failed",
        message="summary test record llm response parse failed",
        cause=cause,
    )
    llm = _RecordingSummaryTestLlm(error=error)
    store = _RecordingSummaryTestStore()
    state = _state(roadmap_item_level="major")

    # Act / Assert
    with (
        capture_logs() as log_output,
        pytest.raises(SummaryTestRecordError) as exc_info,
    ):
        record_summary_test(state, llm=llm, store=store)

    assert exc_info.value is error
    assert exc_info.value.error_code == "llm_response_parse_failed"
    assert exc_info.value.message == "summary test record llm response parse failed"
    assert exc_info.value.__cause__ is cause
    assert len(llm.calls) == 1
    assert len(store.calls) == 0
    assert len(log_output) == 1
    assert find_log_events(log_output, _FAILED_EVENT) == [log_output[0]]
    assert log_output[0]["event"] == _FAILED_EVENT


def test_tc_33_persistence_failure_is_logged_once_and_reraised() -> None:
    # Arrange
    cause = RuntimeError("db write failed")
    error = _summary_test_record_error(
        error_code="persistence_failed",
        message="summary test record persistence failed",
        cause=cause,
    )
    llm = _RecordingSummaryTestLlm(
        output=SummaryAnalysis(score=70, analysis="分析結果テキスト"),
    )
    store = _RecordingSummaryTestStore(error=error)
    state = _state(roadmap_item_level="middle")

    # Act / Assert
    with (
        capture_logs() as log_output,
        pytest.raises(SummaryTestRecordError) as exc_info,
    ):
        record_summary_test(state, llm=llm, store=store)

    assert exc_info.value is error
    assert exc_info.value.error_code == "persistence_failed"
    assert exc_info.value.message == "summary test record persistence failed"
    assert exc_info.value.__cause__ is cause
    assert len(llm.calls) == 1
    assert len(store.calls) == 1
    assert len(log_output) == 1
    assert find_log_events(log_output, _FAILED_EVENT) == [log_output[0]]
    assert log_output[0]["event"] == _FAILED_EVENT
