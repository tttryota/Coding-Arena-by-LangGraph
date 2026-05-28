"""FastAPI router のテスト。TestClient ベース。"""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import patch
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
    """graph_runner=None の Container。quiz 系 503 テスト用。"""
    from api.app import create_app

    app = create_app()
    container = _FakeContainer()
    container.graph_runner = None  # type: ignore[assignment]
    app.state.container = container
    return TestClient(app, raise_server_exceptions=False)


@pytest.fixture
def client_no_embedder() -> TestClient:
    """batch_embedder=None の Container。ingestion 503 テスト用。"""
    from api.app import create_app

    app = create_app()
    container = _FakeContainer()
    container.batch_embedder = None  # type: ignore[assignment]
    app.state.container = container
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
        self.quiz_answer_store = _FakeQuizAnswerStore()
        self.roadmap_item_read_store = _FakeRoadmapItemReadStore()
        self.graph_runner = _FakeGraphRunner()
        self.ingestion_feedback_store = _FakeFeedbackStore()
        self.batch_diff_detector = _FakeBatchDiffDetector()
        self.batch_chunk_splitter = _FakeBatchChunkSplitter()
        self.batch_chunk_tagger = _FakeBatchChunkTagger()
        self.batch_embedder = _FakeBatchEmbedder()
        self.chunk_store = _FakeChunkStore()
        self.post_ingestion_hook = _FakePostIngestionHook()
        self.preset_reader = _FakePresetReader()
        self.note_topic_reader = _FakeNoteTopicReader()
        self.topic_store = _FakeTopicStore()


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

    def get_state(self, *, thread_id: str) -> dict:
        raise LookupError(f"No checkpoint for {thread_id}")


class _FakeBatchDiffDetector:
    def detect(self, target_path: object) -> object:
        return None


class _FakeBatchChunkSplitter:
    def split(self, markdown_text: str, *, source_path: str | None = None) -> list:
        return []


class _FakeBatchChunkTagger:
    def tag(self, chunks: list, *, source_path: str) -> list:
        return []


class _FakeBatchEmbedder:
    def embed(self, chunks: list, *, source_path: str) -> list:
        return []


class _FakeChunkStore:
    def delete_by_source_path(self, source_path: str) -> object:
        return None

    def upsert_chunks(self, upsert_input: object) -> object:
        return None


class _FakePostIngestionHook:
    def on_file_ingested(self, source_path: str, chunk_data: list) -> None:
        pass


class _FakePresetReader:
    def list_preset_topics(self) -> list:
        return []


class _FakeNoteTopicReader:
    def list_note_topics(self) -> list:
        return []

    def list_note_counts(self, canonical_names: list[str]) -> list:
        return []


class _FakeTopicStore:
    def list_manual_topics(self) -> list:
        return []

    def find_topic_by_canonical_name(self, canonical_name: str) -> None:
        return None

    def create_manual_topic(self, name: str, canonical_name: str) -> object:
        from roadmap.domain.topic_listing_types import StoredTopicRecord

        return StoredTopicRecord(
            name=name, canonical_name=canonical_name, source="manual"
        )


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
        """テスト対象: RoadmapListEndpoint の処理。
        テストケース: 個別条件での処理を検証する。
        期待結果: 想定どおりの処理結果が得られる。"""
        response = client.get("/roadmaps")

        assert response.status_code == 200


class TestTopicListEndpoint:
    def test_returns_200_with_empty_candidates(self, client: TestClient) -> None:
        """テスト対象: TopicListEndpoint の処理。
        テストケース: 個別条件での処理を検証する。
        期待結果: 想定どおりの処理結果が得られる。"""
        response = client.get("/roadmaps/topics")

        assert response.status_code == 200
        data = response.json()
        assert data == {"candidates": []}

    def test_returns_candidates_from_application_layer(
        self,
        client: TestClient,
    ) -> None:
        """テスト対象: TopicListEndpoint の処理。
        テストケース: 個別条件での処理を検証する。
        期待結果: 想定どおりの処理結果が得られる。"""
        from roadmap.domain.topic_listing_types import TopicCandidate

        candidates = [
            TopicCandidate(name="TypeScript", source="preset", note_count=12),
            TopicCandidate(name="Docker", source="note", note_count=3),
        ]

        with patch(
            "roadmap.application.topic_listing.list_topic_candidates",
            return_value=candidates,
        ) as mock_list:
            response = client.get("/roadmaps/topics")

        mock_list.assert_called_once()
        assert response.status_code == 200
        data = response.json()
        assert len(data["candidates"]) == 2
        assert data["candidates"][0] == {
            "name": "TypeScript",
            "source": "preset",
            "note_count": 12,
        }
        assert data["candidates"][1] == {
            "name": "Docker",
            "source": "note",
            "note_count": 3,
        }


