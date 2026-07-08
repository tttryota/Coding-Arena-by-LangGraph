"""インテグレーションテスト共通フィクスチャ。

TestClient → FastAPI Router → Application 層 → 実 Infrastructure
LLM のみ ScenarioLlmTransport でスタブする。
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from infrastructure.rdb.base import Base

if TYPE_CHECKING:
    from collections.abc import Iterator

    from sqlalchemy import Engine

    from tests.integration.stubs.scenario_llm_transport import ScenarioLlmTransport


@pytest.fixture(scope="session")
def engine() -> Engine:
    """in-memory SQLite + 全テーブル作成 + algo_themes fixture 投入。"""
    import json
    from pathlib import Path

    import infrastructure.rdb.models  # noqa: F401  — register all ORM models

    eng = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(eng)

    # algo_themes fixture を投入
    json_path = Path(__file__).resolve().parents[2] / "data" / "algo_themes.json"
    if json_path.exists():
        themes = json.loads(json_path.read_text(encoding="utf-8"))
        from infrastructure.rdb.models import AlgoThemeModel

        with Session(eng) as session:
            for t in themes:
                session.add(AlgoThemeModel(
                    id=t["id"], category=t["category"],
                    label=t["label"], display_order=t["display_order"],
                ))
            session.commit()

    return eng


# algo_themes はマスタデータなのでクリーンアップ対象外
_PRESERVED_TABLES = {"algo_themes"}


@pytest.fixture
def clean_tables(engine: Engine) -> Iterator[None]:
    """各テスト前に全テーブルをクリーンアップ (マスタデータ除外)。"""
    yield
    with engine.begin() as conn:
        for table in reversed(Base.metadata.sorted_tables):
            if table.name not in _PRESERVED_TABLES:
                conn.execute(text(f"DELETE FROM {table.name}"))  # noqa: S608


@pytest.fixture
def scenario_transport() -> ScenarioLlmTransport:
    """テストごとに新しい ScenarioLlmTransport を作成。"""
    from tests.integration.stubs.scenario_llm_transport import ScenarioLlmTransport

    return ScenarioLlmTransport()


@pytest.fixture
def integration_container(
    engine: Engine,
    scenario_transport: ScenarioLlmTransport,
    clean_tables: None,  # noqa: ARG001
) -> Iterator[object]:
    """実 engine + スタブ transport の Container。"""
    from api.dependencies import Container

    container = Container(engine=engine)
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
            # adapter 自体は本物を使い、transport だけ差し替えることで
            # prompt 組み立てと JSON 検証の実コードをそのまま通す。
            obj._transport = transport
