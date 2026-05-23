"""FastAPI app factory。"""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import TYPE_CHECKING

from fastapi import FastAPI

if TYPE_CHECKING:
    from collections.abc import AsyncIterator


@asynccontextmanager
async def _lifespan(app: FastAPI) -> AsyncIterator[None]:
    yield
    container = getattr(app.state, "container", None)
    if container is not None and hasattr(container, "shutdown"):
        container.shutdown()


def create_app() -> FastAPI:
    return FastAPI(title="Obsidian RAG Quiz", lifespan=_lifespan)


__all__ = ["create_app"]
