"""Quiz シナリオテスト Q-1..Q-4。

Q-1, Q-3: セッションライフサイクル (graph_runner は NoOp に差替え)
Q-2: グラフ resume (checkpointer 未対応のため制約あり)
Q-4: 存在しない item_id → エラー
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from fastapi.testclient import TestClient

    from tests.integration.stubs.scenario_llm_transport import ScenarioLlmTransport

VALID_ROADMAP_JSON = json.dumps(
    {
        "topic": "QuizTest",
        "items": [
            {
                "title": "基礎",
                "description": "基礎概念",
                "level": "major",
                "children": [
                    {
                        "title": "中項目",
                        "description": "中項目の説明",
                        "level": "middle",
                        "children": [
                            {
                                "title": "詳細項目",
                                "description": "詳細の説明",
                                "level": "detail",
                                "children": [],
                            },
                        ],
                    },
                ],
            },
            {
                "title": "応用",
                "description": "応用技術",
                "level": "major",
                "children": [
                    {
                        "title": "応用中項目",
                        "description": "応用の説明",
                        "level": "middle",
                        "children": [
                            {
                                "title": "応用詳細",
                                "description": "応用詳細の説明",
                                "level": "detail",
                                "children": [],
                            },
                        ],
                    },
                ],
            },
        ],
    },
    ensure_ascii=False,
)


class _NoOpGraphRunner:
    """テスト用: start_graph / resume_graph を no-op にする。"""

    def start_graph(self, state: object) -> None:
        pass

    def resume_graph(self, state: object) -> None:
        pass


def _create_roadmap_and_get_detail_item_id(
    client: TestClient,
    scenario_transport: ScenarioLlmTransport,
) -> str:
    """ロードマップを生成して detail アイテムの ID を返す。"""
    import time

    scenario_transport.set_sequential_responses([VALID_ROADMAP_JSON])
    resp = client.post("/roadmaps/generate", json={"topic": "QuizTest"})
    job_id = resp.json()["job_id"]

    deadline = time.monotonic() + 5.0
    while time.monotonic() < deadline:
        job = client.get(f"/roadmaps/generate/{job_id}").json()
        if job["status"] in ("completed", "failed"):
            break
        time.sleep(0.1)

    tree = client.get(f"/roadmaps/{job['roadmap_id']}").json()
    # 基礎 → 中項目 → 詳細項目
    return tree["items"][0]["children"][0]["children"][0]["id"]


# ---------------------------------------------------------------------------
# Q-4: 存在しない item_id
# ---------------------------------------------------------------------------


class TestQ4NonExistentItemId:
    def test_returns_error_for_missing_item(
        self,
        client: TestClient,
        integration_container: object,
    ) -> None:
        """存在しない roadmap_item_id でセッション開始 → エラー。"""
        # graph_runner を NoOp に差替え (item 検索で失敗するため graph は到達しないが安全のため)
        integration_container.graph_runner = _NoOpGraphRunner()  # type: ignore[attr-defined]

        response = client.post(
            "/sessions",
            json={"roadmap_item_id": "nonexistent-item-id"},
        )

        # item が見つからないため start_session 内でエラー → 422
        assert response.status_code == 422


# ---------------------------------------------------------------------------
# Q-1: セッション開始 → 取得
# ---------------------------------------------------------------------------


class TestQ1SessionStartAndGet:
    def test_start_session_and_retrieve(
        self,
        client: TestClient,
        integration_container: object,
        scenario_transport: ScenarioLlmTransport,
    ) -> None:
        """POST /sessions → 201 → GET /sessions/{id} で DB 行確認。"""
        # Arrange: ロードマップを作成して detail item_id を取得
        detail_item_id = _create_roadmap_and_get_detail_item_id(
            client,
            scenario_transport,
        )

        # Arrange: graph_runner を NoOp に差替え
        integration_container.graph_runner = _NoOpGraphRunner()  # type: ignore[attr-defined]

        # Act: セッション開始
        start_resp = client.post(
            "/sessions",
            json={"roadmap_item_id": detail_item_id},
        )
        assert start_resp.status_code == 201
        start_data = start_resp.json()
        session_id = start_data["session_id"]
        assert start_data["resume_required"] is False
        assert start_data["resume_session_id"] is None

        # Act: セッション取得
        get_resp = client.get(f"/sessions/{session_id}")
        assert get_resp.status_code == 200
        get_data = get_resp.json()
        assert get_data["session_id"] == session_id
        # DB 行の存在を session オブジェクトの存在で確認
        assert get_data["session"] is not None


# ---------------------------------------------------------------------------
# Q-3: 既存セッション検出
# ---------------------------------------------------------------------------


class TestQ3ExistingSessionDetection:
    def test_second_start_returns_resume_required(
        self,
        client: TestClient,
        integration_container: object,
        scenario_transport: ScenarioLlmTransport,
    ) -> None:
        """同一 item_id で 2 回 POST → resume_required=True。"""
        detail_item_id = _create_roadmap_and_get_detail_item_id(
            client,
            scenario_transport,
        )
        integration_container.graph_runner = _NoOpGraphRunner()  # type: ignore[attr-defined]

        # Act: 1回目
        first_resp = client.post(
            "/sessions",
            json={"roadmap_item_id": detail_item_id},
        )
        assert first_resp.status_code == 201
        first_session_id = first_resp.json()["session_id"]

        # Act: 2回目 (同じ item_id)
        second_resp = client.post(
            "/sessions",
            json={"roadmap_item_id": detail_item_id},
        )
        assert second_resp.status_code == 201
        second_data = second_resp.json()
        assert second_data["resume_required"] is True
        assert second_data["resume_session_id"] == first_session_id
