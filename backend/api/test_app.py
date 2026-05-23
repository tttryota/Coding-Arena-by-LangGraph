"""FastAPI app factory + DI container のテスト。"""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor

import pytest
from sqlalchemy import Engine, create_engine


def _setup_db() -> Engine:
    import infrastructure.rdb.models  # noqa: F401
    from infrastructure.rdb.base import Base

    eng = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(eng)
    return eng


class _FakeChromaCollection:
    """ChromaDB collection の最小スタブ。"""

    def get(self, include: list[str]) -> dict:
        return {"ids": [], "documents": [], "metadatas": [], "embeddings": []}

    def query(
        self,
        query_embeddings: list[list[float]],
        n_results: int,
    ) -> dict:
        return {"ids": [[]], "documents": [[]], "metadatas": [[]], "distances": [[]]}

    def upsert(
        self,
        ids: list[str],
        documents: list[str],
        embeddings: list[list[float]],
        metadatas: list[dict],
    ) -> None:
        pass

    def delete(self, where: dict) -> None:
        pass


def _make_container() -> object:
    from api.dependencies import Container

    return Container(
        engine=_setup_db(),
        chroma_collection=_FakeChromaCollection(),
        codex_base_url="http://localhost:11111",
    )


class TestCreateApp:
    def test_returns_fastapi_instance(self) -> None:
        from fastapi import FastAPI

        from api.app import create_app

        app = create_app()

        assert isinstance(app, FastAPI)
        assert app.title == "Obsidian RAG Quiz"

    def test_app_has_docs_enabled(self) -> None:
        from api.app import create_app

        app = create_app()

        assert app.docs_url is not None
        assert app.openapi_url is not None


class TestContainerQuizStores:
    def test_creates_quiz_session_store_with_engine(self) -> None:
        from quiz.infrastructure.sql_quiz_session_store import SqlQuizSessionStore

        engine = _setup_db()
        container = _make_container_with(engine=engine)

        store = container.quiz_session_store
        assert isinstance(store, SqlQuizSessionStore)
        assert store._engine is engine

    def test_creates_quiz_answer_store_with_engine(self) -> None:
        from quiz.infrastructure.sql_quiz_answer_store import SqlQuizAnswerStore

        engine = _setup_db()
        container = _make_container_with(engine=engine)

        assert isinstance(container.quiz_answer_store, SqlQuizAnswerStore)
        assert container.quiz_answer_store._engine is engine

    def test_creates_progress_update_store(self) -> None:
        from quiz.infrastructure.sql_progress_update_store import (
            SqlProgressUpdateStore,
        )

        engine = _setup_db()
        container = _make_container_with(engine=engine)

        assert isinstance(container.progress_update_store, SqlProgressUpdateStore)
        assert container.progress_update_store._engine is engine

    def test_creates_summary_test_result_store(self) -> None:
        from quiz.infrastructure.sql_summary_test_result_store import (
            SqlSummaryTestResultStore,
        )

        container = _make_container()

        assert isinstance(
            container.summary_test_result_store, SqlSummaryTestResultStore,
        )


class TestContainerRoadmapStores:
    def test_creates_roadmap_stores_with_engine(self) -> None:
        from roadmap.infrastructure.sql_roadmap_item_crud_store import (
            SqlRoadmapItemCrudStore,
        )
        from roadmap.infrastructure.sql_roadmap_persistence_writer import (
            SqlRoadmapPersistenceWriter,
        )
        from roadmap.infrastructure.sql_roadmap_retrieval_reader import (
            SqlRoadmapRetrievalReader,
        )

        engine = _setup_db()
        container = _make_container_with(engine=engine)

        assert isinstance(
            container.roadmap_persistence_writer, SqlRoadmapPersistenceWriter,
        )
        assert container.roadmap_persistence_writer._engine is engine
        assert isinstance(
            container.roadmap_retrieval_reader, SqlRoadmapRetrievalReader,
        )
        assert isinstance(container.roadmap_item_crud_store, SqlRoadmapItemCrudStore)

    def test_creates_job_status_store(self) -> None:
        from roadmap.infrastructure.in_memory_job_status_store import (
            InMemoryJobStatusStore,
        )

        container = _make_container()

        assert isinstance(container.job_status_store, InMemoryJobStatusStore)

    def test_creates_topic_store(self) -> None:
        from roadmap.infrastructure.sql_topic_store import SqlTopicStore

        container = _make_container()

        assert isinstance(container.topic_store, SqlTopicStore)


