from __future__ import annotations

import unicodedata

from roadmap.domain.topic_listing_types import (
    TopicCandidate,
    TopicListingEmptyTopicNameError,
    TopicPresetReader,
    TopicStore,
)

__all__ = [
    "list_topic_candidates",
    "register_manual_topic",
]

_SOURCE_PRIORITY: dict[str, int] = {"preset": 0, "manual": 1}


def _to_canonical(name: str) -> str:
    return unicodedata.normalize("NFKC", name).casefold()


def list_topic_candidates(
    *,
    preset_reader: TopicPresetReader,
    topic_store: TopicStore,
) -> list[TopicCandidate]:
    merged: dict[str, tuple[str, str]] = {}

    for preset in preset_reader.list_preset_topics():
        cn = preset.canonical_name
        if (
            cn not in merged
            or _SOURCE_PRIORITY["preset"] < _SOURCE_PRIORITY[merged[cn][1]]
        ):
            merged[cn] = (preset.name, "preset")

    for manual in topic_store.list_manual_topics():
        cn = manual.canonical_name
        if (
            cn not in merged
            or _SOURCE_PRIORITY["manual"] < _SOURCE_PRIORITY[merged[cn][1]]
        ):
            merged[cn] = (manual.name, "manual")

    return [
        TopicCandidate(name=name, source=source)  # type: ignore[arg-type]
        for _, (name, source) in sorted(merged.items())
    ]


def register_manual_topic(
    raw_name: str,
    *,
    topic_store: TopicStore,
) -> TopicCandidate:
    normalized_name = raw_name.strip()
    if not normalized_name:
        raise TopicListingEmptyTopicNameError

    canonical_name = _to_canonical(normalized_name)

    existing = topic_store.find_topic_by_canonical_name(canonical_name)
    if existing is not None:
        return TopicCandidate(name=existing.name, source=existing.source)

    topic_store.create_manual_topic(
        name=normalized_name,
        canonical_name=canonical_name,
    )
    return TopicCandidate(name=normalized_name, source="manual")
