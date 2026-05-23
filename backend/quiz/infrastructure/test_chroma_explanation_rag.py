"""ChromaExplanationRagClient のテスト。"""

from __future__ import annotations


class FakeEmbedder:
    def embed(self, texts: list[str]) -> list[list[float]]:
        return [[0.1, 0.2, 0.3] for _ in texts]


class FakeCollection:
    def __init__(self, documents: list[list[str]]) -> None:
        self._documents = documents
        self.last_query_embeddings: list[list[float]] = []
        self.last_n_results: int = 0

    def query(
        self,
        query_embeddings: list[list[float]],
        n_results: int,
    ) -> dict:
        self.last_query_embeddings = query_embeddings
        self.last_n_results = n_results
        return {"documents": self._documents}


class TestChromaExplanationRagClient:
    def test_returns_documents(self) -> None:
        from quiz.infrastructure.chroma_explanation_rag import (
            ChromaExplanationRagClient,
        )

        collection = FakeCollection([["chunk1", "chunk2"]])
        client = ChromaExplanationRagClient(collection, FakeEmbedder())

        result = client.search_related_chunks("ジェネリクスとは")

        assert result == ["chunk1", "chunk2"]
        assert len(collection.last_query_embeddings) == 1
        assert collection.last_query_embeddings[0] == [0.1, 0.2, 0.3]

    def test_returns_empty_for_no_results(self) -> None:
        from quiz.infrastructure.chroma_explanation_rag import (
            ChromaExplanationRagClient,
        )

        collection = FakeCollection([[]])
        client = ChromaExplanationRagClient(collection, FakeEmbedder())

        result = client.search_related_chunks("query")

        assert result == []

    def test_custom_n_results(self) -> None:
        from quiz.infrastructure.chroma_explanation_rag import (
            ChromaExplanationRagClient,
        )

        collection = FakeCollection([["doc1"]])
        client = ChromaExplanationRagClient(collection, FakeEmbedder(), n_results=10)

        client.search_related_chunks("query")

        assert collection.last_n_results == 10