class TestContainerIngestionStores:
    def test_creates_ingestion_feedback_store(self) -> None:
        from ingestion.infrastructure.sql_ingestion_feedback_store import (
            SqlIngestionFeedbackStore,
        )

        container = _make_container()

        assert isinstance(
            container.ingestion_feedback_store, SqlIngestionFeedbackStore,
        )

    def test_creates_diff_snapshot_store(self) -> None:
        from ingestion.infrastructure.sql_file_diff_snapshot_store import (
            SqlFileDiffSnapshotStore,
        )

        container = _make_container()

        assert isinstance(container.diff_snapshot_store, SqlFileDiffSnapshotStore)


class TestContainerLlmClients:
    def test_creates_llm_clients_with_shared_transport(self) -> None:
        from quiz.infrastructure.codex_llm_adapters import (
            CodexAnswerEvaluationLlm,
            CodexQuestionSetDesignLlm,
        )

        container = _make_container()

        assert isinstance(container.question_set_design_llm, CodexQuestionSetDesignLlm)
        assert isinstance(container.answer_evaluation_llm, CodexAnswerEvaluationLlm)
        assert (
            container.question_set_design_llm._transport
            is container.answer_evaluation_llm._transport
        )

    def test_transport_receives_codex_base_url(self) -> None:
        url = "http://custom-codex:9999"
        container = _make_container_with(codex_base_url=url)

        assert container.transport._base_url == url

    def test_creates_roadmap_generation_llm(self) -> None:
        from roadmap.infrastructure.codex_roadmap_generation_llm import (
            CodexRoadmapGenerationLlm,
        )

        container = _make_container()

        assert isinstance(
            container.roadmap_generation_llm, CodexRoadmapGenerationLlm,
        )


class _FakeEmbedder:
    def embed(self, texts: list[str]) -> list[list[float]]:
        return [[0.1] for _ in texts]


class TestContainerChroma:
    def test_creates_chroma_based_instances_with_collection(self) -> None:
        from ingestion.infrastructure.chroma_chunk_store import ChromaChunkStore
        from quiz.infrastructure.chroma_explanation_rag import (
            ChromaExplanationRagClient,
        )
        from roadmap.infrastructure.chroma_note_topic_reader import (
            ChromaNoteTopicReader,
        )

        chroma = _FakeChromaCollection()
        embedder = _FakeEmbedder()
        container = _make_container_with(
            chroma_collection=chroma, embedder=embedder,
        )

        assert isinstance(container.explanation_rag_client, ChromaExplanationRagClient)
        assert isinstance(container.note_topic_reader, ChromaNoteTopicReader)
        assert isinstance(container.chunk_store, ChromaChunkStore)
        assert container.note_topic_reader._collection is chroma

    def test_rag_client_is_none_without_embedder(self) -> None:
        container = _make_container()

        assert container.explanation_rag_client is None


class TestContainerLifecycle:
    def test_uuid_generator_produces_uuids(self) -> None:
        from uuid import UUID

        container = _make_container()

        assert isinstance(container.uuid_generator.generate(), UUID)

    def test_shutdown_stops_executor(self) -> None:
        container = _make_container()

        container.shutdown()

        with pytest.raises(RuntimeError):
            container.executor.submit(lambda: None)

    def test_executor_is_thread_pool(self) -> None:
        container = _make_container()

        assert isinstance(container.executor, ThreadPoolExecutor)
        container.shutdown()

    def test_job_scheduler_shares_container_executor(self) -> None:
        from roadmap.infrastructure.thread_pool_scheduler import (
            ThreadPoolJobScheduler,
        )

        container = _make_container()

        assert isinstance(container.job_scheduler, ThreadPoolJobScheduler)
        assert container.job_scheduler._executor is container.executor
        container.shutdown()


def _make_container_with(
    *,
    engine: Engine | None = None,
    chroma_collection: object | None = None,
    codex_base_url: str = "http://localhost:11111",
    embedder: object | None = None,
) -> object:
    from api.dependencies import Container

    return Container(
        engine=engine if engine is not None else _setup_db(),
        chroma_collection=(
            chroma_collection
            if chroma_collection is not None
            else _FakeChromaCollection()
        ),
        codex_base_url=codex_base_url,
        embedder=embedder,
    )
