"""競プロうさぎ API エンドポイントのテスト。"""

from __future__ import annotations

from typing import Any, ClassVar

from fastapi.testclient import TestClient
from sqlalchemy.exc import IntegrityError

from algorithm_foundations.domain.foundation_types import (
    AlgorithmFoundationCatalogError,
    AlgorithmFoundationLanguageAdaptationError,
)
from api.app import create_app
from competitive.domain.competitive_types import SolutionEvaluationError


class _FakeCatalog:
    def list_catalog(
        self,
        *,
        best_scores: dict[str, int | None] | None = None,
        last_attempted_at: dict[str, str | None] | None = None,
    ) -> dict[str, object]:
        _ = best_scores, last_attempted_at
        return {
            "total_unit_count": 2,
            "total_problem_count": 6,
            "groups": [
                {
                    "group_id": "group-data",
                    "group_title": "データ構造",
                    "order": 0,
                    "units": [
                        {
                            "unit_id": "algo-102-hashmap-exists",
                            "theme_id": "algo-102",
                            "title": "存在判定をハッシュで高速化",
                            "display_order": 0,
                            "prerequisite_unit_ids": [],
                            "prerequisite_titles": [],
                            "target_skill": "存在判定をハッシュで高速化",
                            "unit_kind": "foundation",
                            "problem_count": 3,
                            "best_score": None,
                            "last_attempted_at": None,
                            "recommended": True,
                            "has_unmet_prerequisites": False,
                        },
                    ],
                },
            ],
        }

    def pick_recommended_unit_id(self, best_scores: dict[str, int | None]) -> str:
        _ = best_scores
        return "algo-102-hashmap-exists"

    def get_unit(self, unit_id: str) -> dict[str, object]:
        if unit_id != "algo-102-hashmap-exists":
            raise AlgorithmFoundationCatalogError(
                error_code="unit_not_found",
                message=f"Algorithm foundation unit not found: {unit_id}",
            )
        return {
            "unit_id": unit_id,
            "theme_id": "algo-102",
            "group_id": "group-data",
            "group_title": "データ構造",
            "title": "存在判定をハッシュで高速化",
            "concept_overview": "値を見たかどうかをハッシュ集合に記録し、あとで同じ値があるかをすぐ調べる考え方です。探索を繰り返さず membership 判定で済ませる形を身につけます。",
            "display_order": 0,
            "prerequisite_unit_ids": [],
            "prerequisite_titles": [],
            "allowed_knowledge": ["存在判定", "ハッシュセット"],
            "forbidden_knowledge": ["尺取り法"],
            "target_skill": "存在判定をハッシュで高速化",
            "unit_kind": "foundation",
            "problem_bank": [
                {
                    "problem_id": "p-1",
                    "title": "問題1",
                    "problem_statement": "問題文",
                    "input_format": "入力形式",
                    "output_format": "出力形式",
                    "constraints": "制約",
                    "examples": [{"input": "1", "output": "1"}],
                    "canonical_reference_solution": "def solve():\n    print(1)\n",
                    "canonical_language": "python",
                    "grading_rubric": [
                        {"criterion": "正しさ", "points": 100, "description": "ok"},
                    ],
                },
            ],
        }

    def pick_problem(
        self,
        unit_id: str,
        recent_problem_ids: list[str],
    ) -> dict[str, object]:
        _ = unit_id, recent_problem_ids
        return self.get_unit("algo-102-hashmap-exists")["problem_bank"][0]

    def get_problem(
        self,
        unit_id: str,
        problem_id: str,
    ) -> dict[str, object]:
        problem = self.get_unit(unit_id)["problem_bank"][0]
        if problem["problem_id"] != problem_id:
            raise AlgorithmFoundationCatalogError(
                error_code="problem_not_found",
                message=f"Algorithm foundation problem not found: {problem_id}",
            )
        return problem


