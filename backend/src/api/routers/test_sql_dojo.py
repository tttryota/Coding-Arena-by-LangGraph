"""SQL道場 API エンドポイントのテスト。"""

from __future__ import annotations

import json
from typing import Any

from fastapi.testclient import TestClient

from api.app import create_app
from sql_dojo.domain.sql_dojo_types import (
    SqlDojoGenerationError,
    SqlDojoQuestionError,
)


class _FakeSqlThemeBank:
    def list_catalog(self) -> dict[str, object]:
        return {
            "difficulties": ["beginner", "intermediate", "advanced"],
            "themes": [
                {
                    "family": "join-basics",
                    "difficulty": "beginner",
                    "business_domain": "EC",
                    "target_skill": "JOIN",
                    "title": "顧客別注文件数",
                    "variant_count": 3,
                    "attempt_count": 0,
                    "best_score": None,
                    "last_attempted_at": None,
                    "topics": [
                        {
                            "topic_id": "join-basics-shipped-orders",
                            "topic_title": "shipped注文件数",
                            "family": "join-basics",
                            "difficulty": "beginner",
                            "business_domain": "EC",
                            "target_skill": "JOIN",
                            "attempt_count": 0,
                            "best_score": None,
                            "last_attempted_at": None,
                        },
                    ],
                },
            ],
        }

    def create_problem(
        self,
        *,
        difficulty: str,
        theme_family: str | None = None,
        topic_id: str | None = None,
    ) -> dict[str, object]:
        if topic_id == "missing-topic":
            raise SqlDojoGenerationError(
                error_code="topic_not_found",
                message="No SQL dojo topic for topic_id='missing-topic'",
            )
        if topic_id is not None:
            return {
                "family": "join-basics",
                "topic_id": topic_id,
                "topic_title": "shipped注文件数",
                "difficulty": "beginner",
                "dialect": "postgresql",
                "theme_title": "顧客別注文件数",
                "business_domain": "EC",
                "target_skill": "JOIN",
                "problem_statement": "問題文",
                "schema_markdown": "schema",
                "sample_data_json": '[{"table":"customers","rows":10}]',
                "expected_focus": "JOIN, COUNT",
                "allow_multiple_statements": False,
                "reference_sql": "SELECT 1",
                "grading_contract": {
                    "statement_kind": "select",
                    "required_tables": ["customers"],
                },
            }
        if theme_family == "plan-reading":
            return {
                "family": "plan-reading",
                "topic_id": "plan-reading-events-account-created-at",
                "topic_title": "events検索の実行計画",
                "difficulty": difficulty,
                "dialect": "postgresql",
                "theme_title": "実行計画を確認する SQL を書く",
                "business_domain": "Marketplace",
                "target_skill": "EXPLAIN",
                "problem_statement": "実行計画を確認してください",
                "schema_markdown": "events(id bigint, account_id bigint, created_at timestamptz)",
                "sample_data_json": '[{"table":"events","rows":8200000}]',
                "expected_focus": "EXPLAIN ANALYZE, BUFFERS",
                "allow_multiple_statements": False,
                "reference_sql": (
                    "EXPLAIN (ANALYZE, BUFFERS) "
                    "SELECT * FROM events "
                    "WHERE account_id = 42 AND created_at >= DATE '2026-06-01'"
                ),
                "grading_contract": {
                    "statement_kind": "explain",
                    "required_tables": ["events"],
                    "required_predicate_columns": ["account_id", "created_at"],
                    "require_explain": True,
                    "required_explain_options": ["ANALYZE", "BUFFERS"],
                },
            }
        return {
            "family": theme_family or "join-basics",
            "topic_id": "join-basics-shipped-orders",
            "topic_title": "shipped注文件数",
            "difficulty": difficulty,
            "dialect": "postgresql",
            "theme_title": "顧客別注文件数",
            "business_domain": "EC",
            "target_skill": "JOIN",
            "problem_statement": "問題文",
            "schema_markdown": "schema",
            "sample_data_json": '[{"table":"customers","rows":10}]',
            "expected_focus": "JOIN, COUNT",
            "allow_multiple_statements": False,
            "reference_sql": "SELECT 1",
            "grading_contract": {
                "statement_kind": "select",
                "required_tables": ["customers"],
            },
        }


class _FakeSqlDojoFeedbackLlm:
    def __init__(self) -> None:
        self.calls: list[dict[str, Any]] = []

    def generate_feedback(self, **kwargs: Any) -> dict[str, str]:
        self.calls.append(kwargs)
        return {
            "feedback": "良い観点です",
            "improvement_suggestions": "JOIN 条件を確認してください",
        }


class _FakeSqlDojoQuestionLlm:
    def __init__(self) -> None:
        self.error: SqlDojoQuestionError | None = None

    def generate_chat_response(self, **kwargs: Any) -> str:
        if self.error is not None:
            raise self.error
        return "まず必要なテーブルを洗い出してください"


