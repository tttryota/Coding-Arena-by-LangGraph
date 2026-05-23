"""FastAPI router のテスト。TestClient ベース。"""

from __future__ import annotations

from uuid import uuid4

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client() -> TestClient:
    from api.app import create_app

    app = create_app()
    app.state.container = _FakeContainer()
    return TestClient(app, raise_server_exceptions=False)


class _FakeContainer:
    """ルーターテスト用の最小スタブ。"""

    def __init__(self) -> None:
        self.roadmap_retrieval_reader = _FakeRoadmapReader()
        self.uuid_generator = _FakeUuidGenerator()
        self.job_scheduler = _FakeScheduler()
        self.job_status_store = _FakeJobStatusStore()
        self.roadmap_item_crud_store = _FakeRoadmapItemCrudStore()
        self.quiz_session_store = _FakeQuizSessionStore()
        self.roadmap_item_read_store = _FakeRoadmapItemReadStore()
        self.graph_runner = _FakeGraphRunner()
        self.ingestion_feedback_store = _FakeFeedbackStore()


class _FakeUuidGenerator:
    def generate(self):
        return uuid4()


class _FakeScheduler:
    def enqueue_roadmap_generation(self, job_id: object, topic: str) -> None:
        pass


class _FakeJobStatusStore:
    def __init__(self) -> None:
        self._jobs: dict = {}

    def create_queued_job(self, job_id: object, topic: str) -> None:
        self._jobs[job_id] = {"status": "queued"}

    def get_job(self, job_id: object) -> dict:
        if job_id not in self._jobs:
            from roadmap.domain.roadmap_generation_types import (
                RoadmapGenerationJobNotFoundError,
            )

            msg = f"Job not found: {job_id}"
            raise RoadmapGenerationJobNotFoundError(msg)
        return self._jobs[job_id]

    def mark_failed(
        self, job_id: object, error_code: str, error_message: str,
    ) -> None:
        self._jobs[job_id] = {
            "status": "failed",
            "error_code": error_code,
            "error_message": error_message,
        }


class _FakeRoadmapReader:
    def find_all_roadmaps(self) -> list:
        return []

    def find_roadmap(self, roadmap_id: object) -> None:
        return None


class _FakeRoadmapItemCrudStore:
    def find_roadmap(self, roadmap_id: object) -> None:
        return None


class _FakeQuizSessionStore:
    def find_session(self, session_id: str) -> None:
        return None

    def find_in_progress_by_item(self, roadmap_item_id: str) -> None:
        return None

    def create_session(self, roadmap_item_id: str) -> object:
        from types import SimpleNamespace

        return SimpleNamespace(id=str(uuid4()))


class _FakeRoadmapItemReadStore:
    def find_item(self, item_id: str) -> None:
        return None


class _FakeGraphRunner:
    def start_graph(self, state: object) -> None:
        pass

    def resume_graph(self, state: object) -> None:
        pass


class _FakeFeedbackStore:
    def find_feedbacks(
        self,
        *,
        date_from: str | None,
        date_to: str | None,
        read_status: str,
    ) -> list:
        return []

    def get_by_id(self, feedback_id: object) -> None:
        return None


# ---------------------------------------------------------------------------
# Roadmap Endpoints
# ---------------------------------------------------------------------------


class TestRoadmapListEndpoint:
    def test_returns_200_with_empty_list(self, client: TestClient) -> None:
        response = client.get("/roadmaps")

        assert response.status_code == 200


class TestRoadmapGetEndpoint:
    def test_returns_404_for_missing_roadmap(self, client: TestClient) -> None:
        response = client.get(f"/roadmaps/{uuid4()}")

        assert response.status_code == 404


class TestRoadmapGenerateEndpoint:
    def test_returns_202_with_job_id(self, client: TestClient) -> None:
        response = client.post(
            "/roadmaps/generate",
            json={"topic": "TypeScript"},
        )

        assert response.status_code == 202
        data = response.json()
        assert "job_id" in data
        assert data["status"] == "queued"

    def test_returns_422_for_empty_topic(self, client: TestClient) -> None:
        response = client.post(
            "/roadmaps/generate",
            json={"topic": ""},
        )

        assert response.status_code == 422


class TestRoadmapJobStatusEndpoint:
    def test_returns_404_for_unknown_job(self, client: TestClient) -> None:
        response = client.get(f"/roadmaps/generate/{uuid4()}")

        assert response.status_code == 404


class TestRoadmapItemDeleteEndpoint:
    def test_returns_404_for_missing_roadmap(self, client: TestClient) -> None:
        response = client.delete(
            f"/roadmaps/{uuid4()}/items/{uuid4()}",
        )

        assert response.status_code == 404


# ---------------------------------------------------------------------------
# Quiz Endpoints
# ---------------------------------------------------------------------------


class TestQuizSessionGetEndpoint:
    def test_returns_404_for_missing_session(self, client: TestClient) -> None:
        response = client.get("/sessions/nonexistent")

        assert response.status_code == 404


# ---------------------------------------------------------------------------
# Ingestion Endpoints
# ---------------------------------------------------------------------------


class TestFeedbackListEndpoint:
    def test_returns_200_with_empty_list(self, client: TestClient) -> None:
        response = client.get("/ingestion/feedbacks")

        assert response.status_code == 200
        data = response.json()
        assert data["items"] == []
        assert data["total_count"] == 0


class TestFeedbackMarkReadEndpoint:
    def test_returns_404_for_missing_feedback(self, client: TestClient) -> None:
        response = client.put(
            f"/ingestion/feedbacks/{uuid4()}/read",
        )

        assert response.status_code == 404