class _FakeEvalResult:
    score = 88
    feedback = "良いです"
    time_complexity = "O(N)"
    space_complexity = "O(N)"
    improvement_suggestions = "端のケースを追加"
    rubric_scores: ClassVar[list[dict[str, object]]] = [
        {"criterion": "正しさ", "points_awarded": 88, "points_max": 100},
    ]


class _FakeEvaluator:
    def __init__(self) -> None:
        self.error: SolutionEvaluationError | None = None
        self.last_kwargs: dict[str, Any] | None = None

    def evaluate_solution(self, **kwargs: Any) -> _FakeEvalResult:
        self.last_kwargs = kwargs
        if self.error is not None:
            raise self.error
        return _FakeEvalResult()


class _FakeLanguageAdapter:
    def __init__(self) -> None:
        self.error: AlgorithmFoundationLanguageAdaptationError | None = None
        self.last_kwargs: dict[str, Any] | None = None

    def adapt_reference_solution(self, **kwargs: Any) -> str:
        self.last_kwargs = kwargs
        if self.error is not None:
            raise self.error
        target_language = kwargs["target_language"]
        if target_language == "typescript":
            return "function solve(): void {\n  console.log(1);\n}\n"
        return str(kwargs["canonical_reference_solution"])


class _FakeAnswer:
    def __init__(self) -> None:
        self.session_id = "sess-1"
        self.answer_text = "print(1)"
        self.score = 88
        self.feedback = "良いです"
        self.time_complexity = "O(N)"
        self.space_complexity = "O(N)"
        self.improvement_suggestions = "端のケースを追加"
        self.rubric_scores_json = "[]"


class _FakeStore:
    def __init__(self) -> None:
        self.sessions: dict[str, dict[str, object]] = {}
        self.answers: dict[str, _FakeAnswer] = {}
        self.raise_integrity_error = False

    def list_unit_history(self) -> list[object]:
        return []

    def list_recent_problem_ids_for_unit(self, unit_id: str, *, limit: int = 5) -> list[str]:
        _ = unit_id, limit
        return []

    def list_problem_history_for_unit(self, unit_id: str) -> list[object]:
        _ = unit_id
        return [
            type(
                "_ProblemHistory",
                (),
                {
                    "unit_id": "algo-102-hashmap-exists",
                    "problem_id": "p-1",
                    "attempt_count": 1,
                    "best_score": 91,
                    "last_attempted_at": "2026-06-25T10:05:00",
                },
            )(),
        ]

    def create_session(self, **kwargs: Any) -> object:
        session_id = str(kwargs["session_id"])
        self.sessions[session_id] = {**kwargs, "status": "in_progress"}
        return object()

    def get_session_details(self, session_id: str) -> dict[str, object]:
        if session_id not in self.sessions:
            msg = f"AlgorithmFoundationSession not found: {session_id}"
            raise ValueError(msg)
        row = self.sessions[session_id]
        completed_at = "2026-06-25T10:05:00" if row["status"] == "completed" else None
        return {
            "session_id": session_id,
            "created_at": "2026-06-25T10:00:00",
            "completed_at": completed_at,
            "grading_rubric": [{"criterion": "正しさ", "points": 100, "description": "ok"}],
            "reference_solution": "def solve():\n    print(1)\n",
            "examples": [{"input": "1", "output": "1"}],
            **row,
        }

    def find_answer_by_session(self, session_id: str) -> _FakeAnswer | None:
        return self.answers.get(session_id)

    def save_answer_and_complete(self, **kwargs: Any) -> _FakeAnswer:
        if self.raise_integrity_error:
            msg = "duplicate"
            raise IntegrityError(msg, {}, None)
        session_id = str(kwargs["session_id"])
        self.sessions[session_id]["status"] = "completed"
        answer = _FakeAnswer()
        answer.session_id = session_id
        self.answers[session_id] = answer
        return answer

    def list_recent_sessions(self, *, limit: int = 50) -> list[object]:
        _ = limit
        return [
            type(
                "_Session",
                (),
                {
                    "id": sid,
                    "unit_id": row["unit_id"],
                    "group_id": row["group_id"],
                    "group_title": row["group_title"],
                    "unit_title": row["unit_title"],
                    "target_skill": row["target_skill"],
                    "unit_kind": row["unit_kind"],
                    "problem_id": row["problem_id"],
                    "problem_title": row["problem_title"],
                    "programming_language": row["programming_language"],
                    "status": row["status"],
                },
            )()
            for sid, row in self.sessions.items()
            if row["status"] == "completed"
        ]


