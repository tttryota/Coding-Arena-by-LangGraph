from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


class EmbeddingBatchInputError(Exception):
    pass


class EmbeddingModelCallError(Exception):
    pass


class EmbeddingResponseCountMismatchError(Exception):
    pass


class EmbeddingVectorFormatError(Exception):
    pass


class EmbeddingModel(Protocol):
    def embed(self, texts: list[str]) -> list[list[float]]: ...


@dataclass(frozen=True)
class ChunkEmbeddingInput:
    chunk_index: int
    text: str


@dataclass(frozen=True)
class ChunkEmbeddingResult:
    chunk_index: int
    embedding: list[float]


@dataclass(frozen=True)
class EmbeddingBatchInput:
    chunks: list[ChunkEmbeddingInput]
    embedding_model: EmbeddingModel
    source_path: str | None = None
