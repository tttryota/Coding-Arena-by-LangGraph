"""競プロ API エンドポイントのテスト。"""

from __future__ import annotations

from typing import Any

from fastapi.testclient import TestClient

from api.app import create_app
from competitive.domain.competitive_types import QuestionResponseError

# ---------------------------------------------------------------------------
# Fake dependencies
# ---------------------------------------------------------------------------


class _FakeThemeReader:
    def list_themes(self) -> list[dict[str, object]]:
        return [
            {
                "id": "algo-001",
                "category": "探索",
                "label": "二分探索",
                "display_order": 0,
                "attempt_count": 0,
                "best_score": None,
                "last_attempted_at": None,
            },
            {
                "id": "algo-002",
                "category": "グラフ",
                "label": "DFS",
                "display_order": 1,
                "attempt_count": 0,
                "best_score": None,
                "last_attempted_at": None,
            },
        ]

    def pick_next(self) -> dict[str, str]:
        return {"id": "algo-001", "category": "探索", "label": "二分探索"}

    def get_by_id(self, theme_id: str) -> dict[str, str]:
        return {"id": theme_id, "category": "探索", "label": "二分探索"}


class _FakeGraphRunner:
    def __init__(self) -> None:
        self._state: dict[str, Any] = {}
        self.resume_calls = 0

    def start_graph(
        self,
        state: dict[str, Any],
        *,
        thread_id: str,
    ) -> None:
        self._state = {
            **state,
            "algo_theme_id": "algo-001",
            "algo_theme_label": "二分探索",
            "algo_theme_category": "探索",
            "programming_language": state.get("programming_language", "python"),
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
        self,
        user_input: dict[str, Any],
        *,
        thread_id: str,
    ) -> None:
        self.resume_calls += 1
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
        self.theme_id = "algo-001"
        self.theme_label = "二分探索"
        self.theme_category = "探索"
        self.programming_language = "python"
        self.status = "in_progress"


class _FakeAnswerRecord:
    def __init__(self) -> None:
        self.answer_text = "def solve(): return 42"
        self.score = 85
        self.feedback = "良い解答です"
        self.time_complexity = "O(log N)"
        self.space_complexity = "O(1)"
        self.improvement_suggestions = "特になし"
        self.rubric_scores_json = "[]"


class _FakeQuestionLlm:
    def __init__(self) -> None:
        self.calls: list[dict[str, Any]] = []
        self.error: QuestionResponseError | None = None

    def generate_chat_response(self, **kwargs: Any) -> str:
        if self.error is not None:
            raise self.error
        self.calls.append(kwargs)
        return "提出前のヒントです"


class _FakeCompetitiveStore:
    def __init__(self) -> None:
        self._sessions: dict[str, dict[str, Any]] = {}
        self._answer: _FakeAnswerRecord | None = None
        self.save_answer_calls = 0

    def create_session(self, **kwargs: Any) -> _FakeSessionRecord:
        sid = kwargs.get("session_id", "fake-id")
        self._sessions[sid] = {**kwargs, "status": "in_progress"}
        return _FakeSessionRecord(sid)

    def get_session_details(self, session_id: str) -> dict[str, Any]:
        if session_id not in self._sessions:
            msg = f"CompetitiveSession not found: {session_id}"
            raise ValueError(msg)
        return {
            "id": session_id,
            "created_at": "2026-05-29T10:00:00",
            **self._sessions[session_id],
        }

    def find_answer_by_session(
        self,
        session_id: str,
    ) -> _FakeAnswerRecord | None:
        return self._answer

    def list_recent_sessions(self, *, limit: int = 50) -> list[_FakeSessionRecord]:
        return [_FakeSessionRecord(sid) for sid in self._sessions]

    def save_answer_and_complete(self, **kwargs: Any) -> _FakeAnswerRecord:
        self.save_answer_calls += 1
        self._answer = _FakeAnswerRecord()
        session = self._sessions.get(kwargs["session_id"])
        if session is not None:
            session["status"] = "completed"
        return self._answer


class _FakeContainer:
    def __init__(self) -> None:
        self.algo_theme_reader = _FakeThemeReader()
        self.competitive_graph_runner = _FakeGraphRunner()
        self.competitive_store = _FakeCompetitiveStore()
        self.competitive_question_llm = _FakeQuestionLlm()


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
        assert data["themes"][0]["display_order"] == 0
        assert data["themes"][0]["attempt_count"] == 0


class TestListLanguages:
    def test_returns_languages(self) -> None:
        client = _make_client()

        resp = client.get("/algorithm-quiz/languages")

        assert resp.status_code == 200
        data = resp.json()
        assert data["languages"][0]["id"] == "python"
        assert "editor_placeholder" in data["languages"][0]


