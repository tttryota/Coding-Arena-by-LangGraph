from __future__ import annotations

from quiz.application.summary_test_results_types import (
    RoadmapItemExistenceChecker,
    SummaryTestResultRecord,
    SummaryTestResultsError,
    SummaryTestResultsNotFoundError,
    SummaryTestResultsStore,
)


def get_summary_test_results(
    roadmap_item_id: str,
    *,
    existence_checker: RoadmapItemExistenceChecker,
    store: SummaryTestResultsStore,
) -> list[SummaryTestResultRecord]:
    """まとめテスト結果の履歴をロードマップ項目 ID で取得する。"""
    try:
        exists = existence_checker.item_exists(roadmap_item_id)
    except Exception as exception:
        raise SummaryTestResultsError(
            error_code="persistence_failed",
            message="summary test results persistence failed",
        ) from exception

    if not exists:
        raise SummaryTestResultsNotFoundError(
            error_code="item_not_found",
            message="roadmap item not found",
        )

    try:
        return store.find_by_roadmap_item(roadmap_item_id)
    except Exception as exception:
        raise SummaryTestResultsError(
            error_code="persistence_failed",
            message="summary test results persistence failed",
        ) from exception


__all__ = [
    "get_summary_test_results",
]
