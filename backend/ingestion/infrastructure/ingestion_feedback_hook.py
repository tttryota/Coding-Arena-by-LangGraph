"""PostIngestionHook concrete: ファイル取り込み後にフィードバック生成。"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

import structlog

from ingestion.application.ingestion_feedback import generate_for_file
from ingestion.domain.ingestion_feedback_types import (
    IngestionFeedbackChunkInput,
    IngestionFeedbackGenerateInput,
    RoadmapCandidate,
)

logger = structlog.get_logger(__name__)

if TYPE_CHECKING:
    from uuid import UUID

    from ingestion.domain.ingestion_feedback_types import (
        IngestionFeedbackLlmClient,
        IngestionFeedbackWriter,
        RoadmapItemReader,
    )
    from roadmap.domain.roadmap_retrieval_types import (
        RoadmapItemRecord,
        RoadmapRecord,
        RoadmapRetrievalReader,
    )

_DEFAULT_MINIMUM_CHUNK_CHARACTERS = 50


class RoadmapItemReaderAdapter:
    """SqlRoadmapRetrievalReader をラップして RoadmapItemReader Protocol を満たす。"""

    def __init__(self, retrieval_reader: RoadmapRetrievalReader) -> None:
        self._reader = retrieval_reader

    def list_items(self) -> list[RoadmapCandidate]:
        roadmaps: list[RoadmapRecord] = self._reader.find_all_roadmaps()
        candidates: list[RoadmapCandidate] = []
        for roadmap in roadmaps:
            title_by_id: dict[UUID, str] = {
                item.id: item.title for item in roadmap.items
            }
            parent_by_id: dict[UUID, UUID | None] = {
                item.id: item.parent_id for item in roadmap.items
            }
            for item in roadmap.items:
                display_path = _build_display_path(
                    item, roadmap.topic, title_by_id, parent_by_id,
                )
                candidates.append(
                    RoadmapCandidate(id=item.id, display_path=display_path),
                )
        return candidates


_MAX_DEPTH = 10


def _build_display_path(
    item: RoadmapItemRecord,
    topic: str,
    title_by_id: dict[UUID, str],
    parent_by_id: dict[UUID, UUID | None],
) -> str:
    """ツリーを辿って "topic > parent > ... > item" のパスを構築する。"""
    parts: list[str] = [item.title]
    current_parent = item.parent_id
    seen: set[UUID] = set()
    while current_parent is not None and len(parts) < _MAX_DEPTH:
        if current_parent in seen:
            break
        seen.add(current_parent)
        parts.append(title_by_id.get(current_parent, "?"))
        current_parent = parent_by_id.get(current_parent)
    parts.append(topic)
    parts.reverse()
    return " > ".join(parts)


class IngestionFeedbackHook:
    """PostIngestionHook Protocol の concrete 実装。"""

    def __init__(
        self,
        llm_client: IngestionFeedbackLlmClient,
        roadmap_reader: RoadmapItemReader,
        writer: IngestionFeedbackWriter,
    ) -> None:
        self._llm_client = llm_client
        self._roadmap_reader = roadmap_reader
        self._writer = writer

    def on_file_ingested(
        self,
        source_path: str,
        chunk_data: list[tuple[int, str]],
    ) -> None:
        chunks = [
            IngestionFeedbackChunkInput(chunk_index=idx, text=text)
            for idx, text in chunk_data
        ]
        feedback_input = IngestionFeedbackGenerateInput(
            source_path=source_path,
            chunks=chunks,
            minimum_chunk_characters=_DEFAULT_MINIMUM_CHUNK_CHARACTERS,
            generated_at=datetime.now(tz=UTC).isoformat(),
        )
        result = generate_for_file(
            feedback_input,
            llm_client=self._llm_client,
            roadmap_reader=self._roadmap_reader,
            writer=self._writer,
        )
        logger.info(
            "ingestion_feedback_hook_completed",
            source_path=source_path,
            status=result.status,
            feedback_id=str(result.created_feedback.id) if result.created_feedback else None,
        )


__all__ = ["IngestionFeedbackHook", "RoadmapItemReaderAdapter"]
