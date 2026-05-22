from __future__ import annotations

import unicodedata
from dataclasses import fields, is_dataclass
from typing import Literal

import pytest

from roadmap.domain.topic_listing_types import (
    NoteTopicReader,
    NoteTopicRecord,
    PresetTopicRecord,
    StoredTopicRecord,
    TopicCandidate,
    TopicListingEmptyTopicNameError,
    TopicNoteCountReader,
    TopicNoteCountRecord,
    TopicPresetReader,
    TopicStore,
)
from roadmap.infrastructure.topic_listing import (
    list_topic_candidates,
    register_manual_topic,
)

# ---------------------------------------------------------------------------
# Test doubles
# ---------------------------------------------------------------------------


class _RecordingPresetReader:
    def __init__(self, *, records: list[PresetTopicRecord]) -> None:
        self._records = list(records)
        self.calls = 0

    def list_preset_topics(self) -> list[PresetTopicRecord]:
        self.calls += 1
        return list(self._records)

    def __getattr__(self, name: str) -> object:
        message = f"unexpected preset reader attribute: {name}"
        raise AssertionError(message)


class _RecordingNoteTopicReader:
    def __init__(self, *, records: list[NoteTopicRecord]) -> None:
        self._records = list(records)
        self.calls = 0

    def list_note_topics(self) -> list[NoteTopicRecord]:
        self.calls += 1
        return list(self._records)

    def __getattr__(self, name: str) -> object:
        message = f"unexpected note topic reader attribute: {name}"
        raise AssertionError(message)


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

    def __getattr__(self, name: str) -> object:
        message = f"unexpected topic store attribute: {name}"
        raise AssertionError(message)


class _RecordingNoteCountReader:
    def __init__(self, *, counts: list[TopicNoteCountRecord]) -> None:
        self._counts = list(counts)
        self.calls: list[list[str]] = []

    def list_note_counts(
        self,
        canonical_names: list[str],
    ) -> list[TopicNoteCountRecord]:
        self.calls.append(list(canonical_names))
        return list(self._counts)

    def __getattr__(self, name: str) -> object:
        message = f"unexpected note count reader attribute: {name}"
        raise AssertionError(message)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_preset = PresetTopicRecord
_note = NoteTopicRecord
_count = TopicNoteCountRecord


def _stored(
    name: str,
    canonical_name: str,
    source: Literal["preset", "note", "manual"] = "manual",
) -> StoredTopicRecord:
    return StoredTopicRecord(name=name, canonical_name=canonical_name, source=source)


def _candidate(
    name: str,
    source: Literal["preset", "note", "manual"],
    note_count: int,
) -> TopicCandidate:
    return TopicCandidate(name=name, source=source, note_count=note_count)


# ---------------------------------------------------------------------------
# TC-01: 静的契約
# ---------------------------------------------------------------------------


def test_tc_01_public_contracts_match_spec() -> None:
    for cls in (TopicCandidate, PresetTopicRecord, NoteTopicRecord, StoredTopicRecord, TopicNoteCountRecord):
        assert is_dataclass(cls)
        assert cls.__dataclass_params__.frozen is True  # type: ignore[attr-defined]

    assert tuple(f.name for f in fields(TopicCandidate)) == ("name", "source", "note_count")
    assert tuple(f.name for f in fields(PresetTopicRecord)) == ("name", "canonical_name")
    assert tuple(f.name for f in fields(StoredTopicRecord)) == ("name", "canonical_name", "source")
    assert tuple(f.name for f in fields(TopicNoteCountRecord)) == ("canonical_name", "note_count")

    for cls in (TopicPresetReader, NoteTopicReader, TopicStore, TopicNoteCountReader):
        assert getattr(cls, "_is_protocol", False) is True

    assert issubclass(TopicListingEmptyTopicNameError, Exception)


# ---------------------------------------------------------------------------
# list_topic_candidates
# ---------------------------------------------------------------------------


