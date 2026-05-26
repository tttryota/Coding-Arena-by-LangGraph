"""Quiz シナリオテスト Q-1..Q-4。

Q-1, Q-3: セッションライフサイクル (graph_runner は NoOp に差替え)
Q-2: グラフ interrupt/resume (MemorySaver + Command(resume) で実 LangGraph 動作確認)
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

    def __init__(self, *, get_state_result: dict | None = None) -> None:
        self._get_state_result = get_state_result or {}

    def start_graph(self, state: object, *, thread_id: str) -> None:
        pass

    def resume_graph(self, user_input: object, *, thread_id: str) -> None:
        pass

    def retry_graph(self, *, thread_id: str) -> None:
        pass

    def get_state(self, *, thread_id: str) -> dict:
        if self._get_state_result:
            return self._get_state_result
        raise LookupError(f"No checkpoint for {thread_id}")


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


# ---------------------------------------------------------------------------
# Q-2: ユーザー入力送信 (interrupt/resume)
# ---------------------------------------------------------------------------

# LLM レスポンス定義
_QUESTION_SET_DESIGN_RESPONSE = json.dumps(
    {
        "topic_overview": "このトピックでは基礎概念を学びます。",
        "confirmation_points": [
            {
                "id": "cp-1",
                "content": "基礎概念の理解",
                "format": "knowledge",
            },
        ],
    },
    ensure_ascii=False,
)

_QUESTION_DELIVERY_RESPONSE = json.dumps(
    {
        "question_text": "TypeScriptのジェネリクスとは何ですか？",  # noqa: RUF001
        "answer_type": "textarea",
    },
    ensure_ascii=False,
)

_ANSWER_EVALUATION_RESPONSE = json.dumps(
    {
        "next_action": "complete",
        "score": 80,
        "feedback": "型パラメータの概念を理解できています。",
        "deepdive_points": [],
    },
    ensure_ascii=False,
)

_PROGRESS_UPDATE_RESPONSE = json.dumps(
    {
        "score": 80,
        "comment": "基礎概念を十分に理解しています。",
    },
    ensure_ascii=False,
)


class TestQ2UserInputSubmission:
    def test_start_then_submit_input_completes_graph(
        self,
        client: TestClient,
        integration_container: object,
        scenario_transport: ScenarioLlmTransport,
    ) -> None:
        """POST /sessions → interrupt → POST /sessions/{id}/input → グラフ完走。"""
        # Arrange: ロードマップを作成して detail item_id を取得
        detail_item_id = _create_roadmap_and_get_detail_item_id(
            client,
            scenario_transport,
        )

        # Arrange: 実 graph_runner を使う (MemorySaver 付き)
        # integration_container は各テストで新規 Container (新規 MemorySaver) が作られるため隔離される

        # Arrange: start_graph 用 LLM レスポンス (question_set_design, question_delivery)
        # set_sequential_responses はレスポンスキューを置換しカウンタをリセットする
        scenario_transport.set_sequential_responses([
            _QUESTION_SET_DESIGN_RESPONSE,
            _QUESTION_DELIVERY_RESPONSE,
        ])
        calls_before_start = scenario_transport.call_count

        # Act: セッション開始 (グラフは interrupt で一時停止)
        start_resp = client.post(
            "/sessions",
            json={"roadmap_item_id": detail_item_id},
        )
        assert start_resp.status_code == 201, start_resp.text
        session_id = start_resp.json()["session_id"]

        # Assert: start_graph で 2 ノード (question_set_design, question_delivery) が実行された
        assert scenario_transport.call_count - calls_before_start == 2

        # Arrange: resume 用 LLM レスポンス (answer_evaluation, progress_update)
        scenario_transport.set_sequential_responses([
            _ANSWER_EVALUATION_RESPONSE,
            _PROGRESS_UPDATE_RESPONSE,
        ])
        calls_before_resume = scenario_transport.call_count

        # Act: ユーザー入力送信 (グラフ resume → answer_evaluation → progress_update → END)
        input_resp = client.post(
            f"/sessions/{session_id}/input",
            json={"user_input": "型パラメータで再利用可能な型を定義できます。", "input_source": "form"},
        )
        assert input_resp.status_code == 200, input_resp.text

        # Assert: resume_graph で 2 ノード (answer_evaluation, progress_update) が実行された
        assert scenario_transport.call_count - calls_before_resume == 2

        # Assert: レスポンスボディにグラフ実行後の state が含まれる (post-run state 契約)
        input_data = input_resp.json()
        # get_state() はグラフ完走後の全フィールドを返す
        assert "session_id" in input_data
        assert "roadmap_item_id" in input_data
        assert "roadmap_item_level" in input_data
        assert "is_resumed" in input_data
        assert input_data["session_id"] == session_id
        assert input_data["roadmap_item_id"] == detail_item_id
        assert input_data["roadmap_item_level"] == "detail"
        assert input_data["is_resumed"] is True
        # post-run state 固有フィールドが含まれることを確認（退行防止）
        assert "next_action" in input_data or "input_type" in input_data

        # Assert: グラフ完走後、セッションが完了状態 (再度 start しても resume_required=False)
        # グラフ実行は不要なので NoOp に差替え
        integration_container.graph_runner = _NoOpGraphRunner()  # type: ignore[attr-defined]
        new_start_resp = client.post(
            "/sessions",
            json={"roadmap_item_id": detail_item_id},
        )
        assert new_start_resp.status_code == 201
        assert new_start_resp.json()["resume_required"] is False

    def test_submit_to_nonexistent_session_returns_error(
        self,
        client: TestClient,
        integration_container: object,
    ) -> None:
        """存在しない session_id への入力送信 → エラー。"""
        # graph_runner の None チェック (503) を通過させるため NoOp を設定
        integration_container.graph_runner = _NoOpGraphRunner()  # type: ignore[attr-defined]

        response = client.post(
            "/sessions/00000000-0000-0000-0000-000000000000/input",
            json={"user_input": "test", "input_source": "form"},
        )

        assert response.status_code == 422
        detail = response.json().get("detail", "")
        assert "00000000-0000-0000-0000-000000000000" in detail