class _FakeContainer:
    def __init__(self) -> None:
        self.algorithm_foundation_catalog = _FakeCatalog()
        self.algorithm_foundation_store = _FakeStore()
        self.algorithm_foundation_language_adapter = _FakeLanguageAdapter()
        self.algorithm_foundation_solution_evaluator = _FakeEvaluator()


def _client() -> TestClient:
    app = create_app()
    app.state.container = _FakeContainer()
    return TestClient(app)


def test_get_catalog() -> None:
    client = _client()
    response = client.get("/algorithm-foundations/catalog")

    assert response.status_code == 200
    data = response.json()
    assert data["total_unit_count"] == 2
    assert data["groups"][0]["units"][0]["recommended"] is True


def test_get_languages() -> None:
    client = _client()

    response = client.get("/algorithm-foundations/languages")

    assert response.status_code == 200
    assert [item["id"] for item in response.json()["languages"]] == [
        "python",
        "typescript",
    ]


def test_get_unit_detail() -> None:
    client = _client()

    response = client.get("/algorithm-foundations/units/algo-102-hashmap-exists")

    assert response.status_code == 200
    data = response.json()
    assert data["unit_id"] == "algo-102-hashmap-exists"
    assert "ハッシュ集合に記録" in data["concept_overview"]
    assert data["problems"][0]["problem_id"] == "p-1"
    assert data["problems"][0]["best_score"] == 91


def test_start_session_does_not_list_unsubmitted_attempt() -> None:
    client = _client()
    response = client.post("/algorithm-foundations/sessions")

    assert response.status_code == 201
    data = response.json()
    assert data["unit_id"] == "algo-102-hashmap-exists"
    assert data["allowed_knowledge"] == ["存在判定", "ハッシュセット"]
    assert data["forbidden_knowledge"] == ["尺取り法"]
    session_id = data["session_id"]
    container = client.app.state.container
    container.algorithm_foundation_store.sessions[session_id]["problem_statement"] = (
        "知識をそのまま使う確認として、存在判定をハッシュで高速化 を使う 1 問です。\n\n"
        "- カテゴリ: データ構造\n"
        "- 学習単位: 存在判定をハッシュで高速化\n"
        "- ねらい: この unit の知識だけで解けるように作ってあります。\n"
        "- 補足: 前提として他の知識は要求しません。\n\n"
        "問題文"
    )
    container.algorithm_foundation_store.sessions[session_id]["problem_title"] = (
        "知識をそのまま使う確認: 存在判定をハッシュで高速化"
    )

    detail = client.get(f"/algorithm-foundations/sessions/{session_id}")
    assert detail.status_code == 200
    assert (
        detail.json()["problem_statement"]
        == "値を見たかどうかをハッシュ集合に記録し、あとで同じ値があるかをすぐ調べる考え方です。探索を繰り返さず membership 判定で済ませる形を身につけます。\n\n"
        "- カテゴリ: データ構造\n"
        "- 学習単位: 存在判定をハッシュで高速化\n\n"
        "問題文"
    )
    assert detail.json()["problem_title"] == "存在判定をハッシュで高速化 / 典型入力をそのまま処理する"

    listed = client.get("/algorithm-foundations/sessions")
    assert listed.status_code == 200
    assert listed.json()["sessions"] == []


