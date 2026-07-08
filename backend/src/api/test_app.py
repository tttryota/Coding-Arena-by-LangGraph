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


def _make_container() -> object:
    from api.dependencies import Container

    return Container(engine=_setup_db())


class TestCreateApp:
    def test_returns_fastapi_instance(self) -> None:
        """テスト対象: create_app 関数。
        テストケース: 個別条件での処理を検証する。
        期待結果: 想定どおりの処理結果が得られる。"""
        from fastapi import FastAPI

        from api.app import create_app

        app = create_app()

        assert isinstance(app, FastAPI)
        assert app.title == "Obsidian Quiz"

    def test_app_has_docs_enabled(self) -> None:
        """テスト対象: create_app 関数。
        テストケース: 個別条件での処理を検証する。
        期待結果: 想定どおりの処理結果が得られる。"""
        from api.app import create_app

        app = create_app()

        assert app.docs_url is not None
        assert app.openapi_url is not None


class TestContainerQuizStores:
    def test_creates_quiz_session_store_with_engine(self) -> None:
        """テスト対象: クイズ用コンテナ構築処理。
        テストケース: 個別条件での処理を検証する。
        期待結果: 想定どおりの処理結果が得られる。"""
        from quiz.infrastructure.sql_quiz_session_store import SqlQuizSessionStore

        engine = _setup_db()
        container = _make_container_with(engine=engine)

        store = container.quiz_session_store
        assert isinstance(store, SqlQuizSessionStore)
        assert store._engine is engine

    def test_creates_quiz_answer_store_with_engine(self) -> None:
        """テスト対象: クイズ用コンテナ構築処理。
        テストケース: 個別条件での処理を検証する。
        期待結果: 想定どおりの処理結果が得られる。"""
        from quiz.infrastructure.sql_quiz_answer_store import SqlQuizAnswerStore

        engine = _setup_db()
        container = _make_container_with(engine=engine)

        assert isinstance(container.quiz_answer_store, SqlQuizAnswerStore)
        assert container.quiz_answer_store._engine is engine

    def test_creates_progress_update_store(self) -> None:
        """テスト対象: クイズ用コンテナ構築処理。
        テストケース: 個別条件での処理を検証する。
        期待結果: 想定どおりの処理結果が得られる。"""
        from quiz.infrastructure.sql_progress_update_store import (
            SqlProgressUpdateStore,
        )

        engine = _setup_db()
        container = _make_container_with(engine=engine)

        assert isinstance(container.progress_update_store, SqlProgressUpdateStore)
        assert container.progress_update_store._engine is engine

    def test_creates_summary_test_result_store(self) -> None:
        """テスト対象: クイズ用コンテナ構築処理。
        テストケース: 個別条件での処理を検証する。
        期待結果: 想定どおりの処理結果が得られる。"""
        from quiz.infrastructure.sql_summary_test_result_store import (
            SqlSummaryTestResultStore,
        )

        container = _make_container()

        assert isinstance(
            container.summary_test_result_store, SqlSummaryTestResultStore,
        )


class TestContainerRoadmapStores:
    def test_creates_roadmap_stores_with_engine(self) -> None:
        """テスト対象: ロードマップ用コンテナ構築処理。
        テストケース: 個別条件での処理を検証する。
        期待結果: 想定どおりの処理結果が得られる。"""
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
        """テスト対象: ロードマップ用コンテナ構築処理。
        テストケース: 個別条件での処理を検証する。
        期待結果: 想定どおりの処理結果が得られる。"""
        from roadmap.infrastructure.in_memory_job_status_store import (
            InMemoryJobStatusStore,
        )

        container = _make_container()

        assert isinstance(container.job_status_store, InMemoryJobStatusStore)

    def test_creates_topic_store(self) -> None:
        """テスト対象: ロードマップ用コンテナ構築処理。
        テストケース: 個別条件での処理を検証する。
        期待結果: 想定どおりの処理結果が得られる。"""
        from roadmap.infrastructure.sql_topic_store import SqlTopicStore

        container = _make_container()

        assert isinstance(container.topic_store, SqlTopicStore)


class TestContainerLlmClients:
    def test_creates_llm_clients_with_shared_transport(self) -> None:
        """テスト対象: LLM クライアント構築処理。
        テストケース: 個別条件での処理を検証する。
        期待結果: 想定どおりの処理結果が得られる。"""
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

    def test_creates_roadmap_generation_llm(self) -> None:
        """テスト対象: LLM クライアント構築処理。
        テストケース: 個別条件での処理を検証する。
        期待結果: 想定どおりの処理結果が得られる。"""
        from roadmap.infrastructure.codex_roadmap_generation_llm import (
            CodexRoadmapGenerationLlm,
        )

        container = _make_container()

        assert isinstance(
            container.roadmap_generation_llm, CodexRoadmapGenerationLlm,
        )


class TestContainerLifecycle:
    def test_uuid_generator_produces_uuids(self) -> None:
        """テスト対象: コンテナのライフサイクル処理。
        テストケース: 個別条件での処理を検証する。
        期待結果: 想定どおりの処理結果が得られる。"""
        from uuid import UUID

        container = _make_container()

        assert isinstance(container.uuid_generator.generate(), UUID)

    def test_shutdown_stops_executor(self) -> None:
        """テスト対象: コンテナのライフサイクル処理。
        テストケース: 個別条件での処理を検証する。
        期待結果: 想定どおりの処理結果が得られる。"""
        container = _make_container()

        container.shutdown()

        with pytest.raises(RuntimeError):
            container.executor.submit(lambda: None)

    def test_shutdown_closes_transport(self) -> None:
        """テスト対象: コンテナ shutdown 時の LLM transport 後始末。"""
        from unittest.mock import MagicMock

        container = _make_container()
        transport = MagicMock()
        container.transport = transport

        container.shutdown()

        transport.close.assert_called_once()

    def test_executor_is_thread_pool(self) -> None:
        """テスト対象: コンテナのライフサイクル処理。
        テストケース: 個別条件での処理を検証する。
        期待結果: 想定どおりの処理結果が得られる。"""
        container = _make_container()

        assert isinstance(container.executor, ThreadPoolExecutor)
        container.shutdown()

    def test_job_scheduler_shares_container_executor(self) -> None:
        """テスト対象: コンテナのライフサイクル処理。
        テストケース: 個別条件での処理を検証する。
        期待結果: 想定どおりの処理結果が得られる。"""
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
) -> object:
    from api.dependencies import Container

    return Container(engine=engine if engine is not None else _setup_db())