class TestTopicRegisterEndpoint:
    def test_returns_201_with_registered_topic(self, client: TestClient) -> None:
        """テスト対象: TopicRegisterEndpoint の処理。
        テストケース: 個別条件での処理を検証する。
        期待結果: 想定どおりの処理結果が得られる。"""
        from roadmap.domain.topic_listing_types import TopicCandidate

        with patch(
            "roadmap.application.topic_listing.register_manual_topic",
            return_value=TopicCandidate(
                name="GraphRAG",
                source="manual",
                note_count=0,
            ),
        ) as mock_register:
            response = client.post(
                "/roadmaps/topics",
                json={"name": "GraphRAG"},
            )

        mock_register.assert_called_once()
        assert response.status_code == 201
        data = response.json()
        assert data == {"name": "GraphRAG", "source": "manual", "note_count": 0}

    def test_returns_201_for_duplicate_topic(self, client: TestClient) -> None:
        """テスト対象: TopicRegisterEndpoint の処理。
        テストケース: 個別条件での処理を検証する。
        期待結果: 想定どおりの処理結果が得られる。"""
        from roadmap.domain.topic_listing_types import TopicCandidate

        with patch(
            "roadmap.application.topic_listing.register_manual_topic",
            return_value=TopicCandidate(
                name="TypeScript",
                source="preset",
                note_count=12,
            ),
        ):
            response = client.post(
                "/roadmaps/topics",
                json={"name": "typescript"},
            )

        assert response.status_code == 201
        assert response.json()["name"] == "TypeScript"
        assert response.json()["source"] == "preset"

    def test_returns_422_for_empty_name(self, client: TestClient) -> None:
        """テスト対象: TopicRegisterEndpoint の処理。
        テストケース: 個別条件での処理を検証する。
        期待結果: 想定どおりの処理結果が得られる。"""
        from roadmap.domain.topic_listing_types import TopicListingEmptyTopicNameError

        with patch(
            "roadmap.application.topic_listing.register_manual_topic",
            side_effect=TopicListingEmptyTopicNameError,
        ):
            response = client.post(
                "/roadmaps/topics",
                json={"name": ""},
            )

        assert response.status_code == 422
        assert response.json()["detail"] == "Topic name must not be empty"

    def test_returns_422_for_whitespace_only(self, client: TestClient) -> None:
        """テスト対象: TopicRegisterEndpoint の処理。
        テストケース: 個別条件での処理を検証する。
        期待結果: 想定どおりの処理結果が得られる。"""
        from roadmap.domain.topic_listing_types import TopicListingEmptyTopicNameError

        with patch(
            "roadmap.application.topic_listing.register_manual_topic",
            side_effect=TopicListingEmptyTopicNameError,
        ):
            response = client.post(
                "/roadmaps/topics",
                json={"name": "   "},
            )

        assert response.status_code == 422

    def test_response_has_exactly_three_fields(self, client: TestClient) -> None:
        """テスト対象: TopicRegisterEndpoint の処理。
        テストケース: 個別条件での処理を検証する。
        期待結果: 想定どおりの処理結果が得られる。"""
        from roadmap.domain.topic_listing_types import TopicCandidate

        with patch(
            "roadmap.application.topic_listing.register_manual_topic",
            return_value=TopicCandidate(
                name="Test",
                source="manual",
                note_count=0,
            ),
        ):
            response = client.post(
                "/roadmaps/topics",
                json={"name": "Test"},
            )

        assert response.status_code == 201
        assert set(response.json().keys()) == {"name", "source", "note_count"}


