"""NoteTopicReader + TopicNoteCountReader Protocol の ChromaDB concrete 実装。"""

from __future__ import annotations

import unicodedata
from typing import Protocol

from roadmap.domain.topic_listing_types import NoteTopicRecord, TopicNoteCountRecord


class ChromaMetadataCollection(Protocol):
    def get(self, include: list[str]) -> dict: ...


class ChromaNoteTopicReader:
    def __init__(self, collection: ChromaMetadataCollection) -> None:
        self._collection = collection

    def list_note_topics(self) -> list[NoteTopicRecord]:
        results = self._collection.get(include=["metadatas"])
        metadatas = results.get("metadatas", [])
        seen: dict[str, str] = {}
        for meta in metadatas:
            if not isinstance(meta, dict):
                continue
            for tag in _extract_tags(meta):
                canonical = _normalize(tag)
                if canonical and canonical not in seen:
                    seen[canonical] = tag
        return [
            NoteTopicRecord(name=name, canonical_name=canonical)
            for canonical, name in sorted(seen.items())
        ]

    def list_note_counts(
        self,
        canonical_names: list[str],
    ) -> list[TopicNoteCountRecord]:
        results = self._collection.get(include=["metadatas"])
        metadatas = results.get("metadatas", [])
        # source_path 単位でユニーク化してノート数をカウント(chunk 重複を排除)
        tag_sources: dict[str, set[str]] = {cn: set() for cn in canonical_names}
        for meta in metadatas:
            if not isinstance(meta, dict):
                continue
            source_path = meta.get("source_path", "")
            if not source_path:
                continue
            for tag in _extract_tags(meta):
                canonical = _normalize(tag)
                if canonical in tag_sources:
                    tag_sources[canonical].add(source_path)
        return [
            TopicNoteCountRecord(canonical_name=cn, note_count=len(sources))
            for cn, sources in tag_sources.items()
        ]


def _normalize(text: str) -> str:
    return unicodedata.normalize("NFKC", text.strip()).casefold()


def _extract_tags(meta: dict) -> list[str]:
    tags = meta.get("tags", [])
    if isinstance(tags, list):
        return [t for t in tags if isinstance(t, str)]
    if isinstance(tags, str) and tags:
        return [t.strip() for t in tags.split(",")]
    return []


__all__ = ["ChromaNoteTopicReader"]
