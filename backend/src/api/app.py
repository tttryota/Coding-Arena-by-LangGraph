"""FastAPI app factory。"""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import TYPE_CHECKING

from fastapi import FastAPI

from api.routers import (
    algorithm_foundations,
    competitive,
    quiz,
    roadmap,
    sql_dojo,
)

if TYPE_CHECKING:
    from collections.abc import AsyncIterator

    from api.dependencies import Container


@asynccontextmanager
async def _lifespan(app: FastAPI) -> AsyncIterator[None]:
    """アプリ終了時にコンテナの後始末だけを担う。"""
    yield
    container = getattr(app.state, "container", None)
    if container is not None and hasattr(container, "shutdown"):
        container.shutdown()


def create_app(container: Container | None = None) -> FastAPI:
    """router を束ねた FastAPI アプリを生成する。

    container を差し込める形にしておくことで、実運用では本物の依存を使い、
    テストでは差し替え済みの container をそのまま注入できる。
    """
    app = FastAPI(title="Obsidian Quiz", lifespan=_lifespan)
    if container is not None:
        app.state.container = container
    app.include_router(quiz.router)
    app.include_router(roadmap.router)
    app.include_router(competitive.router)
    app.include_router(algorithm_foundations.router)
    app.include_router(sql_dojo.router)
    return app


__all__ = ["create_app"]
