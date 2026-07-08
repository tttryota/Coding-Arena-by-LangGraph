from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Protocol, runtime_checkable

__all__ = [
    "PresetTopicRecord",
    "StoredTopicRecord",
    "TopicCandidate",
    "TopicListingEmptyTopicNameError",
    "TopicPresetReader",
    "TopicStore",
]


@dataclass(frozen=True)
class TopicCandidate:
    name: str
    source: Literal["preset", "manual"]


@dataclass(frozen=True)
class PresetTopicRecord:
    name: str
    canonical_name: str


@dataclass(frozen=True)
class StoredTopicRecord:
    name: str
    canonical_name: str
    source: Literal["preset", "manual"]


class TopicListingEmptyTopicNameError(Exception):
    pass


@runtime_checkable
class TopicPresetReader(Protocol):
    def list_preset_topics(self) -> list[PresetTopicRecord]: ...


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