def test_submit_answer_uses_saved_session_problem_definition() -> None:
    client = _client()
    response = client.post("/algorithm-foundations/sessions")

    assert response.status_code == 201
    session_id = response.json()["session_id"]
    container = client.app.state.container
    container.algorithm_foundation_store.sessions[session_id]["problem_statement"] = (
        "保存済み問題文"
    )
    container.algorithm_foundation_store.sessions[session_id]["input_format"] = (
        "保存済み入力形式"
    )
    container.algorithm_foundation_store.sessions[session_id]["output_format"] = (
        "保存済み出力形式"
    )
    container.algorithm_foundation_store.sessions[session_id]["constraints"] = (
        "保存済み制約"
    )
    container.algorithm_foundation_store.sessions[session_id]["examples"] = [
        {"input": "9", "output": "8"},
    ]

    submit = client.post(
        f"/algorithm-foundations/sessions/{session_id}/answer",
        json={"user_code": "print(1)"},
    )

    assert submit.status_code == 200
    evaluator = container.algorithm_foundation_solution_evaluator
    assert evaluator.last_kwargs is not None
    assert evaluator.last_kwargs["problem_statement"] == "保存済み問題文"
    assert evaluator.last_kwargs["input_format"] == "保存済み入力形式"
    assert evaluator.last_kwargs["output_format"] == "保存済み出力形式"
    assert evaluator.last_kwargs["constraints"] == "保存済み制約"
    assert evaluator.last_kwargs["examples"] == [{"input": "9", "output": "8"}]
    assert evaluator.last_kwargs["reference_solution"] == "def solve():\n    print(1)\n"


def test_completed_session_detail_and_list_normalize_legacy_problem_title() -> None:
    client = _client()
    response = client.post("/algorithm-foundations/sessions")

    assert response.status_code == 201
    session_id = response.json()["session_id"]
    container = client.app.state.container
    container.algorithm_foundation_store.sessions[session_id]["problem_statement"] = (
        "知識をそのまま使う確認として、存在判定をハッシュで高速化 を使う 1 問です。\n\n"
        "- カテゴリ: データ構造\n"
        "- 学習単位: 存在判定をハッシュで高速化\n"
        "- ねらい: この unit の知識だけで解けるように作ってあります。\n"
        "- 補足: 前提として他の知識は要求しません。\n\n"
        "問題文"
    )
    container.algorithm_foundation_store.sessions[session_id]["problem_title"] = (
        "知識をそのまま使う確認: 存在判定をハッシュで高速化"
    )
    submit = client.post(
        f"/algorithm-foundations/sessions/{session_id}/answer",
        json={"user_code": "print(1)"},
    )

    assert submit.status_code == 200

    detail = client.get(f"/algorithm-foundations/sessions/{session_id}")
    assert detail.status_code == 200
    assert detail.json()["problem_title"] == "存在判定をハッシュで高速化 / 典型入力をそのまま処理する"
    assert (
        detail.json()["problem_statement"]
        == "値を見たかどうかをハッシュ集合に記録し、あとで同じ値があるかをすぐ調べる考え方です。探索を繰り返さず membership 判定で済ませる形を身につけます。\n\n"
        "- カテゴリ: データ構造\n"
        "- 学習単位: 存在判定をハッシュで高速化\n\n"
        "問題文"
    )

    listed = client.get("/algorithm-foundations/sessions")
    assert listed.status_code == 200
    assert listed.json()["sessions"][0]["problem_title"] == (
        "存在判定をハッシュで高速化 / 典型入力をそのまま処理する"
    )


def test_start_session_with_problem_id() -> None:
    client = _client()

    response = client.post(
        "/algorithm-foundations/sessions",
        json={"unit_id": "algo-102-hashmap-exists", "problem_id": "p-1"},
    )

    assert response.status_code == 201
    data = response.json()
    assert data["problem_id"] == "p-1"


def test_start_session_with_programming_language() -> None:
    client = _client()

    response = client.post(
        "/algorithm-foundations/sessions",
        json={
            "unit_id": "algo-102-hashmap-exists",
            "problem_id": "p-1",
            "programming_language": "typescript",
        },
    )

    assert response.status_code == 201
    data = response.json()
    assert data["programming_language"] == "typescript"
    detail = client.get(f"/algorithm-foundations/sessions/{data['session_id']}")
    assert detail.status_code == 200
    assert detail.json()["programming_language"] == "typescript"
    container = client.app.state.container
    adapter = container.algorithm_foundation_language_adapter
    assert adapter.last_kwargs is not None
    assert adapter.last_kwargs["canonical_language"] == "python"
    assert adapter.last_kwargs["target_language"] == "typescript"