class _FakeSqlDojoAnswerRecord:
    def __init__(self) -> None:
        self.session_id = "sess-1"
        self.answer_text = "SELECT 1"
        self.score = 80
        self.feedback = "良い観点です"
        self.rule_breakdown_json = "[]"
        self.improvement_suggestions = "JOIN 条件を確認してください"


class _FakeSqlDojoStore:
    def __init__(self) -> None:
        self.sessions: dict[str, dict[str, object]] = {}
        self.answer: _FakeSqlDojoAnswerRecord | None = None

    def create_session(self, **kwargs: Any) -> None:
        self.sessions[kwargs["session_id"]] = {
            **kwargs,
            "status": "in_progress",
            "created_at": "2026-06-19T00:00:00+09:00",
        }

    def get_session_details(self, session_id: str) -> dict[str, object]:
        if session_id not in self.sessions:
            msg = f"SqlDojoSession not found: {session_id}"
            raise ValueError(msg)
        session = self.sessions[session_id]
        return {"session_id": session_id, **session}

    def list_recent_sessions(self, *, limit: int = 50) -> list[object]:
        return [
            type(
                "Row",
                (),
                {
                    "id": session_id,
                    "theme_family": str(session["theme_family"]),
                    "topic_id": session.get("topic_id"),
                    "topic_title": session.get("topic_title"),
                    "difficulty": str(session["difficulty"]),
                    "dialect": str(session["dialect"]),
                    "theme_title": str(session["theme_title"]),
                    "status": str(session["status"]),
                },
            )()
            for session_id, session in self.sessions.items()
        ]

    def list_theme_history(self) -> list[object]:
        return [
            type(
                "ThemeHistoryRow",
                (),
                {
                    "theme_family": "join-basics",
                    "attempt_count": 2,
                    "best_score": 91,
                    "last_attempted_at": "2026-06-21T00:00:00+09:00",
                },
            )(),
        ]

    def list_topic_history(self) -> list[object]:
        return [
            type(
                "TopicHistoryRow",
                (),
                {
                    "topic_id": "join-basics-shipped-orders",
                    "attempt_count": 1,
                    "best_score": 88,
                    "last_attempted_at": "2026-06-20T00:00:00+09:00",
                },
            )(),
        ]

    def find_answer_by_session(self, session_id: str) -> _FakeSqlDojoAnswerRecord | None:
        return self.answer

    def save_answer_and_complete(self, **kwargs: Any) -> _FakeSqlDojoAnswerRecord:
        self.answer = _FakeSqlDojoAnswerRecord()
        self.sessions[kwargs["session_id"]]["status"] = "completed"
        return self.answer

    @staticmethod
    def grading_contract_as_dict(details: dict[str, object]) -> dict[str, object]:
        return json.loads(str(details["grading_contract_json"]))


class _FakeContainer:
    def __init__(self) -> None:
        self.sql_theme_bank = _FakeSqlThemeBank()
        self.sql_dojo_store = _FakeSqlDojoStore()
        self.sql_dojo_feedback_llm = _FakeSqlDojoFeedbackLlm()
        self.sql_dojo_question_llm = _FakeSqlDojoQuestionLlm()


def _make_client() -> TestClient:
    app = create_app()
    app.state.container = _FakeContainer()
    return TestClient(app)


class TestCatalog:
    def test_returns_catalog(self) -> None:
        client = _make_client()
        resp = client.get("/sql-dojo/catalog")

        assert resp.status_code == 200
        data = resp.json()
        assert data["difficulties"] == [
            "beginner",
            "intermediate",
            "advanced",
        ]
        assert data["themes"][0]["attempt_count"] == 2
        assert data["themes"][0]["best_score"] == 91
        assert data["themes"][0]["topics"][0]["topic_id"] == (
            "join-basics-shipped-orders"
        )
        assert data["themes"][0]["topics"][0]["attempt_count"] == 1
        assert data["themes"][0]["topics"][0]["best_score"] == 88


class TestStartSession:
    def test_creates_session(self) -> None:
        client = _make_client()
        resp = client.post(
            "/sql-dojo/sessions",
            json={"difficulty": "beginner", "theme_family": "join-basics"},
        )

        assert resp.status_code == 201
        data = resp.json()
        assert data["dialect"] == "postgresql"
        assert data["theme_family"] == "join-basics"
        assert data["topic_id"] == "join-basics-shipped-orders"
        assert data["topic_title"] == "shipped注文件数"
        assert "reference_sql" not in data
        assert data["allow_multiple_statements"] is False

    def test_creates_session_for_topic(self) -> None:
        client = _make_client()
        resp = client.post(
            "/sql-dojo/sessions",
            json={"topic_id": "join-basics-shipped-orders"},
        )

        assert resp.status_code == 201
        data = resp.json()
        assert data["difficulty"] == "beginner"
        assert data["theme_family"] == "join-basics"
        assert data["topic_id"] == "join-basics-shipped-orders"
        assert data["topic_title"] == "shipped注文件数"
        assert data["allow_multiple_statements"] is False

    def test_rejects_unknown_topic(self) -> None:
        client = _make_client()
        resp = client.post(
            "/sql-dojo/sessions",
            json={"topic_id": "missing-topic"},
        )

        assert resp.status_code == 422

    def test_rejects_topic_with_mismatched_difficulty(self) -> None:
        client = _make_client()
        resp = client.post(
            "/sql-dojo/sessions",
            json={
                "difficulty": "advanced",
                "topic_id": "join-basics-shipped-orders",
            },
        )

        assert resp.status_code == 422

    def test_rejects_topic_with_mismatched_theme_family(self) -> None:
        client = _make_client()
        resp = client.post(
            "/sql-dojo/sessions",
            json={
                "theme_family": "window-ranking",
                "topic_id": "join-basics-shipped-orders",
            },
        )

        assert resp.status_code == 422


