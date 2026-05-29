"""競プロ API エンドポイントのテスト。"""

from __future__ import annotations

from typing import Any

from fastapi.testclient import TestClient

from api.app import create_app

# ---------------------------------------------------------------------------
# Fake dependencies
# ---------------------------------------------------------------------------


class _FakeThemeReader:
    def list_themes(self) -> list[dict[str, str]]:
        return [
            {"id": "algo-001", "category": "探索", "label": "二分探索"},
            {"id": "algo-002", "category": "グラフ", "label": "DFS"},
        ]


class _FakeGraphRunner:
    def __init__(self) -> None:
        self._state: dict[str, Any] = {}

    def start_graph(
        self, state: dict[str, Any], *, thread_id: str,
    ) -> None:
        self._state = {
            **state,
            "algo_theme_id": "algo-001",
            "algo_theme_label": "二分探索",
            "algo_theme_category": "探索",
            "programming_language": "python",
            "problem_statement": "問題文",
            "input_format": "入力形式",
            "output_format": "出力形式",
            "constraints": "制約",
            "examples": [{"input": "1", "output": "2"}],
            "reference_solution": "def solve(): pass",
            "grading_rubric": [
                {"criterion": "正しさ", "points": 100, "description": "ok"},
            ],
        }

    def resume_graph(
        self, user_input: dict[str, Any], *, thread_id: str,
    ) -> None:
        self._state.update(user_input)
        self._state["status"] = "completed"
        self._state["score"] = 85
        self._state["feedback"] = "良い解答です"
        self._state["time_complexity"] = "O(log N)"
        self._state["space_complexity"] = "O(1)"
        self._state["improvement_suggestions"] = "特になし"
        self._state["rubric_scores_json"] = "[]"

    def get_state(self, *, thread_id: str) -> dict[str, Any]:
        if not self._state:
            msg = f"No checkpoint for {thread_id}"
            raise LookupError(msg)
        return self._state


class _FakeSessionRecord:
    def __init__(self, session_id: str) -> None:
        self.id = session_id


class _FakeAnswerRecord:
    def __init__(self) -> None:
        self.score = 85
        self.feedback = "良い解答です"
        self.time_complexity = "O(log N)"
        self.space_complexity = "O(1)"
        self.improvement_suggestions = "特になし"
        self.rubric_scores_json = "[]"


class _FakeCompetitiveStore:
    def __init__(self) -> None:
        self._sessions: dict[str, dict[str, Any]] = {}
        self._answer: _FakeAnswerRecord | None = None

    def create_session(self, **kwargs: Any) -> _FakeSessionRecord:
        sid = kwargs.get("session_id", "fake-id")
        self._sessions[sid] = kwargs
        return _FakeSessionRecord(sid)

    def get_session_details(self, session_id: str) -> dict[str, Any]:
        if session_id not in self._sessions:
            msg = f"CompetitiveSession not found: {session_id}"
            raise ValueError(msg)
        return {"id": session_id, **self._sessions[session_id]}

    def find_answer_by_session(
        self, session_id: str,
    ) -> _FakeAnswerRecord | None:
        return self._answer

    def save_answer_and_complete(self, **kwargs: Any) -> _FakeAnswerRecord:
        self._answer = _FakeAnswerRecord()
        return self._answer


class _FakeContainer:
    def __init__(self) -> None:
        self.algo_theme_reader = _FakeThemeReader()
        self.competitive_graph_runner = _FakeGraphRunner()
        self.competitive_store = _FakeCompetitiveStore()


def _make_client() -> TestClient:
    app = create_app()
    app.state.container = _FakeContainer()
    return TestClient(app)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestListThemes:
    def test_returns_themes(self) -> None:
        client = _make_client()
        resp = client.get("/algorithm-quiz/themes")

        assert resp.status_code == 200
        data = resp.json()
        assert len(data["themes"]) == 2
        assert data["themes"][0]["id"] == "algo-001"


class TestStartSession:
    def test_random_start(self) -> None:
        client = _make_client()
        resp = client.post("/algorithm-quiz/sessions")

        assert resp.status_code == 201
        data = resp.json()
        assert data["session_id"]
        assert data["theme_id"] == "algo-001"
        assert data["problem_statement"] == "問題文"
        assert "reference_solution" not in data

    def test_with_theme_id_passes_to_graph(self) -> None:
        client = _make_client()
        resp = client.post(
            "/algorithm-quiz/sessions",
            json={"theme_id": "algo-002"},
        )

        assert resp.status_code == 201
        data = resp.json()
        assert data["session_id"]
        assert data["theme_id"] == "algo-001"


class TestSubmitAnswer:
    def test_submit_and_get_result(self) -> None:
        client = _make_client()
        start_resp = client.post("/algorithm-quiz/sessions")
        session_id = start_resp.json()["session_id"]

        resp = client.post(
            f"/algorithm-quiz/sessions/{session_id}/answer",
            json={"user_code": "def solve(): return 42"},
        )

        assert resp.status_code == 200
        data = resp.json()
        assert data["score"] == 85
        assert data["feedback"] == "良い解答です"

    def test_empty_code_rejected(self) -> None:
        client = _make_client()
        resp = client.post(
            "/algorithm-quiz/sessions/fake-id/answer",
            json={"user_code": ""},
        )

        assert resp.status_code == 422


class TestGetSession:
    def test_returns_session_without_hidden_fields(self) -> None:
        client = _make_client()
        start_resp = client.post("/algorithm-quiz/sessions")
        session_id = start_resp.json()["session_id"]

        resp = client.get(f"/algorithm-quiz/sessions/{session_id}")

        assert resp.status_code == 200
        data = resp.json()
        assert data["session_id"] == session_id
        assert "reference_solution" not in data
        assert "grading_rubric" not in data

    def test_not_found(self) -> None:
        client = _make_client()
        resp = client.get("/algorithm-quiz/sessions/nonexistent")

        assert resp.status_code == 404

    def test_includes_answer_data_when_completed(self) -> None:
        client = _make_client()
        start_resp = client.post("/algorithm-quiz/sessions")
        session_id = start_resp.json()["session_id"]

        client.post(
            f"/algorithm-quiz/sessions/{session_id}/answer",
            json={"user_code": "def solve(): pass"},
        )

        resp = client.get(f"/algorithm-quiz/sessions/{session_id}")
        data = resp.json()
        assert data["score"] == 85
        assert data["feedback"] == "良い解答です"
