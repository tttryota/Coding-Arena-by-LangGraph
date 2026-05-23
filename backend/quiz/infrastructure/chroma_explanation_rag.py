"""ExplanationRagClient Protocol の ChromaDB concrete 実装。"""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from ingestion.domain.embedder_types import EmbeddingModel


class ChromaQueryCollection(Protocol):
    def query(
        self,
        query_embeddings: list[list[float]],
        n_results: int,
    ) -> dict: ...


class ChromaExplanationRagClient:
    def __init__(
        self,
        collection: ChromaQueryCollection,
        embedder: EmbeddingModel,
        *,
        n_results: int = 5,
    ) -> None:
        self._collection = collection
        self._embedder = embedder
        self._n_results = n_results

    def search_related_chunks(self, query: str) -> list[str]:
        from quiz.application.explanation_generation_types import (
            ExplanationGenerationError,
        )

        try:
            embeddings = self._embedder.embed([query])
            results = self._collection.query(
                query_embeddings=embeddings,
                n_results=self._n_results,
            )
            documents = results.get("documents")
            if documents is None or not isinstance(documents, list) or not documents:
                return []
            first = documents[0]
            if not isinstance(first, list):
                raise ExplanationGenerationError(
                    error_code="rag_response_format_error",
                    message=f"unexpected documents format: {type(first).__name__}",
                )
            return [doc for doc in first if isinstance(doc, str)]
        except ExplanationGenerationError:
            raise
        except Exception as exc:
            raise ExplanationGenerationError(
                error_code="rag_search_failed",
                message=f"RAG search failed: {exc}",
            ) from exc


__all__ = ["ChromaExplanationRagClient"]
