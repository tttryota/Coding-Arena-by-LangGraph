"""Roadmap シナリオテスト R-1..R-6。

TestClient → FastAPI Router → Application 層 → 実 Infrastructure (SQLite + ChromaDB)
LLM は ScenarioLlmTransport でスタブ。
"""

from __future__ import annotations

import json
import time
from typing import TYPE_CHECKING
from uuid import uuid4

if TYPE_CHECKING:
    from fastapi.testclient import TestClient

    from tests.integration.stubs.scenario_llm_transport import ScenarioLlmTransport

VALID_ROADMAP_JSON = json.dumps(
    {
        "topic": "TypeScript",
        "items": [
            {
                "title": "基礎",
                "description": "TypeScript の基礎概念",
                "level": "major",
                "children": [
                    {
                        "title": "型システム",
                        "description": "型の基本",
                        "level": "middle",
                        "children": [
                            {
                                "title": "プリミティブ型",
                                "description": "string, number, boolean",
                                "level": "detail",
                                "children": [],
                            },
                        ],
                    },
                ],
            },
            {
                "title": "応用",
                "description": "TypeScript の応用技術",
                "level": "major",
                "children": [
                    {
                        "title": "ジェネリクス",
                        "description": "ジェネリクスの活用",
                        "level": "middle",
                        "children": [
                            {
                                "title": "条件型",
                                "description": "Conditional Types",
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


def _poll_job_until_terminal(
    client: TestClient,
    job_id: str,
    *,
    max_wait: float = 5.0,
    interval: float = 0.1,
) -> dict:
    """ジョブが terminal 状態になるまでポーリングする。"""
    deadline = time.monotonic() + max_wait
    while time.monotonic() < deadline:
        resp = client.get(f"/roadmaps/generate/{job_id}")
        assert resp.status_code == 200
        data = resp.json()
        if data["status"] in ("completed", "failed"):
            return data
        time.sleep(interval)
    msg = f"Job {job_id} did not reach terminal state within {max_wait}s"
    raise TimeoutError(msg)


def _generate_roadmap(
    client: TestClient,
    scenario_transport: ScenarioLlmTransport,
    topic: str = "TypeScript",
) -> str:
    """ロードマップを生成して roadmap_id を返すヘルパー。"""
    scenario_transport.set_sequential_responses([VALID_ROADMAP_JSON])

    resp = client.post("/roadmaps/generate", json={"topic": topic})
    assert resp.status_code == 202
    job_id = resp.json()["job_id"]

    job_data = _poll_job_until_terminal(client, job_id)
    assert job_data["status"] == "completed"
    return job_data["roadmap_id"]


# ---------------------------------------------------------------------------
# R-5: 空トピック拒否
# ---------------------------------------------------------------------------


class TestR5EmptyTopicRejection:
    def test_returns_422_for_empty_topic(self, client: TestClient) -> None:
        response = client.post("/roadmaps/generate", json={"topic": ""})

        assert response.status_code == 422


# ---------------------------------------------------------------------------
# R-6: 存在しないロードマップ
# ---------------------------------------------------------------------------


class TestR6NonExistentRoadmap:
    def test_returns_404_for_random_uuid(self, client: TestClient) -> None:
        response = client.get(f"/roadmaps/{uuid4()}")

        assert response.status_code == 404


# ---------------------------------------------------------------------------
# R-1: ロードマップ生成 E2E
# ---------------------------------------------------------------------------


class TestR1RoadmapGenerationE2E:
    def test_generate_poll_and_retrieve_tree(
        self,
        client: TestClient,
        scenario_transport: ScenarioLlmTransport,
    ) -> None:
        # Arrange
        scenario_transport.set_sequential_responses([VALID_ROADMAP_JSON])

        # Act: POST /generate
        gen_resp = client.post(
            "/roadmaps/generate",
            json={"topic": "TypeScript"},
        )
        assert gen_resp.status_code == 202
        job_id = gen_resp.json()["job_id"]
        assert gen_resp.json()["status"] == "queued"

        # Act: Poll until completed
        job_data = _poll_job_until_terminal(client, job_id)
        assert job_data["status"] == "completed"
        roadmap_id = job_data["roadmap_id"]

        # Act: GET /{roadmap_id}
        get_resp = client.get(f"/roadmaps/{roadmap_id}")
        assert get_resp.status_code == 200
        tree = get_resp.json()

        # Assert: ツリー構造
        assert tree["topic"] == "TypeScript"
        items = tree["items"]
        assert len(items) == 2
        assert items[0]["title"] == "基礎"
        assert items[0]["level"] == "major"
        assert items[1]["title"] == "応用"
        assert items[1]["level"] == "major"

        # Assert: 子ノード (middle -> detail)
        kiso_children = items[0]["children"]
        assert len(kiso_children) == 1
        assert kiso_children[0]["title"] == "型システム"
        assert kiso_children[0]["level"] == "middle"

        detail_children = kiso_children[0]["children"]
        assert len(detail_children) == 1
        assert detail_children[0]["title"] == "プリミティブ型"
        assert detail_children[0]["level"] == "detail"

    def test_roadmap_appears_in_list(
        self,
        client: TestClient,
        scenario_transport: ScenarioLlmTransport,
    ) -> None:
        roadmap_id = _generate_roadmap(client, scenario_transport)

        list_resp = client.get("/roadmaps")
        assert list_resp.status_code == 200
        data = list_resp.json()
        assert data["total_count"] >= 1
        roadmap_ids = [item["roadmap_id"] for item in data["items"]]
        assert roadmap_id in roadmap_ids


# ---------------------------------------------------------------------------
# R-2: アイテム追加 + 削除
# ---------------------------------------------------------------------------


class TestR2ItemAddAndDelete:
    def test_add_middle_then_detail_then_delete_detail(
        self,
        client: TestClient,
        scenario_transport: ScenarioLlmTransport,
    ) -> None:
        roadmap_id = _generate_roadmap(client, scenario_transport)

        # 既存ツリーから major の id を取得
        tree = client.get(f"/roadmaps/{roadmap_id}").json()
        major_id = tree["items"][0]["id"]

        # Act: middle 追加
        add_middle_resp = client.post(
            f"/roadmaps/{roadmap_id}/items",
            json={
                "parent_id": major_id,
                "title": "追加 middle",
                "description": "新しい middle",
            },
        )
        assert add_middle_resp.status_code == 201
        middle_id = add_middle_resp.json()["created_item"]["id"]

        # Act: detail 追加
        add_detail_resp = client.post(
            f"/roadmaps/{roadmap_id}/items",
            json={
                "parent_id": middle_id,
                "title": "追加 detail",
                "description": "新しい detail",
            },
        )
        assert add_detail_resp.status_code == 201
        detail_id = add_detail_resp.json()["created_item"]["id"]

        # Assert: ツリーに追加されている (middle + detail)
        tree_after_add = client.get(f"/roadmaps/{roadmap_id}").json()
        kiso = tree_after_add["items"][0]
        added_middle = next(c for c in kiso["children"] if c["title"] == "追加 middle")
        assert added_middle["level"] == "middle"
        assert len(added_middle["children"]) == 1
        assert added_middle["children"][0]["title"] == "追加 detail"
        assert added_middle["children"][0]["level"] == "detail"
        assert added_middle["children"][0]["id"] == detail_id

        # Act: detail 削除
        del_resp = client.delete(
            f"/roadmaps/{roadmap_id}/items/{detail_id}",
        )
        assert del_resp.status_code == 200
        assert del_resp.json()["deleted_count"] == 1

        # Assert: 削除後 detail は消え、middle は残る
        tree_after_del = client.get(f"/roadmaps/{roadmap_id}").json()
        added_middle_after = next(
            c
            for c in tree_after_del["items"][0]["children"]
            if c["title"] == "追加 middle"
        )
        assert len(added_middle_after["children"]) == 0
        assert added_middle_after["id"] == middle_id


# ---------------------------------------------------------------------------
# R-3: アイテム移動
# ---------------------------------------------------------------------------


class TestR3ItemMove:
    def test_move_detail_to_another_parent(
        self,
        client: TestClient,
        scenario_transport: ScenarioLlmTransport,
    ) -> None:
        roadmap_id = _generate_roadmap(client, scenario_transport)

        tree = client.get(f"/roadmaps/{roadmap_id}").json()
        # 基礎 → 型システム → プリミティブ型
        kiso = tree["items"][0]
        ouyou = tree["items"][1]
        detail_id = kiso["children"][0]["children"][0]["id"]
        target_parent_id = ouyou["children"][0]["id"]  # ジェネリクス(middle)

        # Act: detail を応用/ジェネリクス配下に移動
        move_resp = client.put(
            f"/roadmaps/{roadmap_id}/items/{detail_id}/move",
            json={
                "target_parent_id": target_parent_id,
                "target_order": 0,
            },
        )
        assert move_resp.status_code == 200

        # Assert: 移動後のツリー構造
        tree_after = client.get(f"/roadmaps/{roadmap_id}").json()
        kiso_after = tree_after["items"][0]
        ouyou_after = tree_after["items"][1]

        # 元の親の子から消えている
        kiso_detail_titles = [c["title"] for c in kiso_after["children"][0]["children"]]
        assert "プリミティブ型" not in kiso_detail_titles

        # 新しい親の子に追加されている + level/order 検証
        ouyou_details = ouyou_after["children"][0]["children"]
        moved_node = next(c for c in ouyou_details if c["title"] == "プリミティブ型")
        assert moved_node["level"] == "detail"
        assert moved_node["order"] == 0


# ---------------------------------------------------------------------------
# R-4: LLM リトライ + 失敗
# ---------------------------------------------------------------------------


class TestR4LlmRetryAndFailure:
    def test_first_invalid_then_success(
        self,
        client: TestClient,
        scenario_transport: ScenarioLlmTransport,
    ) -> None:
        """1回目 invalid JSON → 2回目成功。"""
        scenario_transport.set_sequential_responses(
            [
                "this is not valid json",
                VALID_ROADMAP_JSON,
            ],
        )

        resp = client.post(
            "/roadmaps/generate",
            json={"topic": "TypeScript"},
        )
        assert resp.status_code == 202
        job_id = resp.json()["job_id"]

        job_data = _poll_job_until_terminal(client, job_id)
        assert job_data["status"] == "completed"

        # LLM は 2 回呼ばれた
        assert scenario_transport.call_count == 2

    def test_all_three_fail(
        self,
        client: TestClient,
        scenario_transport: ScenarioLlmTransport,
    ) -> None:
        """3回全失敗 → failed ジョブ。"""
        scenario_transport.set_sequential_responses(
            [
                "invalid 1",
                "invalid 2",
                "invalid 3",
            ],
        )

        resp = client.post(
            "/roadmaps/generate",
            json={"topic": "TypeScript"},
        )
        assert resp.status_code == 202
        job_id = resp.json()["job_id"]

        job_data = _poll_job_until_terminal(client, job_id)
        assert job_data["status"] == "failed"
        assert "error_code" in job_data
        assert scenario_transport.call_count == 3