def test_tc_02_returns_presets_with_missing_counts_defaulting_to_zero() -> None:
    result = list_topic_candidates(
        preset_reader=_RecordingPresetReader(
            records=[_preset("Docker", "docker"), _preset("TypeScript", "typescript")],
        ),
        note_topic_reader=_RecordingNoteTopicReader(records=[]),
        topic_store=_RecordingTopicStore(manual_records=[]),
        note_count_reader=_RecordingNoteCountReader(counts=[_count("typescript", 2)]),
    )
    assert result == [
        _candidate("TypeScript", "preset", 2),
        _candidate("Docker", "preset", 0),
    ]


def test_tc_10_merges_three_sources_with_priority_counts_and_sorting() -> None:
    note_count_reader = _RecordingNoteCountReader(
        counts=[_count("typescript", 12), _count("docker", 3), _count("langgraph", 5)],
    )
    result = list_topic_candidates(
        preset_reader=_RecordingPresetReader(
            records=[
                _preset("TypeScript", "typescript"),
                _preset("Docker", "docker"),
                _preset("React", "react"),
            ],
        ),
        note_topic_reader=_RecordingNoteTopicReader(
            records=[
                _note("docker", "docker"),
                _note("LangGraph", "langgraph"),
                _note("react", "react"),
            ],
        ),
        topic_store=_RecordingTopicStore(
            manual_records=[
                _stored("Terraform", "terraform"),
                _stored("React Manual", "react"),
            ],
        ),
        note_count_reader=note_count_reader,
    )
    assert result == [
        _candidate("TypeScript", "preset", 12),
        _candidate("LangGraph", "note", 5),
        _candidate("Docker", "preset", 3),
        _candidate("React", "preset", 0),
        _candidate("Terraform", "manual", 0),
    ]
    assert note_count_reader.calls == [
        ["docker", "langgraph", "react", "terraform", "typescript"],
    ]


def test_tc_11_prefers_manual_over_note_when_preset_absent() -> None:
    result = list_topic_candidates(
        preset_reader=_RecordingPresetReader(records=[]),
        note_topic_reader=_RecordingNoteTopicReader(
            records=[_note("terraform", "terraform")],
        ),
        topic_store=_RecordingTopicStore(
            manual_records=[_stored("Terraform", "terraform")],
        ),
        note_count_reader=_RecordingNoteCountReader(counts=[_count("terraform", 7)]),
    )
    assert result == [_candidate("Terraform", "manual", 7)]


def test_tc_20_returns_empty_when_all_sources_empty() -> None:
    ncr = _RecordingNoteCountReader(counts=[])
    result = list_topic_candidates(
        preset_reader=_RecordingPresetReader(records=[]),
        note_topic_reader=_RecordingNoteTopicReader(records=[]),
        topic_store=_RecordingTopicStore(manual_records=[]),
        note_count_reader=ncr,
    )
    assert result == []
    assert ncr.calls == [[]]


def test_tc_30_calls_listing_dependencies_once_each() -> None:
    pr = _RecordingPresetReader(records=[_preset("Docker", "docker")])
    ntr = _RecordingNoteTopicReader(records=[_note("terraform", "terraform")])
    ts = _RecordingTopicStore(manual_records=[_stored("GraphRAG", "graphrag")])
    ncr = _RecordingNoteCountReader(counts=[])

    list_topic_candidates(
        preset_reader=pr,
        note_topic_reader=ntr,
        topic_store=ts,
        note_count_reader=ncr,
    )

    assert pr.calls == 1
    assert ntr.calls == 1
    assert ts.list_manual_topics_calls == 1
    assert ncr.calls == [["docker", "graphrag", "terraform"]]
    assert ts.find_calls == []
    assert ts.create_calls == []


# ---------------------------------------------------------------------------
# register_manual_topic
# ---------------------------------------------------------------------------


