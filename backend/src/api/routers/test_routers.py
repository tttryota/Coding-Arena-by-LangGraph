"""roadmap / quiz ルーターの API テスト。"""

from __future__ import annotations

from types import SimpleNamespace
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client() -> TestClient:
    from api.app import create_app

    app = create_app()
    app.state.container = _FakeContainer()
    return TestClient(app, raise_server_exceptions=False)


@pytest.fixture
def client_no_graph_runner() -> TestClient:
    from api.app import create_app

    app = create_app()
    container = _FakeContainer()
    container.graph_runner = None  # type: ignore[assignment]
    app.state.container = container
    return TestClient(app, raise_server_exceptions=False)


class _FakeContainer:
    def __init__(self) -> None:
        self.roadmap_retrieval_reader = _FakeRoadmapReader()
        self.uuid_generator = _FakeUuidGenerator()
        self.job_scheduler = _FakeScheduler()
        self.job_status_store = _FakeJobStatusStore()
        self.roadmap_item_crud_store = _FakeRoadmapItemCrudStore()
        self.quiz_session_store = _FakeQuizSessionStore()
        self.quiz_answer_store = _FakeQuizAnswerStore()
        self.roadmap_item_read_store = _FakeRoadmapItemReadStore()
        self.graph_runner = _FakeGraphRunner()
        self.preset_reader = _FakePresetReader()
        self.topic_store = _FakeTopicStore()
        self.coding_graph_runner = None


class _FakeUuidGenerator:
    def generate(self):
        return uuid4()


class _FakeScheduler:
    def enqueue_roadmap_generation(self, job_id: object, topic: str) -> None:
        pass


class _FakeJobStatusStore:
    def __init__(self) -> None:
        self._jobs: dict[object, dict[str, object]] = {}

    def create_queued_job(self, job_id: object, topic: str) -> None:
        self._jobs[job_id] = {"status": "queued"}

    def get_job(self, job_id: object) -> dict[str, object]:
        if job_id not in self._jobs:
            from roadmap.domain.roadmap_generation_types import (
                RoadmapGenerationJobNotFoundError,
            )

            msg = f"Job not found: {job_id}"
            raise RoadmapGenerationJobNotFoundError(msg)
        return self._jobs[job_id]

    def mark_failed(
        self,
        job_id: object,
        error_code: str,
        error_message: str,
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

    def find_item(self, item_id: object) -> None:
        return None

    def replace_items(self, roadmap_id: object, items: list) -> None:
        pass


class _FakeQuizSessionStore:
    def find_session(self, session_id: str) -> None:
        return None

    def find_in_progress_by_item(self, roadmap_item_id: str) -> None:
        return None

    def create_session(self, roadmap_item_id: str) -> object:
        return SimpleNamespace(id=str(uuid4()), roadmap_item_id=roadmap_item_id)

    def discard_session(self, session_id: str) -> None:
        pass


class _FakeQuizAnswerStore:
    def find_by_session(self, session_id: str) -> list:
        return []

    def save_answer(self, quiz_session_id: str, answer: object) -> None:
        pass


class _FakeRoadmapItemReadStore:
    def find_item(self, item_id: str) -> None:
        return None


class _FakeGraphRunner:
    def start_graph(self, state: object, *, thread_id: str) -> None:
        pass

    def resume_graph(self, user_input: object, *, thread_id: str) -> None:
        pass

    def retry_graph(self, *, thread_id: str) -> None:
        pass

    def get_state(self, *, thread_id: str) -> dict[str, object]:
        msg = f"No checkpoint for {thread_id}"
        raise LookupError(msg)


class _FakePresetReader:
    def list_preset_topics(self) -> list:
        from roadmap.domain.topic_listing_types import PresetTopicRecord

        return [
            PresetTopicRecord(name="TypeScript", canonical_name="typescript"),
            PresetTopicRecord(name="Docker", canonical_name="docker"),
        ]


class _FakeTopicStore:
    def __init__(self) -> None:
        self._stored: dict[str, object] = {}

    def list_manual_topics(self) -> list:
        return list(self._stored.values())

    def find_topic_by_canonical_name(self, canonical_name: str) -> object | None:
        return self._stored.get(canonical_name)

    def create_manual_topic(self, name: str, canonical_name: str) -> object:
        from roadmap.domain.topic_listing_types import StoredTopicRecord

        record = StoredTopicRecord(
            name=name,
            canonical_name=canonical_name,
            source="manual",
        )
        self._stored[canonical_name] = record
        return record


def test_list_topics_returns_preset_and_manual_candidates(client: TestClient) -> None:
    response = client.get("/roadmaps/topics")

    assert response.status_code == 200
    assert response.json() == {
        "candidates": [
            {"name": "Docker", "source": "preset"},
            {"name": "TypeScript", "source": "preset"},
        ],
    }


def test_register_topic_returns_name_and_source_only(client: TestClient) -> None:
    response = client.post("/roadmaps/topics", json={"name": "Graph Search"})

    assert response.status_code == 201
    assert response.json() == {"name": "Graph Search", "source": "manual"}


def test_register_topic_rejects_blank_name(client: TestClient) -> None:
    response = client.post("/roadmaps/topics", json={"name": "  "})

    assert response.status_code == 422
    assert response.json()["detail"] == "Topic name must not be empty"


def test_generate_roadmap_returns_queued_job(client: TestClient) -> None:
    response = client.post("/roadmaps/generate", json={"topic": "TypeScript"})

    assert response.status_code == 202
    payload = response.json()
    assert payload["status"] == "queued"
    assert isinstance(payload["job_id"], str)


def test_get_generation_job_returns_404_for_unknown_job(client: TestClient) -> None:
    response = client.get(f"/roadmaps/generate/{uuid4()}")

    assert response.status_code == 404


def test_start_session_returns_503_without_graph_runner(
    client_no_graph_runner: TestClient,
) -> None:
    response = client_no_graph_runner.post(
        "/sessions",
        json={"roadmap_item_id": "roadmap-item-1"},
    )

    assert response.status_code == 503
    assert response.json()["detail"] == "Quiz service unavailable"
