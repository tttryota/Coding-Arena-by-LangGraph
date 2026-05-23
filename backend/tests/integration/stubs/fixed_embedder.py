"""FixedVectorEmbedder: 固定ベクトルを返すテスト用 EmbeddingModel。

EmbeddingModel Protocol (embed(texts) -> list[list[float]]) を満たす。
全テキストに対して同一の 384 次元正規化ベクトルを返す。
"""

from __future__ import annotations

import math

DIMENSION = 384


class FixedVectorEmbedder:
    """テスト用の固定ベクトル Embedder。"""

    def __init__(self, dimension: int = DIMENSION) -> None:
        self._dimension = dimension
        value = 1.0 / math.sqrt(dimension)
        self._vector = [value] * dimension

    def embed(self, texts: list[str]) -> list[list[float]]:
        return [list(self._vector) for _ in texts]

    @property
    def dimension(self) -> int:
        return self._dimension


__all__ = ["FixedVectorEmbedder"]
