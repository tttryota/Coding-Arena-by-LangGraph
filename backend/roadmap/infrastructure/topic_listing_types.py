from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Protocol, runtime_checkable

__all__ = [
    "NoteTopicReader",
    "NoteTopicRecord",
    "PresetTopicRecord",
    "StoredTopicRecord",
    "TopicCandidate",
    "TopicListingEmptyTopicNameError",
    "TopicNoteCountReader",
    "TopicNoteCountRecord",
    "TopicPresetReader",
    "TopicStore",
]


@dataclass(frozen=True)
class TopicCandidate:
    name: str
    source: Literal["preset", "note", "manual"]
    note_count: int


@dataclass(frozen=True)
class PresetTopicRecord:
    name: str
    canonical_name: str


@dataclass(frozen=True)
class NoteTopicRecord:
    name: str
    canonical_name: str


@dataclass(frozen=True)
class StoredTopicRecord:
    name: str
    canonical_name: str
    source: Literal["preset", "note", "manual"]


@dataclass(frozen=True)
class TopicNoteCountRecord:
    canonical_name: str
    note_count: int


class TopicListingEmptyTopicNameError(Exception):
    pass


@runtime_checkable
class TopicPresetReader(Protocol):
    def list_preset_topics(self) -> list[PresetTopicRecord]: ...


@runtime_checkable
class NoteTopicReader(Protocol):
    def list_note_topics(self) -> list[NoteTopicRecord]: ...


@runtime_checkable
class TopicStore(Protocol):
    def list_manual_topics(self) -> list[StoredTopicRecord]: ...

    def find_topic_by_canonical_name(
        self,
        canonical_name: str,
    ) -> StoredTopicRecord | None: ...

    def create_manual_topic(
        self,
        name: str,
        canonical_name: str,
    ) -> StoredTopicRecord: ...


@runtime_checkable
class TopicNoteCountReader(Protocol):
    def list_note_counts(
        self,
        canonical_names: list[str],
    ) -> list[TopicNoteCountRecord]: ...
