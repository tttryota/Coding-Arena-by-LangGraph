"""インテグレーションテスト共通フィクスチャ。

TestClient → FastAPI Router → Application 層 → 実 Infrastructure
LLM のみ ScenarioLlmTransport でスタブ、Embedder は FixedVectorEmbedder。
"""

from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import uuid4

import chromadb
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.pool import StaticPool

from infrastructure.rdb.base import Base

if TYPE_CHECKING:
    from collections.abc import Iterator

    from sqlalchemy import Engine

    from tests.integration.stubs.scenario_llm_transport import ScenarioLlmTransport


@pytest.fixture(scope="session")
def engine() -> Engine:
    """in-memory SQLite + 全テーブル作成。"""
    import infrastructure.rdb.models  # noqa: F401  — register all ORM models

    eng = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(eng)
    return eng


@pytest.fixture
def clean_tables(engine: Engine) -> Iterator[None]:
    """各テスト前に全テーブルをクリーンアップ。"""
    yield
    with engine.begin() as conn:
        for table in reversed(Base.metadata.sorted_tables):
            conn.execute(text(f"DELETE FROM {table.name}"))  # noqa: S608


@pytest.fixture
def chroma_collection() -> Iterator[object]:
    """テストごとにユニークな EphemeralClient コレクションを作成。"""
    chroma_client = chromadb.EphemeralClient()
    collection_name = f"test_{uuid4().hex[:12]}"
    collection = chroma_client.get_or_create_collection(
        name=collection_name,
        metadata={"hnsw:space": "cosine"},
    )
    yield collection
    chroma_client.delete_collection(collection_name)


@pytest.fixture
def scenario_transport() -> ScenarioLlmTransport:
    """テストごとに新しい ScenarioLlmTransport を作成。"""
    from tests.integration.stubs.scenario_llm_transport import ScenarioLlmTransport

    return ScenarioLlmTransport()


@pytest.fixture
def integration_container(
    engine: Engine,
    chroma_collection: object,
    scenario_transport: ScenarioLlmTransport,
    clean_tables: None,  # noqa: ARG001
) -> Iterator[object]:
    """実 engine + 実 chroma + スタブ transport + スタブ embedder の Container。"""
    from api.dependencies import Container
    from tests.integration.stubs.fixed_embedder import FixedVectorEmbedder

    embedder = FixedVectorEmbedder()
    container = Container(
        engine=engine,
        chroma_collection=chroma_collection,
        embedder=embedder,
    )
    _replace_transport(container, scenario_transport)
    try:
        yield container
    finally:
        container.shutdown()


@pytest.fixture
def client(integration_container: object) -> Iterator[TestClient]:
    """インテグレーションテスト用 TestClient。"""
    from api.app import create_app

    app = create_app(integration_container)  # type: ignore[arg-type]
    with TestClient(app, raise_server_exceptions=False) as tc:
        yield tc


def _replace_transport(container: object, transport: object) -> None:
    """Container 内の全 LLM クライアントのトランスポートを差し替える。"""
    setattr(container, "transport", transport)  # noqa: B010
    for attr_name in dir(container):
        obj = getattr(container, attr_name, None)
        if obj is not None and hasattr(obj, "_transport"):
            obj._transport = transport
