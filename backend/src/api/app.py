"""FastAPI app factory。"""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import TYPE_CHECKING

from fastapi import FastAPI

from api.routers import competitive, ingestion, quiz, roadmap

if TYPE_CHECKING:
    from collections.abc import AsyncIterator

    from api.dependencies import Container


@asynccontextmanager
async def _lifespan(app: FastAPI) -> AsyncIterator[None]:
    yield
    container = getattr(app.state, "container", None)
    if container is not None and hasattr(container, "shutdown"):
        container.shutdown()


def create_app(container: Container | None = None) -> FastAPI:
    app = FastAPI(title="Obsidian RAG Quiz", lifespan=_lifespan)
    if container is not None:
        app.state.container = container
    app.include_router(quiz.router)
    app.include_router(roadmap.router)
    app.include_router(ingestion.router)
    app.include_router(competitive.router)
    return app


__all__ = ["create_app"]