class TestRoadmapGetEndpoint:
    def test_returns_404_for_missing_roadmap(self, client: TestClient) -> None:
        """テスト対象: RoadmapGetEndpoint の処理。
        テストケース: 個別条件での処理を検証する。
        期待結果: 想定どおりの処理結果が得られる。"""
        response = client.get(f"/roadmaps/{uuid4()}")

        assert response.status_code == 404


class TestRoadmapGenerateEndpoint:
    def test_returns_202_with_job_id(self, client: TestClient) -> None:
        """テスト対象: RoadmapGenerateEndpoint の処理。
        テストケース: 個別条件での処理を検証する。
        期待結果: 想定どおりの処理結果が得られる。"""
        response = client.post(
            "/roadmaps/generate",
            json={"topic": "TypeScript"},
        )

        assert response.status_code == 202
        data = response.json()
        assert "job_id" in data
        assert data["status"] == "queued"

    def test_returns_422_for_empty_topic(self, client: TestClient) -> None:
        """テスト対象: RoadmapGenerateEndpoint の処理。
        テストケース: 個別条件での処理を検証する。
        期待結果: 想定どおりの処理結果が得られる。"""
        response = client.post(
            "/roadmaps/generate",
            json={"topic": ""},
        )

        assert response.status_code == 422


class TestRoadmapJobStatusEndpoint:
    def test_returns_404_for_unknown_job(self, client: TestClient) -> None:
        """テスト対象: RoadmapJobStatusEndpoint の処理。
        テストケース: 個別条件での処理を検証する。
        期待結果: 想定どおりの処理結果が得られる。"""
        response = client.get(f"/roadmaps/generate/{uuid4()}")

        assert response.status_code == 404


class TestRoadmapItemMoveEndpoint:
    def test_returns_404_for_missing_roadmap(self, client: TestClient) -> None:
        """テスト対象: RoadmapItemMoveEndpoint の処理。
        テストケース: 個別条件での処理を検証する。
        期待結果: 想定どおりの処理結果が得られる。"""
        from roadmap.domain.roadmap_item_crud_types import RoadmapItemCrudNotFoundError

        with patch(
            "roadmap.application.roadmap_item_crud.move_roadmap_item",
            side_effect=RoadmapItemCrudNotFoundError("not found"),
        ) as mock_move:
            response = client.put(
                f"/roadmaps/{uuid4()}/items/{uuid4()}/move",
                json={"target_parent_id": None, "target_order": 0},
            )

        mock_move.assert_called_once()
        assert response.status_code == 404

    def test_returns_422_for_invalid_move(self, client: TestClient) -> None:
        """テスト対象: RoadmapItemMoveEndpoint の処理。
        テストケース: 個別条件での処理を検証する。
        期待結果: 想定どおりの処理結果が得られる。"""
        from roadmap.domain.roadmap_item_crud_types import RoadmapItemCrudInputError

        with patch(
            "roadmap.application.roadmap_item_crud.move_roadmap_item",
            side_effect=RoadmapItemCrudInputError("invalid move"),
        ) as mock_move:
            response = client.put(
                f"/roadmaps/{uuid4()}/items/{uuid4()}/move",
                json={"target_parent_id": None, "target_order": 0},
            )

        mock_move.assert_called_once()
        assert response.status_code == 422

    def test_returns_moved_item_on_success(self, client: TestClient) -> None:
        """テスト対象: RoadmapItemMoveEndpoint の処理。
        テストケース: 個別条件での処理を検証する。
        期待結果: 想定どおりの処理結果が得られる。"""
        from roadmap.domain.roadmap_item_crud_types import (
            RoadmapItemMoveInput,
            RoadmapItemMoveResult,
        )

        item_id = uuid4()
        roadmap_id = uuid4()
        moved_item = SimpleNamespace(
            id=item_id,
            roadmap_id=roadmap_id,
            parent_id=None,
            title="Moved",
            description="desc",
            level="major",
            order=0,
            score=0,
        )

        with patch(
            "roadmap.application.roadmap_item_crud.move_roadmap_item",
            return_value=RoadmapItemMoveResult(moved_item=moved_item),
        ) as mock_move:
            response = client.put(
                f"/roadmaps/{roadmap_id}/items/{item_id}/move",
                json={"target_parent_id": None, "target_order": 0},
            )

        mock_move.assert_called_once()
        call_input = mock_move.call_args[0][0]
        assert isinstance(call_input, RoadmapItemMoveInput)
        assert call_input.roadmap_id == roadmap_id
        assert call_input.item_id == item_id
        assert call_input.target_parent_id is None
        assert call_input.target_order == 0

        assert response.status_code == 200
        data = response.json()
        assert set(data.keys()) == {"moved_item"}
        mi = data["moved_item"]
        assert set(mi.keys()) == {
            "id",
            "roadmap_id",
            "parent_id",
            "title",
            "description",
            "level",
            "order",
            "score",
        }
        assert mi["id"] == str(item_id)
        assert mi["roadmap_id"] == str(roadmap_id)
        assert mi["parent_id"] is None
        assert mi["title"] == "Moved"
        assert mi["description"] == "desc"
        assert mi["level"] == "major"
        assert mi["order"] == 0
        assert mi["score"] == 0


