from __future__ import annotations

import pytest

from quiz.application.summary_test_results import get_summary_test_results
from quiz.application.summary_test_results_types import (
    SummaryTestResultRecord,
    SummaryTestResultsError,
    SummaryTestResultsNotFoundError,
)


class _StubExistenceChecker:
    def __init__(
        self,
        *,
        existing_ids: set[str] | None = None,
        error: Exception | None = None,
    ) -> None:
        self._existing_ids = existing_ids or set()
        self._error = error
        self.calls: list[str] = []

    def item_exists(self, item_id: str) -> bool:
        self.calls.append(item_id)
        if self._error is not None:
            raise self._error
        return item_id in self._existing_ids


class _StubSummaryTestResultsStore:
    def __init__(
        self,
        *,
        results_by_item: dict[str, list[SummaryTestResultRecord]] | None = None,
        error: Exception | None = None,
    ) -> None:
        self._results_by_item = results_by_item or {}
        self._error = error
        self.calls: list[str] = []

    def find_by_roadmap_item(
        self,
        roadmap_item_id: str,
    ) -> list[SummaryTestResultRecord]:
        self.calls.append(roadmap_item_id)
        if self._error is not None:
            raise self._error
        return self._results_by_item.get(roadmap_item_id, [])


def _record(
    *,
    record_id: str = "str_001",
    session_id: str = "sess_001",
    score: int = 65,
    analysis: str = "分析テキスト",
    created_at: str = "2026-05-18T14:00:00",
) -> SummaryTestResultRecord:
    return SummaryTestResultRecord(
        id=record_id,
        session_id=session_id,
        score=score,
        analysis=analysis,
        created_at=created_at,
    )


def test_tc_01_returns_single_result_with_all_fields() -> None:
    # Arrange
    record = _record(
        record_id="str_001",
        session_id="sess_001",
        score=65,
        analysis="型の基礎知識は十分ですが、ジェネリクスの実践的な使用に課題があります。",
        created_at="2026-05-18T14:00:00",
    )
    checker = _StubExistenceChecker(existing_ids={"rm_mid_001"})
    store = _StubSummaryTestResultsStore(
        results_by_item={"rm_mid_001": [record]},
    )

    # Act
    results = get_summary_test_results(
        "rm_mid_001",
        existence_checker=checker,
        store=store,
    )

    # Assert
    assert len(results) == 1
    assert results[0].id == "str_001"
    assert results[0].session_id == "sess_001"
    assert results[0].score == 65
    assert results[0].analysis == "型の基礎知識は十分ですが、ジェネリクスの実践的な使用に課題があります。"
    assert results[0].created_at == "2026-05-18T14:00:00"


def test_tc_02_summary_test_result_record_is_frozen_dataclass_with_five_fields() -> (
    None
):
    # Arrange / Act
    record = SummaryTestResultRecord(
        id="str_002",
        session_id="sess_002",
        score=45,
        analysis="全体的に理解が浅いです。",
        created_at="2026-05-10T10:00:00",
    )

    # Assert
    assert record.id == "str_002"
    assert record.session_id == "sess_002"
    assert record.score == 45
    assert record.analysis == "全体的に理解が浅いです。"
    assert record.created_at == "2026-05-10T10:00:00"

    with pytest.raises(AttributeError):
        record.score = 99  # type: ignore[misc]


def test_tc_10_delegates_roadmap_item_id_to_store_and_returns_results() -> None:
    # Arrange
    records = [
        _record(
            record_id="str_010",
            session_id="sess_010",
            score=78,
            analysis="分析A",
            created_at="2026-05-18T14:00:00",
        ),
        _record(
            record_id="str_011",
            session_id="sess_011",
            score=52,
            analysis="分析B",
            created_at="2026-05-10T10:00:00",
        ),
    ]
    checker = _StubExistenceChecker(existing_ids={"rm_large_001"})
    store = _StubSummaryTestResultsStore(
        results_by_item={"rm_large_001": records},
    )

    # Act
    results = get_summary_test_results(
        "rm_large_001",
        existence_checker=checker,
        store=store,
    )

    # Assert
    assert store.calls == ["rm_large_001"]
    assert len(results) == 2
    assert results[0].id == "str_010"
    assert results[1].id == "str_011"


def test_tc_11_results_are_returned_in_created_at_descending_order() -> None:
    # Arrange
    records = [
        _record(
            record_id="str_newer",
            created_at="2026-05-18T14:00:00",
        ),
        _record(
            record_id="str_older",
            created_at="2026-05-10T10:00:00",
        ),
    ]
    checker = _StubExistenceChecker(existing_ids={"rm_large_001"})
    store = _StubSummaryTestResultsStore(
        results_by_item={"rm_large_001": records},
    )

    # Act
    results = get_summary_test_results(
        "rm_large_001",
        existence_checker=checker,
        store=store,
    )

    # Assert
    assert len(results) == 2
    assert results[0].created_at == "2026-05-18T14:00:00"
    assert results[1].created_at == "2026-05-10T10:00:00"


def test_tc_20_existing_item_with_no_results_returns_empty_list() -> None:
    # Arrange
    checker = _StubExistenceChecker(existing_ids={"rm_mid_002"})
    store = _StubSummaryTestResultsStore(results_by_item={})

    # Act
    results = get_summary_test_results(
        "rm_mid_002",
        existence_checker=checker,
        store=store,
    )

    # Assert
    assert results == []


def test_tc_30_nonexistent_item_raises_not_found_error() -> None:
    # Arrange
    checker = _StubExistenceChecker(existing_ids=set())
    store = _StubSummaryTestResultsStore()

    # Act / Assert
    with pytest.raises(SummaryTestResultsNotFoundError) as exc_info:
        get_summary_test_results(
            "rm_missing_001",
            existence_checker=checker,
            store=store,
        )

    assert exc_info.value.error_code == "item_not_found"
    assert exc_info.value.message == "roadmap item not found"


def test_tc_31_existence_check_db_failure_raises_persistence_error() -> None:
    # Arrange
    db_error = RuntimeError("db read failed")
    checker = _StubExistenceChecker(error=db_error)
    store = _StubSummaryTestResultsStore()

    # Act / Assert
    with pytest.raises(SummaryTestResultsError) as exc_info:
        get_summary_test_results(
            "rm_mid_003",
            existence_checker=checker,
            store=store,
        )

    assert exc_info.value.error_code == "persistence_failed"
    assert exc_info.value.message == "summary test results persistence failed"
    assert exc_info.value.__cause__ is db_error


def test_tc_32_store_find_db_failure_raises_persistence_error() -> None:
    # Arrange
    db_error = RuntimeError("db read failed")
    checker = _StubExistenceChecker(existing_ids={"rm_mid_004"})
    store = _StubSummaryTestResultsStore(error=db_error)

    # Act / Assert
    with pytest.raises(SummaryTestResultsError) as exc_info:
        get_summary_test_results(
            "rm_mid_004",
            existence_checker=checker,
            store=store,
        )

    assert exc_info.value.error_code == "persistence_failed"
    assert exc_info.value.message == "summary test results persistence failed"
    assert exc_info.value.__cause__ is db_error
