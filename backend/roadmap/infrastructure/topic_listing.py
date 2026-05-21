from __future__ import annotations

import unicodedata

from roadmap.infrastructure.topic_listing_types import (
    NoteTopicReader,
    TopicCandidate,
    TopicListingEmptyTopicNameError,
    TopicNoteCountReader,
    TopicPresetReader,
    TopicStore,
)

__all__ = [
    "list_topic_candidates",
    "register_manual_topic",
]

_SOURCE_PRIORITY: dict[str, int] = {"preset": 0, "manual": 1, "note": 2}


def _to_canonical(name: str) -> str:
    return unicodedata.normalize("NFKC", name).casefold()


def list_topic_candidates(
    *,
    preset_reader: TopicPresetReader,
    note_topic_reader: NoteTopicReader,
    topic_store: TopicStore,
    note_count_reader: TopicNoteCountReader,
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

    for note in note_topic_reader.list_note_topics():
        cn = note.canonical_name
        if (
            cn not in merged
            or _SOURCE_PRIORITY["note"] < _SOURCE_PRIORITY[merged[cn][1]]
        ):
            merged[cn] = (note.name, "note")

    sorted_canonical_names = sorted(merged)
    counts_result = note_count_reader.list_note_counts(sorted_canonical_names)
    count_map: dict[str, int] = {r.canonical_name: r.note_count for r in counts_result}

    entries = [
        (
            cn,
            TopicCandidate(
                name=name,
                source=source,  # type: ignore[arg-type]
                note_count=count_map.get(cn, 0),
            ),
        )
        for cn, (name, source) in merged.items()
    ]

    entries.sort(key=lambda e: (-e[1].note_count, e[0]))
    candidates = [candidate for _, candidate in entries]

    return candidates


def register_manual_topic(
    raw_name: str,
    *,
    topic_store: TopicStore,
    note_count_reader: TopicNoteCountReader,
) -> TopicCandidate:
    normalized_name = raw_name.strip()
    if not normalized_name:
        raise TopicListingEmptyTopicNameError

    canonical_name = _to_canonical(normalized_name)

    existing = topic_store.find_topic_by_canonical_name(canonical_name)
    if existing is not None:
        counts = note_count_reader.list_note_counts([canonical_name])
        count_map = {r.canonical_name: r.note_count for r in counts}
        return TopicCandidate(
            name=existing.name,
            source=existing.source,
            note_count=count_map.get(canonical_name, 0),
        )

    topic_store.create_manual_topic(
        name=normalized_name,
        canonical_name=canonical_name,
    )
    counts = note_count_reader.list_note_counts([canonical_name])
    count_map = {r.canonical_name: r.note_count for r in counts}
    return TopicCandidate(
        name=normalized_name,
        source="manual",
        note_count=count_map.get(canonical_name, 0),
    )