class TestRoadmapItemDeleteEndpoint:
    def test_returns_404_for_missing_roadmap(self, client: TestClient) -> None:
        """テスト対象: RoadmapItemDeleteEndpoint の処理。
        テストケース: 個別条件での処理を検証する。
        期待結果: 想定どおりの処理結果が得られる。"""
        response = client.delete(
            f"/roadmaps/{uuid4()}/items/{uuid4()}",
        )

        assert response.status_code == 404


# ---------------------------------------------------------------------------
# Quiz Endpoints
# ---------------------------------------------------------------------------


class TestQuizSessionInputEndpoint:
    def test_returns_503_when_graph_runner_is_none(
        self,
        client_no_graph_runner: TestClient,
    ) -> None:
        """テスト対象: QuizSessionInputEndpoint の処理。
        テストケース: 個別条件での処理を検証する。
        期待結果: 想定どおりの処理結果が得られる。"""
        response = client_no_graph_runner.post(
            "/sessions/some-session/input",
            json={"user_input": "test", "input_source": "form"},
        )

        assert response.status_code == 503

    def test_returns_422_for_lifecycle_error(self, client: TestClient) -> None:
        """テスト対象: QuizSessionInputEndpoint の処理。
        テストケース: 個別条件での処理を検証する。
        期待結果: 想定どおりの処理結果が得られる。"""
        from quiz.application.session_lifecycle_types import (
            QuizSessionLifecycleError,
        )

        with patch(
            "quiz.application.session_lifecycle.resume_session",
            side_effect=QuizSessionLifecycleError(
                error_code="test_error",
                message="lifecycle error",
            ),
        ) as mock_resume:
            response = client.post(
                "/sessions/some-session/input",
                json={"user_input": "test", "input_source": "form"},
            )

        mock_resume.assert_called_once()
        assert response.status_code == 422

    def test_returns_422_for_value_error(self, client: TestClient) -> None:
        """テスト対象: QuizSessionInputEndpoint の処理。
        テストケース: 個別条件での処理を検証する。
        期待結果: 想定どおりの処理結果が得られる。"""
        with patch(
            "quiz.application.session_lifecycle.resume_session",
            side_effect=ValueError("bad value"),
        ) as mock_resume:
            response = client.post(
                "/sessions/some-session/input",
                json={"user_input": "test", "input_source": "form"},
            )

        mock_resume.assert_called_once()
        assert response.status_code == 422

    def test_returns_session_state_on_success(self, client: TestClient) -> None:
        """テスト対象: QuizSessionInputEndpoint の処理。
        テストケース: 個別条件での処理を検証する。
        期待結果: 想定どおりの処理結果が得られる。"""
        from quiz.application.session_lifecycle_types import ResumeSessionInput

        expected_state = {
            "session_id": "sess-1",
            "roadmap_item_id": "item-1",
            "roadmap_item_level": "middle",
            "roadmap_item_title": "Test",
            "roadmap_item_description": "desc",
            "is_resumed": True,
        }

        with patch(
            "quiz.application.session_lifecycle.resume_session",
            return_value=expected_state,
        ) as mock_resume:
            response = client.post(
                "/sessions/sess-1/input",
                json={"user_input": "answer text", "input_source": "form"},
            )

        mock_resume.assert_called_once()
        call_input = mock_resume.call_args[0][0]
        assert isinstance(call_input, ResumeSessionInput)
        assert call_input.session_id == "sess-1"
        assert call_input.user_input == "answer text"
        assert call_input.input_source == "form"

        assert response.status_code == 200
        data = response.json()
        assert data == expected_state