def test_unknown_programming_language_returns_422() -> None:
    client = _client()

    response = client.post(
        "/algorithm-foundations/sessions",
        json={"programming_language": "ruby"},
    )

    assert response.status_code == 422


def test_unknown_problem_returns_422() -> None:
    client = _client()

    response = client.post(
        "/algorithm-foundations/sessions",
        json={"unit_id": "algo-102-hashmap-exists", "problem_id": "p-x"},
    )

    assert response.status_code == 422


def test_problem_id_requires_unit_id() -> None:
    client = _client()

    response = client.post(
        "/algorithm-foundations/sessions",
        json={"problem_id": "p-1"},
    )

    assert response.status_code == 422


def test_submit_answer_returns_reference_solution() -> None:
    client = _client()
    start = client.post("/algorithm-foundations/sessions")
    session_id = start.json()["session_id"]

    response = client.post(
        f"/algorithm-foundations/sessions/{session_id}/answer",
        json={"user_code": "print(1)"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["score"] == 88
    assert "reference_solution" in data
    evaluator = client.app.state.container.algorithm_foundation_solution_evaluator
    assert evaluator.last_kwargs is not None
    assert evaluator.last_kwargs["allowed_knowledge"] == ["存在判定", "ハッシュセット"]
    assert evaluator.last_kwargs["forbidden_knowledge"] == ["尺取り法"]

    listed = client.get("/algorithm-foundations/sessions")
    assert listed.status_code == 200
    assert listed.json()["sessions"][0]["score"] == 88


def test_submit_answer_returns_502_for_parse_failure() -> None:
    client = _client()
    container = client.app.state.container
    start = client.post("/algorithm-foundations/sessions")
    session_id = start.json()["session_id"]
    container.algorithm_foundation_solution_evaluator.error = (
        SolutionEvaluationError(
            error_code="llm_response_parse_failed",
            message="failed to parse llm response",
        )
    )

    response = client.post(
        f"/algorithm-foundations/sessions/{session_id}/answer",
        json={"user_code": "print(1)"},
    )

    assert response.status_code == 502


def test_start_session_returns_503_when_language_adaptation_fails() -> None:
    client = _client()
    container = client.app.state.container
    container.algorithm_foundation_language_adapter.error = (
        AlgorithmFoundationLanguageAdaptationError(
            error_code="llm_request_failed",
            message="adapter unavailable",
        )
    )

    response = client.post(
        "/algorithm-foundations/sessions",
        json={
            "unit_id": "algo-102-hashmap-exists",
            "problem_id": "p-1",
            "programming_language": "typescript",
        },
    )

    assert response.status_code == 503


def test_unknown_unit_returns_422() -> None:
    client = _client()

    response = client.post(
        "/algorithm-foundations/sessions",
        json={"unit_id": "does-not-exist"},
    )

    assert response.status_code == 422


def test_duplicate_answer_is_409_when_store_hits_unique_constraint() -> None:
    client = _client()
    container = client.app.state.container
    start = client.post("/algorithm-foundations/sessions")
    session_id = start.json()["session_id"]
    container.algorithm_foundation_store.raise_integrity_error = True

    response = client.post(
        f"/algorithm-foundations/sessions/{session_id}/answer",
        json={"user_code": "print(1)"},
    )

    assert response.status_code == 409


def test_list_sessions_includes_score() -> None:
    client = _client()
    start = client.post("/algorithm-foundations/sessions")
    session_id = start.json()["session_id"]
    client.post(
        f"/algorithm-foundations/sessions/{session_id}/answer",
        json={"user_code": "print(1)"},
    )

    response = client.get("/algorithm-foundations/sessions")

    assert response.status_code == 200
    data = response.json()
    assert data["sessions"][0]["score"] == 88
