from __future__ import annotations

import unicodedata
from dataclasses import fields, is_dataclass
from typing import Literal

import pytest

from roadmap.application.topic_listing import (
    list_topic_candidates,
    register_manual_topic,
)
from roadmap.domain.topic_listing_types import (
    PresetTopicRecord,
    StoredTopicRecord,
    TopicCandidate,
    TopicListingEmptyTopicNameError,
    TopicPresetReader,
    TopicStore,
)


class _RecordingPresetReader:
    def __init__(self, *, records: list[PresetTopicRecord]) -> None:
        self._records = list(records)
        self.calls = 0

    def list_preset_topics(self) -> list[PresetTopicRecord]:
        self.calls += 1
        return list(self._records)


class _RecordingTopicStore:
    def __init__(
        self,
        *,
        manual_records: list[StoredTopicRecord] | None = None,
        find_result: StoredTopicRecord | None = None,
        create_result: StoredTopicRecord | None = None,
    ) -> None:
        self._manual_records = list(manual_records or [])
        self._find_result = find_result
        self._create_result = create_result
        self.list_manual_topics_calls = 0
        self.find_calls: list[str] = []
        self.create_calls: list[tuple[str, str]] = []

    def list_manual_topics(self) -> list[StoredTopicRecord]:
        self.list_manual_topics_calls += 1
        return list(self._manual_records)

    def find_topic_by_canonical_name(
        self,
        canonical_name: str,
    ) -> StoredTopicRecord | None:
        self.find_calls.append(canonical_name)
        return self._find_result

    def create_manual_topic(self, name: str, canonical_name: str) -> StoredTopicRecord:
        self.create_calls.append((name, canonical_name))
        if self._create_result is not None:
            return self._create_result
        return StoredTopicRecord(
            name=name,
            canonical_name=canonical_name,
            source="manual",
        )


_preset = PresetTopicRecord


def _stored(
    name: str,
    canonical_name: str,
    source: Literal["preset", "manual"] = "manual",
) -> StoredTopicRecord:
    return StoredTopicRecord(name=name, canonical_name=canonical_name, source=source)


def _candidate(
    name: str,
    source: Literal["preset", "manual"],
) -> TopicCandidate:
    return TopicCandidate(name=name, source=source)


def test_tc_01_public_contracts_match_spec() -> None:
    for cls in (TopicCandidate, PresetTopicRecord, StoredTopicRecord):
        assert is_dataclass(cls)
        assert cls.__dataclass_params__.frozen is True  # type: ignore[attr-defined]

    assert tuple(f.name for f in fields(TopicCandidate)) == ("name", "source")
    assert tuple(f.name for f in fields(PresetTopicRecord)) == ("name", "canonical_name")
    assert tuple(f.name for f in fields(StoredTopicRecord)) == ("name", "canonical_name", "source")

    for cls in (TopicPresetReader, TopicStore):
        assert getattr(cls, "_is_protocol", False) is True

    assert issubclass(TopicListingEmptyTopicNameError, Exception)


def test_tc_02_returns_sorted_presets_and_manual_topics() -> None:
    result = list_topic_candidates(
        preset_reader=_RecordingPresetReader(
            records=[_preset("Docker", "docker"), _preset("TypeScript", "typescript")],
        ),
        topic_store=_RecordingTopicStore(
            manual_records=[_stored("Terraform", "terraform")],
        ),
    )

    assert result == [
        _candidate("Docker", "preset"),
        _candidate("Terraform", "manual"),
        _candidate("TypeScript", "preset"),
    ]


def test_tc_03_prefers_preset_over_manual_for_same_canonical_name() -> None:
    result = list_topic_candidates(
        preset_reader=_RecordingPresetReader(records=[_preset("React", "react")]),
        topic_store=_RecordingTopicStore(
            manual_records=[_stored("React Manual", "react")],
        ),
    )

    assert result == [_candidate("React", "preset")]


def test_tc_04_registers_new_topic_and_returns_candidate() -> None:
    ts = _RecordingTopicStore(
        find_result=None,
        create_result=_stored("Graph Search", "graph search"),
    )

    result = register_manual_topic(" Graph Search ", topic_store=ts)

    assert ts.find_calls == ["graph search"]
    assert ts.create_calls == [("Graph Search", "graph search")]
    assert result == _candidate("Graph Search", "manual")


def test_tc_05_detects_duplicate_via_nfkc_casefold() -> None:
    ts = _RecordingTopicStore(
        find_result=_stored("Terraform", "terraform", source="preset"),
    )

    result = register_manual_topic(
        "\uff54\uff45\uff52\uff52\uff41\uff46\uff4f\uff52\uff4d",
        topic_store=ts,
    )

    assert ts.find_calls == ["terraform"]
    assert ts.create_calls == []
    assert result == _candidate("Terraform", "preset")


def test_tc_06_raises_for_blank_input_without_calling_dependencies() -> None:
    ts = _RecordingTopicStore()

    with pytest.raises(TopicListingEmptyTopicNameError):
        register_manual_topic(" \t\n ", topic_store=ts)

    assert ts.find_calls == []
    assert ts.create_calls == []


def test_tc_07_preserves_internal_whitespace_and_canonicalizes() -> None:
    normalized = "AI\u3000Agent"
    canonical = unicodedata.normalize("NFKC", normalized).casefold()
    ts = _RecordingTopicStore(
        find_result=None,
        create_result=_stored(normalized, canonical),
    )

    result = register_manual_topic("  AI\u3000Agent  ", topic_store=ts)

    assert canonical == "ai agent"
    assert ts.find_calls == [canonical]
    assert ts.create_calls == [(normalized, canonical)]
    assert result == _candidate(normalized, "manual")