class TestQuizSessionGetEndpoint:
    def test_returns_404_for_missing_session(self, client: TestClient) -> None:
        """テスト対象: QuizSessionGetEndpoint の処理。
        テストケース: 個別条件での処理を検証する。
        期待結果: 想定どおりの処理結果が得られる。"""
        response = client.get("/sessions/nonexistent")

        assert response.status_code == 404

    def test_returns_session_with_graph_state_when_available(
        self, client: TestClient,
    ) -> None:
        """テスト対象: QuizSessionGetEndpoint の処理。
        テストケース: 個別条件での処理を検証する。
        期待結果: 想定どおりの処理結果が得られる。"""
        from unittest.mock import MagicMock

        app = client.app
        container = app.state.container  # type: ignore[union-attr]
        mock_session = MagicMock()
        mock_session.id = "sess-get-1"
        container.quiz_session_store.find_session = MagicMock(return_value=mock_session)

        mock_state = {"session_id": "sess-get-1", "current_question_text": "問題文"}
        container.graph_runner.get_state = MagicMock(return_value=mock_state)

        response = client.get("/sessions/sess-get-1")

        assert response.status_code == 200
        data = response.json()
        assert data["session_id"] == "sess-get-1"
        assert "graph_state" in data
        assert data["graph_state"]["current_question_text"] == "問題文"

    def test_returns_session_without_graph_state_on_lookup_error(
        self, client: TestClient,
    ) -> None:
        """テスト対象: QuizSessionGetEndpoint の処理。
        テストケース: 個別条件での処理を検証する。
        期待結果: 想定どおりの処理結果が得られる。"""
        from unittest.mock import MagicMock

        app = client.app
        container = app.state.container  # type: ignore[union-attr]
        mock_session = MagicMock()
        mock_session.id = "sess-get-2"
        container.quiz_session_store.find_session = MagicMock(return_value=mock_session)
        container.graph_runner.get_state = MagicMock(
            side_effect=LookupError("No checkpoint"),
        )

        response = client.get("/sessions/sess-get-2")

        assert response.status_code == 200
        data = response.json()
        assert data["session_id"] == "sess-get-2"
        assert "graph_state" not in data

    def test_returns_session_without_graph_state_when_graph_runner_is_none(
        self, client: TestClient,
    ) -> None:
        """テスト対象: QuizSessionGetEndpoint の処理。
        テストケース: 個別条件での処理を検証する。
        期待結果: 想定どおりの処理結果が得られる。"""
        from unittest.mock import MagicMock

        app = client.app
        container = app.state.container  # type: ignore[union-attr]
        container.graph_runner = None  # type: ignore[assignment]
        mock_session = MagicMock()
        mock_session.id = "sess-get-3"
        container.quiz_session_store.find_session = MagicMock(return_value=mock_session)

        response = client.get("/sessions/sess-get-3")

        assert response.status_code == 200
        data = response.json()
        assert data["session_id"] == "sess-get-3"
        assert "graph_state" not in data
        # restore for other tests
        container.graph_runner = _FakeGraphRunner()


# ---------------------------------------------------------------------------
# Ingestion Endpoints
# ---------------------------------------------------------------------------