class TestStartSession:
    def test_auto_start(self) -> None:
        client = _make_client()
        resp = client.post("/algorithm-quiz/sessions")

        assert resp.status_code == 201
        data = resp.json()
        assert data["session_id"]
        assert data["theme_id"] == "algo-001"
        assert data["problem_statement"] == "問題文"
        assert "reference_solution" not in data

    def test_with_theme_id(self) -> None:
        client = _make_client()
        resp = client.post(
            "/algorithm-quiz/sessions",
            json={"theme_id": "algo-001", "programming_language": "typescript"},
        )

        assert resp.status_code == 201
        data = resp.json()
        assert data["session_id"]
        assert data["theme_id"] == "algo-001"
        assert data["programming_language"] == "typescript"
        assert "reference_solution" not in data

    def test_rejects_unknown_language(self) -> None:
        client = _make_client()
        resp = client.post(
            "/algorithm-quiz/sessions",
            json={"programming_language": "ruby"},
        )

        assert resp.status_code == 422


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
        assert data["reference_solution"] == "def solve(): pass"

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
        assert "reference_solution" not in data

    def test_hides_reference_solution_until_completed(self) -> None:
        client = _make_client()
        start_resp = client.post("/algorithm-quiz/sessions")
        session_id = start_resp.json()["session_id"]

        resp = client.get(f"/algorithm-quiz/sessions/{session_id}")

        assert resp.status_code == 200
        assert "reference_solution" not in resp.json()


class TestListSessions:
    def test_returns_sessions_with_created_at(self) -> None:
        client = _make_client()
        client.post("/algorithm-quiz/sessions")

        resp = client.get("/algorithm-quiz/sessions")

        assert resp.status_code == 200
        data = resp.json()
        assert len(data["sessions"]) == 1
        assert data["sessions"][0]["session_id"]
        assert data["sessions"][0]["created_at"] == "2026-05-29T10:00:00"

    def test_empty_when_no_sessions(self) -> None:
        client = _make_client()
        resp = client.get("/algorithm-quiz/sessions")

        assert resp.status_code == 200
        data = resp.json()
        assert data["sessions"] == []


class TestAskQuestion:
    def test_returns_hint_without_submitting_answer(self) -> None:
        client = _make_client()
        start_resp = client.post("/algorithm-quiz/sessions")
        session_id = start_resp.json()["session_id"]
        container = client.app.state.container

        resp = client.post(
            f"/algorithm-quiz/sessions/{session_id}/question",
            json={
                "user_input": "どこから考えればいい？",
                "history": [{"role": "user", "content": "制約が重い？"}],
            },
        )

        assert resp.status_code == 200
        assert resp.json()["chat_response_text"] == "提出前のヒントです"
        assert container.competitive_store.save_answer_calls == 0
        assert container.competitive_graph_runner.resume_calls == 0
        assert container.competitive_store.get_session_details(session_id)[
            "status"
        ] == ("in_progress")
        assert "reference_solution" not in container.competitive_question_llm.calls[0]

    def test_returns_409_when_session_completed(self) -> None:
        client = _make_client()
        start_resp = client.post("/algorithm-quiz/sessions")
        session_id = start_resp.json()["session_id"]
        client.post(
            f"/algorithm-quiz/sessions/{session_id}/answer",
            json={"user_code": "def solve(): return 42"},
        )

        resp = client.post(
            f"/algorithm-quiz/sessions/{session_id}/question",
            json={"user_input": "どこが違う？", "history": []},
        )

        assert resp.status_code == 409

    def test_returns_404_for_unknown_session(self) -> None:
        client = _make_client()

        resp = client.post(
            "/algorithm-quiz/sessions/00000000-0000-0000-0000-000000000000/question",
            json={"user_input": "ヒントください", "history": []},
        )

        assert resp.status_code == 404

    def test_returns_503_for_transient_llm_failure(self) -> None:
        client = _make_client()
        start_resp = client.post("/algorithm-quiz/sessions")
        session_id = start_resp.json()["session_id"]
        client.app.state.container.competitive_question_llm.error = (
            QuestionResponseError(
                error_code="llm_request_failed",
                message="temporary upstream failure",
            )
        )

        resp = client.post(
            f"/algorithm-quiz/sessions/{session_id}/question",
            json={"user_input": "ヒントください", "history": []},
        )

        assert resp.status_code == 503

    def test_returns_502_for_llm_parse_failure(self) -> None:
        client = _make_client()
        start_resp = client.post("/algorithm-quiz/sessions")
        session_id = start_resp.json()["session_id"]
        client.app.state.container.competitive_question_llm.error = (
            QuestionResponseError(
                error_code="llm_response_parse_failed",
                message="invalid structured output",
            )
        )

        resp = client.post(
            f"/algorithm-quiz/sessions/{session_id}/question",
            json={"user_input": "ヒントください", "history": []},
        )

        assert resp.status_code == 502