def test_tc_03_registers_new_topic_and_returns_candidate() -> None:
    ts = _RecordingTopicStore(
        find_result=None,
        create_result=_stored("GraphRAG", "graphrag"),
    )
    ncr = _RecordingNoteCountReader(counts=[])

    result = register_manual_topic(" GraphRAG ", topic_store=ts, note_count_reader=ncr)

    assert ts.find_calls == ["graphrag"]
    assert ts.create_calls == [("GraphRAG", "graphrag")]
    assert ncr.calls == [["graphrag"]]
    assert result == _candidate("GraphRAG", "manual", 0)


def test_tc_12_detects_duplicate_via_nfkc_casefold() -> None:
    ts = _RecordingTopicStore(
        find_result=_stored("Terraform", "terraform", source="preset"),
    )
    ncr = _RecordingNoteCountReader(counts=[_count("terraform", 2)])

    result = register_manual_topic(
        "\uff54\uff45\uff52\uff52\uff41\uff46\uff4f\uff52\uff4d",
        topic_store=ts,
        note_count_reader=ncr,
    )

    assert ts.find_calls == ["terraform"]
    assert ts.create_calls == []
    assert ncr.calls == [["terraform"]]
    assert result == _candidate("Terraform", "preset", 2)


def test_tc_13_limits_duplicate_detection_to_exact_canonical_match() -> None:
    ts = _RecordingTopicStore(find_result=None)
    ncr = _RecordingNoteCountReader(counts=[])

    result = register_manual_topic("Type", topic_store=ts, note_count_reader=ncr)

    assert ts.find_calls == ["type"]
    assert ts.create_calls == [("Type", "type")]
    assert result == _candidate("Type", "manual", 0)


def test_tc_21_raises_for_blank_input_without_calling_dependencies() -> None:
    ts = _RecordingTopicStore()
    ncr = _RecordingNoteCountReader(counts=[])

    with pytest.raises(TopicListingEmptyTopicNameError):
        register_manual_topic(" \t\n ", topic_store=ts, note_count_reader=ncr)

    assert ts.find_calls == []
    assert ts.create_calls == []
    assert ncr.calls == []


def test_tc_22_preserves_internal_whitespace_applies_nfkc_casefold_to_canonical() -> (
    None
):
    normalized = "AI\u3000Agent"
    canonical = unicodedata.normalize("NFKC", normalized).casefold()
    ts = _RecordingTopicStore(
        find_result=None,
        create_result=_stored(normalized, canonical),
    )
    ncr = _RecordingNoteCountReader(counts=[])

    result = register_manual_topic(
        "  AI\u3000Agent  ",
        topic_store=ts,
        note_count_reader=ncr,
    )

    assert canonical == "ai agent"
    assert ts.find_calls == [canonical]
    assert ts.create_calls == [(normalized, canonical)]
    assert ncr.calls == [[canonical]]
    assert result == _candidate(normalized, "manual", 0)


def test_tc_31_uses_find_only_for_existing_duplicate_skips_create() -> None:
    ts = _RecordingTopicStore(
        find_result=_stored("Terraform", "terraform", source="manual"),
    )
    ncr = _RecordingNoteCountReader(counts=[])

    result = register_manual_topic(" Terraform ", topic_store=ts, note_count_reader=ncr)

    assert ts.find_calls == ["terraform"]
    assert ts.create_calls == []
    assert ncr.calls == [["terraform"]]
    assert result == _candidate("Terraform", "manual", 0)


def test_tc_32_creates_new_topic_once_and_reads_note_count() -> None:
    ts = _RecordingTopicStore(
        find_result=None,
        create_result=_stored("GraphRAG", "graphrag"),
    )
    ncr = _RecordingNoteCountReader(counts=[_count("graphrag", 4)])

    result = register_manual_topic("GraphRAG", topic_store=ts, note_count_reader=ncr)

    assert ts.find_calls == ["graphrag"]
    assert ts.create_calls == [("GraphRAG", "graphrag")]
    assert ncr.calls == [["graphrag"]]
    assert result == _candidate("GraphRAG", "manual", 4)