class TestSubmitAnswer:
    def test_submits_answer(self) -> None:
        client = _make_client()
        session_id = client.post("/sql-dojo/sessions", json={}).json()["session_id"]

        resp = client.post(
            f"/sql-dojo/sessions/{session_id}/answer",
            json={"user_sql": "SELECT * FROM customers"},
        )

        assert resp.status_code == 200
        data = resp.json()
        assert data["score"] >= 0
        assert data["reference_sql"] == "SELECT 1"

    def test_rejects_empty_sql(self) -> None:
        client = _make_client()

        resp = client.post(
            "/sql-dojo/sessions/sess-1/answer",
            json={"user_sql": ""},
        )

        assert resp.status_code == 422


class TestGetSession:
    def test_returns_session_and_result(self) -> None:
        client = _make_client()
        session_id = client.post("/sql-dojo/sessions", json={}).json()["session_id"]
        client.post(
            f"/sql-dojo/sessions/{session_id}/answer",
            json={"user_sql": "SELECT * FROM customers"},
        )

        resp = client.get(f"/sql-dojo/sessions/{session_id}")

        assert resp.status_code == 200
        assert resp.json()["feedback"] == "良い観点です"
        assert resp.json()["reference_sql"] == "SELECT 1"
        assert resp.json()["topic_id"] == "join-basics-shipped-orders"
        assert resp.json()["topic_title"] == "shipped注文件数"
        assert resp.json()["allow_multiple_statements"] is False


class TestListSessions:
    def test_returns_recent_sessions(self) -> None:
        client = _make_client()
        client.post("/sql-dojo/sessions", json={})

        resp = client.get("/sql-dojo/sessions")

        assert resp.status_code == 200
        data = resp.json()
        assert len(data["sessions"]) == 1
        assert data["sessions"][0]["topic_id"] == "join-basics-shipped-orders"
        assert data["sessions"][0]["topic_title"] == "shipped注文件数"


class TestAskQuestion:
    def test_returns_hint(self) -> None:
        client = _make_client()
        session_id = client.post("/sql-dojo/sessions", json={}).json()["session_id"]

        resp = client.post(
            f"/sql-dojo/sessions/{session_id}/question",
            json={"user_input": "どこから考える？", "history": []},
        )

        assert resp.status_code == 200
        assert "テーブル" in resp.json()["chat_response_text"]

    def test_returns_409_when_completed(self) -> None:
        client = _make_client()
        session_id = client.post("/sql-dojo/sessions", json={}).json()["session_id"]
        client.post(
            f"/sql-dojo/sessions/{session_id}/answer",
            json={"user_sql": "SELECT * FROM customers"},
        )

        resp = client.post(
            f"/sql-dojo/sessions/{session_id}/question",
            json={"user_input": "ヒント", "history": []},
        )

        assert resp.status_code == 409

    def test_returns_502_for_parse_failure(self) -> None:
        client = _make_client()
        session_id = client.post("/sql-dojo/sessions", json={}).json()["session_id"]
        client.app.state.container.sql_dojo_question_llm.error = SqlDojoQuestionError(
            error_code="llm_response_parse_failed",
            message="bad output",
        )

        resp = client.post(
            f"/sql-dojo/sessions/{session_id}/question",
            json={"user_input": "ヒント", "history": []},
        )

        assert resp.status_code == 502


class TestPlanReadingAnswer:
    def test_accepts_bare_explain_analyze(self) -> None:
        client = _make_client()
        session_id = client.post(
            "/sql-dojo/sessions",
            json={"difficulty": "advanced", "theme_family": "plan-reading"},
        ).json()["session_id"]

        resp = client.post(
            f"/sql-dojo/sessions/{session_id}/answer",
            json={
                "user_sql": (
                    "EXPLAIN ANALYZE BUFFERS "
                    "SELECT * FROM events "
                    "WHERE account_id = 42 AND created_at >= DATE '2026-06-01'"
                ),
            },
        )

        assert resp.status_code == 200
        assert resp.json()["reference_sql"].startswith("EXPLAIN")
