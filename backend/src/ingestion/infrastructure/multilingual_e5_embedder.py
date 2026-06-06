"""EmbeddingModel Protocol の multilingual-e5-large concrete 実装。"""

from __future__ import annotations

from typing import TYPE_CHECKING

from ingestion.domain.embedder_types import EmbeddingModelCallError

if TYPE_CHECKING:
    from sentence_transformers import SentenceTransformer


class MultilingualE5Embedder:
    def __init__(self, model: SentenceTransformer) -> None:
        self._model = model

    def embed(self, texts: list[str]) -> list[list[float]]:
        try:
            embeddings = self._model.encode(texts)
            return [vec.tolist() for vec in embeddings]
        except Exception as exc:
            msg = f"embedding failed: {exc}"
            raise EmbeddingModelCallError(msg) from exc


__all__ = ["MultilingualE5Embedder"]