class TestIngestionTriggerEndpoint:
    def test_returns_503_when_embedder_is_none(
        self,
        client_no_embedder: TestClient,
    ) -> None:
        """テスト対象: IngestionTriggerEndpoint の処理。
        テストケース: 個別条件での処理を検証する。
        期待結果: 想定どおりの処理結果が得られる。"""
        response = client_no_embedder.post(
            "/ingestion/trigger",
            json={"target_path": "/some/path", "trigger": "startup"},
        )

        assert response.status_code == 503

    def test_returns_422_for_config_error(self, client: TestClient) -> None:
        """テスト対象: IngestionTriggerEndpoint の処理。
        テストケース: 個別条件での処理を検証する。
        期待結果: 想定どおりの処理結果が得られる。"""
        from ingestion.domain.batch_scheduler_types import BatchSchedulerConfigError

        with patch(
            "ingestion.application.batch_executor.run_once",
            side_effect=BatchSchedulerConfigError("target_path must not be empty"),
        ) as mock_run_once:
            response = client.post(
                "/ingestion/trigger",
                json={"target_path": "", "trigger": "startup"},
            )

        mock_run_once.assert_called_once()
        assert response.status_code == 422

    def test_returns_422_for_invalid_trigger(self, client: TestClient) -> None:
        """テスト対象: IngestionTriggerEndpoint の処理。
        テストケース: 個別条件での処理を検証する。
        期待結果: 想定どおりの処理結果が得られる。"""
        with patch(
            "ingestion.application.batch_executor.run_once",
        ) as mock_run_once:
            response = client.post(
                "/ingestion/trigger",
                json={"target_path": "/some/path", "trigger": "invalid"},
            )

        mock_run_once.assert_not_called()
        assert response.status_code == 422

    def test_returns_202_with_summary_on_success(self, client: TestClient) -> None:
        """テスト対象: IngestionTriggerEndpoint の処理。
        テストケース: 個別条件での処理を検証する。
        期待結果: 想定どおりの処理結果が得られる。"""
        from ingestion.domain.batch_scheduler_types import BatchRunSummary

        summary = BatchRunSummary(
            status="completed",
            trigger="startup",
            new_count=1,
            updated_count=0,
            deleted_count=0,
            deleted_success_count=0,
            ingest_target_count=1,
            ingested_success_count=1,
            failed_file_count=0,
            failed_files=[],
            stored_chunk_count=3,
        )

        with patch(
            "ingestion.application.batch_executor.run_once",
            return_value=summary,
        ) as mock_run_once:
            response = client.post(
                "/ingestion/trigger",
                json={"target_path": "/vault", "trigger": "startup"},
            )

        mock_run_once.assert_called_once()
        call_config = mock_run_once.call_args[0][0]
        assert call_config.target_path == "/vault"
        call_kwargs = mock_run_once.call_args[1]
        assert call_kwargs["trigger"] == "startup"

        assert response.status_code == 202
        data = response.json()
        assert data["status"] == "completed"
        assert data["trigger"] == "startup"
        assert data["new_count"] == 1
        assert data["updated_count"] == 0
        assert data["deleted_count"] == 0
        assert data["deleted_success_count"] == 0
        assert data["ingest_target_count"] == 1
        assert data["ingested_success_count"] == 1
        assert data["failed_file_count"] == 0
        assert data["failed_files"] == []
        assert data["stored_chunk_count"] == 3


class TestFeedbackListEndpoint:
    def test_returns_200_with_empty_list(self, client: TestClient) -> None:
        """テスト対象: FeedbackListEndpoint の処理。
        テストケース: 個別条件での処理を検証する。
        期待結果: 想定どおりの処理結果が得られる。"""
        response = client.get("/ingestion/feedbacks")

        assert response.status_code == 200
        data = response.json()
        assert data["items"] == []
        assert data["total_count"] == 0


class TestFeedbackMarkReadEndpoint:
    def test_returns_404_for_missing_feedback(self, client: TestClient) -> None:
        """テスト対象: FeedbackMarkReadEndpoint の処理。
        テストケース: 個別条件での処理を検証する。
        期待結果: 想定どおりの処理結果が得られる。"""
        response = client.put(
            f"/ingestion/feedbacks/{uuid4()}/read",
        )

        assert response.status_code == 404
