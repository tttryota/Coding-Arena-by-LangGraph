"""BatchExecutionConfig 向け Protocol アダプタ群。

機能モジュールの関数ベース API を Protocol インターフェースに橋渡しする。
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ingestion.application.tagger import (
        ChunkTaggingResult,
        LlmTagClassifier,
        TaggingPromptStrategy,
    )
    from ingestion.domain.chunk_splitter import ChunkSplitResult, TokenCounter
    from ingestion.domain.embedder_types import ChunkEmbeddingResult, EmbeddingModel
    from ingestion.infrastructure.file_diff_detector import (
        FileDiffResult,
        FileDiffSnapshotStore,
    )


class FileDiffDetectorAdapter:
    """FileDiffDetector Protocol の adapter。snapshot_store を束縛する。"""

    def __init__(self, snapshot_store: FileDiffSnapshotStore) -> None:
        self._snapshot_store = snapshot_store

    def detect(self, target_path: str | Path) -> FileDiffResult:
        from ingestion.infrastructure.file_diff_detector import detect

        return detect(target_path, self._snapshot_store)


class VaultMarkdownLoaderImpl:
    """VaultMarkdownLoader Protocol の実装。ファイルシステムから読み込む。"""

    def __init__(self, vault_root: str | Path) -> None:
        self._root = Path(vault_root)

    def load(self, source_path: str | Path) -> str:
        full_path = self._root / source_path
        return full_path.read_text(encoding="utf-8")


class ChunkSplitterAdapter:
    """ChunkSplitter Protocol の adapter。token_counter を束縛する。"""

    def __init__(self, token_counter: TokenCounter) -> None:
        self._token_counter = token_counter

    def split(
        self,
        markdown_text: str,
        *,
        source_path: str | None = None,  # noqa: ARG002
    ) -> list[ChunkSplitResult]:
        from ingestion.domain.chunk_splitter import split

        return split(markdown_text, self._token_counter)


class ChunkTaggerAdapter:
    """ChunkTagger Protocol の adapter。prompt_strategy と llm_client を束縛する。"""

    def __init__(
        self,
        prompt_strategy: TaggingPromptStrategy,
        llm_client: LlmTagClassifier,
    ) -> None:
        self._prompt_strategy = prompt_strategy
        self._llm_client = llm_client

    def tag(
        self,
        chunks: list[ChunkSplitResult],
        *,
        source_path: str,
    ) -> list[ChunkTaggingResult]:
        from ingestion.application.tagger import (
            ChunkTaggingInput,
            TaggingBatchInput,
            tag,
        )

        batch_input = TaggingBatchInput(
            chunks=[
                ChunkTaggingInput(chunk_index=i, text=c.content)
                for i, c in enumerate(chunks)
            ],
            existing_tags=[],
            prompt_strategy=self._prompt_strategy,
            llm_client=self._llm_client,
            source_path=source_path,
        )
        return tag(batch_input)


class EmbedderAdapter:
    """Embedder Protocol の adapter。embedding_model を束縛する。"""

    def __init__(self, embedding_model: EmbeddingModel) -> None:
        self._model = embedding_model

    def embed(
        self,
        chunks: list[ChunkSplitResult],
        *,
        source_path: str,
    ) -> list[ChunkEmbeddingResult]:
        from ingestion.application.embedder import embed
        from ingestion.domain.embedder_types import (
            ChunkEmbeddingInput,
            EmbeddingBatchInput,
        )

        batch_input = EmbeddingBatchInput(
            chunks=[
                ChunkEmbeddingInput(chunk_index=i, text=c.content)
                for i, c in enumerate(chunks)
            ],
            embedding_model=self._model,
            source_path=source_path,
        )
        return embed(batch_input)


class DefaultTaggingPromptStrategy:
    """TaggingPromptStrategy Protocol のデフォルト実装。"""

    def build_prompt(self, chunk_text: str, existing_tags: list[str]) -> object:
        return {
            "chunk_text": chunk_text,
            "existing_tags": existing_tags,
        }


class SimpleTokenCounter:
    """TokenCounter Protocol の簡易実装。空白区切りで単語数を数える。"""

    def count(self, text: str) -> int:
        return len(text.split())


__all__ = [
    "ChunkSplitterAdapter",
    "ChunkTaggerAdapter",
    "DefaultTaggingPromptStrategy",
    "EmbedderAdapter",
    "FileDiffDetectorAdapter",
    "SimpleTokenCounter",
    "VaultMarkdownLoaderImpl",
]
