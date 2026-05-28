"""Feedback シナリオテスト F-1..F-3。

TestClient → FastAPI Router → Application 層 → 実 Infrastructure (SQLite)
"""

from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import uuid4

if TYPE_CHECKING:
    from fastapi.testclient import TestClient


def _seed_feedbacks(container: object) -> list[str]:
    """3件のフィードバックを作成して ID のリストを返す。

    - FB-0: 2026-05-20, unread
    - FB-1: 2026-05-21, read
    - FB-2: 2026-05-22, unread
    """
    from ingestion.domain.ingestion_feedback_types import NewIngestionFeedbackRecord

    store = container.ingestion_feedback_store  # type: ignore[attr-defined]
    ids = []
    for i in range(3):
        record = NewIngestionFeedbackRecord(
            source_path=f"notes/file{i}.md",
            roadmap_item_id=None,
            title=f"Feedback {i}",
            body=f"Body {i}",
            is_read=i == 1,
            created_at=f"2026-05-{20 + i:02d}T00:00:00+00:00",
            read_at="2026-05-21T01:00:00+00:00" if i == 1 else None,
        )
        stored = store.create(record)
        ids.append(str(stored.id))
    return ids


# ---------------------------------------------------------------------------
# F-1: フィードバック一覧 → 既読 → 再取得
# ---------------------------------------------------------------------------


class TestF1FeedbackListAndMarkRead:
    def test_list_then_mark_read_then_filter_unread(
        self,
        client: TestClient,
        integration_container: object,
    ) -> None:
        """テスト対象: F1FeedbackListAndMarkRead の処理。
        テストケース: 個別条件での処理を検証する。
        期待結果: 想定どおりの処理結果が得られる。"""
        ids = _seed_feedbacks(integration_container)

        # Act: 全件取得
        list_resp = client.get("/ingestion/feedbacks")
        assert list_resp.status_code == 200
        data = list_resp.json()
        assert data["total_count"] == 3

        # Act: FB-0 (unread) を既読にする
        mark_resp = client.put(f"/ingestion/feedbacks/{ids[0]}/read")
        assert mark_resp.status_code == 200
        marked = mark_resp.json()
        assert marked["is_read"] is True
        assert marked["read_at"] is not None

        # Act: unread のみ再取得
        unread_resp = client.get(
            "/ingestion/feedbacks",
            params={"read_status": "unread"},
        )
        assert unread_resp.status_code == 200
        unread_data = unread_resp.json()

        # Assert: FB-0 は既読なので除外、FB-2 のみ残る
        assert unread_data["total_count"] == 1
        assert unread_data["items"][0]["id"] == ids[2]


# ---------------------------------------------------------------------------
# F-2: 日付範囲フィルタ
# ---------------------------------------------------------------------------


class TestF2DateRangeFilter:
    def test_date_from_excludes_earlier(
        self,
        client: TestClient,
        integration_container: object,
    ) -> None:
        """テスト対象: F2DateRangeFilter の処理。
        テストケース: 個別条件での処理を検証する。
        期待結果: 想定どおりの処理結果が得られる。"""
        ids = _seed_feedbacks(integration_container)

        resp = client.get(
            "/ingestion/feedbacks",
            params={"date_from": "2026-05-21T00:00:00+00:00"},
        )
        assert resp.status_code == 200
        data = resp.json()
        # FB-0 (5/20) は除外、FB-1 (5/21) と FB-2 (5/22) が残る
        assert data["total_count"] == 2
        returned_ids = {item["id"] for item in data["items"]}
        assert ids[0] not in returned_ids
        assert ids[1] in returned_ids
        assert ids[2] in returned_ids

    def test_date_to_excludes_later(
        self,
        client: TestClient,
        integration_container: object,
    ) -> None:
        """テスト対象: F2DateRangeFilter の処理。
        テストケース: 個別条件での処理を検証する。
        期待結果: 想定どおりの処理結果が得られる。"""
        ids = _seed_feedbacks(integration_container)

        resp = client.get(
            "/ingestion/feedbacks",
            params={"date_to": "2026-05-20T23:59:59+00:00"},
        )
        assert resp.status_code == 200
        data = resp.json()
        # FB-0 (5/20) のみ
        assert data["total_count"] == 1
        assert data["items"][0]["id"] == ids[0]

    def test_date_range_boundary(
        self,
        client: TestClient,
        integration_container: object,
    ) -> None:
        """テスト対象: F2DateRangeFilter の処理。
        テストケース: 個別条件での処理を検証する。
        期待結果: 想定どおりの処理結果が得られる。"""
        _seed_feedbacks(integration_container)

        resp = client.get(
            "/ingestion/feedbacks",
            params={
                "date_from": "2026-05-21T00:00:00+00:00",
                "date_to": "2026-05-21T23:59:59+00:00",
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        # FB-1 (5/21) のみ
        assert data["total_count"] == 1
        assert data["items"][0]["title"] == "Feedback 1"


# ---------------------------------------------------------------------------
# F-3: 存在しないフィードバック既読
# ---------------------------------------------------------------------------


class TestF3NonExistentFeedbackRead:
    def test_returns_404_for_random_uuid(self, client: TestClient) -> None:
        """テスト対象: F3NonExistentFeedbackRead の処理。
        テストケース: 個別条件での処理を検証する。
        期待結果: 想定どおりの処理結果が得られる。"""
        response = client.put(f"/ingestion/feedbacks/{uuid4()}/read")

        assert response.status_code == 404
