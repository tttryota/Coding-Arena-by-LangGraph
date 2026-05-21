from __future__ import annotations

import datetime as _datetime_module
import dis
from types import CodeType, FunctionType, MethodType, ModuleType
from typing import TYPE_CHECKING, Any, Literal, cast
from uuid import UUID

import pytest
from structlog.testing import capture_logs

from ingestion.infrastructure.feedback_listing import (
    list_feedbacks,
    mark_feedback_as_read,
)
from ingestion.infrastructure.feedback_listing_types import (
    FeedbackListingInputError,
    FeedbackListingNotFoundError,
    FeedbackListingQuery,
    FeedbackListingResult,
    FeedbackListingStoreError,
    FeedbackListItem,
)

if TYPE_CHECKING:
    from collections.abc import Callable, MutableMapping

_ROADMAP_ID = UUID("11111111-1111-1111-1111-111111111111")
_SECOND_ROADMAP_ID = UUID("22222222-2222-2222-2222-222222222222")
_THIRD_ROADMAP_ID = UUID("33333333-3333-3333-3333-333333333333")
_FOURTH_ROADMAP_ID = UUID("44444444-4444-4444-4444-444444444444")
_FIFTH_ROADMAP_ID = UUID("55555555-5555-5555-5555-555555555555")

_FIRST_ID = UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")
_SECOND_ID = UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb")
_THIRD_ID = UUID("cccccccc-cccc-cccc-cccc-cccccccccccc")
_FOURTH_ID = UUID("dddddddd-dddd-dddd-dddd-dddddddddddd")
_FIFTH_ID = UUID("eeeeeeee-eeee-eeee-eeee-eeeeeeeeeeee")


class _RecordingReader:
    def __init__(
        self,
        *,
        items: list[FeedbackListItem] | None = None,
        error: Exception | None = None,
    ) -> None:
        self._items = list(items or [])
        self._error = error
        self.calls: list[dict[str, str | None]] = []

    def find_feedbacks(
        self,
        *,
        date_from: str | None,
        date_to: str | None,
        read_status: Literal["all", "unread", "read"],
    ) -> list[FeedbackListItem]:
        self.calls.append(
            {
                "date_from": date_from,
                "date_to": date_to,
                "read_status": read_status,
            },
        )
        if self._error is not None:
            raise self._error
        return list(self._items)


class _RecordingWriter:
    def __init__(
        self,
        *,
        current_item: FeedbackListItem | None = None,
        updated_item: FeedbackListItem | None = None,
        get_error: Exception | None = None,
        update_error: Exception | None = None,
    ) -> None:
        self._current_item = current_item
        self._updated_item = updated_item
        self._get_error = get_error
        self._update_error = update_error
        self.get_calls: list[UUID] = []
        self.update_calls: list[dict[str, object]] = []

    def get_by_id(self, feedback_id: UUID) -> FeedbackListItem | None:
        self.get_calls.append(feedback_id)
        if self._get_error is not None:
            raise self._get_error
        return self._current_item

    def update_read_status(
        self,
        feedback_id: UUID,
        *,
        is_read: bool,
        read_at: str,
    ) -> FeedbackListItem:
        self.update_calls.append(
            {
                "feedback_id": feedback_id,
                "is_read": is_read,
                "read_at": read_at,
            },
        )
        if self._update_error is not None:
            raise self._update_error
        assert self._updated_item is not None
        return self._updated_item


class _ProtocolOnlyReader:
    __slots__ = ("find_feedbacks",)

    def __init__(
        self,
        *,
        items: list[FeedbackListItem],
        calls: list[dict[str, str | None]],
    ) -> None:
        stored_items = list(items)

        def find_feedbacks(
            *,
            date_from: str | None,
            date_to: str | None,
            read_status: Literal["all", "unread", "read"],
        ) -> list[FeedbackListItem]:
            calls.append(
                {
                    "date_from": date_from,
                    "date_to": date_to,
                    "read_status": read_status,
                },
            )
            return list(stored_items)

        self.find_feedbacks = find_feedbacks

    def __getattr__(self, name: str) -> object:
        message = f"unexpected reader attribute access: {name}"
        raise AssertionError(message)


class _ProtocolOnlyWriter:
    __slots__ = ("get_by_id", "update_read_status")

    def __init__(
        self,
        *,
        current_item: FeedbackListItem | None,
        updated_item: FeedbackListItem | None,
        get_calls: list[UUID],
        update_calls: list[dict[str, object]],
    ) -> None:
        def get_by_id(feedback_id: UUID) -> FeedbackListItem | None:
            get_calls.append(feedback_id)
            return current_item

        def update_read_status(
            feedback_id: UUID,
            *,
            is_read: bool,
            read_at: str,
        ) -> FeedbackListItem:
            update_calls.append(
                {
                    "feedback_id": feedback_id,
                    "is_read": is_read,
                    "read_at": read_at,
                },
            )
            assert updated_item is not None
            return updated_item

        self.get_by_id = get_by_id
        self.update_read_status = update_read_status

    def __getattr__(self, name: str) -> object:
        message = f"unexpected writer attribute access: {name}"
        raise AssertionError(message)


class _CurrentTimeClassGuard(_datetime_module.datetime):
    @classmethod
    def now(
        cls,
        tz: _datetime_module.tzinfo | None = None,
    ) -> _CurrentTimeClassGuard:
        message = "mark_feedback_as_read must use the injected now value"
        raise AssertionError(message)

    @classmethod
    def today(cls) -> _CurrentTimeClassGuard:
        message = "mark_feedback_as_read must use the injected now value"
        raise AssertionError(message)

    @classmethod
    def utcnow(cls) -> _CurrentTimeClassGuard:
        message = "mark_feedback_as_read must use the injected now value"
        raise AssertionError(message)


class _CurrentTimeModuleGuard:
    datetime = _CurrentTimeClassGuard

    def __getattr__(self, name: str) -> object:
        return getattr(_datetime_module, name)


_CURRENT_TIME_LOOKUP_METHODS = frozenset({"now", "today", "utcnow"})
_CURRENT_TIME_HELPER_NAMES = frozenset(
    {
        "now",
        "utcnow",
        "today",
        "_now",
        "_utcnow",
        "_today",
        "current_time",
        "current_timestamp",
        "current_datetime",
    },
)


def _make_item(
    *,
    feedback_id: UUID,
    source_path: str,
    roadmap_item_id: UUID | None,
    body: str,
    is_read: bool,
    created_at: str,
    read_at: str | None,
    title: str | None = None,
) -> FeedbackListItem:
    return FeedbackListItem(
        id=feedback_id,
        source_path=source_path,
        roadmap_item_id=roadmap_item_id,
        title=title or f"{source_path} の取り込みフィードバック",
        body=body,
        is_read=is_read,
        created_at=created_at,
        read_at=read_at,
    )


def _make_result(*items: FeedbackListItem) -> FeedbackListingResult:
    return FeedbackListingResult(items=list(items), total_count=len(items))


def _find_log_events(
    log_output: list[MutableMapping[str, Any]],
    event_name: str,
) -> list[MutableMapping[str, Any]]:
    return [entry for entry in log_output if entry.get("event") == event_name]


def _assert_single_log_event_includes(
    log_output: list[MutableMapping[str, Any]],
    event_name: str,
    expected_fields: dict[str, object],
) -> MutableMapping[str, Any]:
    events = _find_log_events(log_output, event_name)
    assert len(events) == 1
    event = events[0]

    for field_name, expected_value in expected_fields.items():
        assert field_name in event
        actual_value = event[field_name]
        if field_name == "feedback_id":
            _assert_feedback_id_log_field(
                actual_value=actual_value,
                expected_value=expected_value,
            )
            continue
        if isinstance(expected_value, UUID):
            assert actual_value == expected_value
            continue
        assert actual_value == expected_value

    return event


def _assert_feedback_id_log_field(
    *,
    actual_value: object,
    expected_value: object,
) -> None:
    assert isinstance(expected_value, str)
    assert isinstance(actual_value, str)
    assert actual_value == expected_value


def _assert_no_log_event(
    log_output: list[MutableMapping[str, Any]],
    event_name: str,
) -> None:
    assert _find_log_events(log_output, event_name) == []


def _raise_on_current_time_lookup(*args: object, **kwargs: object) -> object:
    message = "mark_feedback_as_read must use the injected now value"
    raise AssertionError(message)


def _is_datetime_module_alias(value: object) -> bool:
    return isinstance(value, ModuleType) and value is _datetime_module


def _is_datetime_class_alias(value: object) -> bool:
    return value is _datetime_module.datetime


def _get_dis_instructions(value: object) -> tuple[dis.Instruction, ...] | None:
    disassemblable: (
        MethodType | FunctionType | CodeType | type[Any] | Callable[..., Any]
    )
    if isinstance(value, (MethodType, FunctionType, CodeType, type)):
        disassemblable = value
    elif callable(value):
        disassemblable = cast("Callable[..., Any]", value)
    else:
        return None

    try:
        return tuple(dis.get_instructions(disassemblable))
    except TypeError:
        return None


def _loads_current_time_method(value: object) -> bool:
    instructions = _get_dis_instructions(value)
    if instructions is None:
        return False

    return any(
        instruction.argval in _CURRENT_TIME_LOOKUP_METHODS
        and instruction.opname in {"LOAD_ATTR", "LOAD_METHOD"}
        for instruction in instructions
    )


def _is_current_time_method_alias(value: object) -> bool:
    if getattr(value, "__name__", None) not in _CURRENT_TIME_LOOKUP_METHODS:
        return False

    owner = getattr(value, "__self__", None)
    return _is_datetime_module_alias(owner) or _is_datetime_class_alias(owner)


def _loads_guarded_global_callable(
    *,
    instructions: tuple[dis.Instruction, ...],
    value: object,
    module_globals: dict[str, object],
    visited: set[int],
) -> bool:
    for instruction in instructions:
        if instruction.opname not in {"LOAD_GLOBAL", "LOAD_NAME"}:
            continue

        referenced_name = instruction.argval
        if not isinstance(referenced_name, str):
            continue

        referenced_value = module_globals.get(referenced_name)
        if referenced_value is None or referenced_value is value:
            continue
        if _is_current_time_lookup_callable(
            name=referenced_name,
            value=referenced_value,
            module_globals=module_globals,
            visited=visited,
        ):
            return True

    return False


def _is_current_time_lookup_callable(
    *,
    name: str,
    value: object,
    module_globals: dict[str, object],
    visited: set[int] | None = None,
) -> bool:
    if not callable(value):
        return False

    if visited is None:
        visited = set()
    object_id = id(value)
    if object_id in visited:
        return False
    visited.add(object_id)

    if _is_current_time_method_alias(value):
        return True
    if _loads_current_time_method(value):
        return True

    partial_target = getattr(value, "func", None)
    if callable(partial_target) and _is_current_time_lookup_callable(
        name=name,
        value=partial_target,
        module_globals=module_globals,
        visited=visited,
    ):
        return True

    instructions = _get_dis_instructions(value)
    if instructions is None:
        return name.lower() in _CURRENT_TIME_HELPER_NAMES

    if _loads_guarded_global_callable(
        instructions=instructions,
        value=value,
        module_globals=module_globals,
        visited=visited,
    ):
        return True

    return name.lower() in _CURRENT_TIME_HELPER_NAMES


def _forbid_internal_current_time_lookup(monkeypatch: pytest.MonkeyPatch) -> None:
    module_globals = mark_feedback_as_read.__globals__
    replacements: dict[str, object] = {}
    for name, value in tuple(module_globals.items()):
        if _is_datetime_module_alias(value):
            replacements[name] = _CurrentTimeModuleGuard()
            continue
        if _is_datetime_class_alias(value):
            replacements[name] = _CurrentTimeClassGuard
            continue
        if _is_current_time_lookup_callable(
            name=name,
            value=value,
            module_globals=module_globals,
        ):
            replacements[name] = _raise_on_current_time_lookup

    for name, replacement in replacements.items():
        monkeypatch.setitem(module_globals, name, replacement)


def test_tc_01_lists_all_feedbacks_sorted_and_logs_success() -> None:
    older_item = _make_item(
        feedback_id=_SECOND_ID,
        source_path="study/docker/compose.md",
        roadmap_item_id=None,
        body="Docker Compose 設定の補足メモ",
        is_read=True,
        created_at="2026-05-17T10:00:00+09:00",
        read_at="2026-05-19T12:00:00+09:00",
    )
    newer_item = _make_item(
        feedback_id=_FIRST_ID,
        source_path="study/typescript/generics.md",
        roadmap_item_id=_ROADMAP_ID,
        body="ジェネリクス制約の追記候補",
        is_read=False,
        created_at="2026-05-20T21:30:00+09:00",
        read_at=None,
    )
    reader = _RecordingReader(items=[older_item, newer_item])
    query = FeedbackListingQuery(date_from=None, date_to=None, read_status="all")

    with capture_logs() as log_output:
        result = list_feedbacks(query, reader=reader)

    assert result == _make_result(newer_item, older_item)
    assert reader.calls == [
        {
            "date_from": None,
            "date_to": None,
            "read_status": "all",
        },
    ]
    _assert_single_log_event_includes(
        log_output,
        "feedback_listing_queried",
        {
            "total_count": 2,
            "date_from": None,
            "date_to": None,
            "read_status": "all",
        },
    )


def test_tc_02_lists_unread_feedbacks_and_logs_success() -> None:
    unread_item = _make_item(
        feedback_id=_FIRST_ID,
        source_path="study/typescript/generics.md",
        roadmap_item_id=_ROADMAP_ID,
        body="ジェネリクス制約の追記候補",
        is_read=False,
        created_at="2026-05-20T21:30:00+09:00",
        read_at=None,
    )
    reader = _RecordingReader(items=[unread_item])
    query = FeedbackListingQuery(date_from=None, date_to=None, read_status="unread")

    with capture_logs() as log_output:
        result = list_feedbacks(query, reader=reader)

    assert result == _make_result(unread_item)
    assert reader.calls == [
        {
            "date_from": None,
            "date_to": None,
            "read_status": "unread",
        },
    ]
    _assert_single_log_event_includes(
        log_output,
        "feedback_listing_queried",
        {
            "total_count": 1,
            "date_from": None,
            "date_to": None,
            "read_status": "unread",
        },
    )


def test_tc_03_marks_unread_feedback_as_read_and_logs_success(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    feedback_id = _FIRST_ID
    now = "2026-05-21T00:00:00Z"
    unread_item = _make_item(
        feedback_id=feedback_id,
        source_path="study/typescript/generics.md",
        roadmap_item_id=_ROADMAP_ID,
        body="ジェネリクス制約の追記候補",
        is_read=False,
        created_at="2026-05-20T21:30:00+09:00",
        read_at=None,
    )
    read_item = _make_item(
        feedback_id=feedback_id,
        source_path="study/typescript/generics.md",
        roadmap_item_id=_ROADMAP_ID,
        body="ジェネリクス制約の追記候補",
        is_read=True,
        created_at="2026-05-20T21:30:00+09:00",
        read_at=now,
    )
    writer = _RecordingWriter(current_item=unread_item, updated_item=read_item)
    _forbid_internal_current_time_lookup(monkeypatch)

    with capture_logs() as log_output:
        result = mark_feedback_as_read(feedback_id, writer=writer, now=now)

    assert result == read_item
    assert result.read_at == now
    assert writer.get_calls == [feedback_id]
    assert writer.update_calls == [
        {
            "feedback_id": feedback_id,
            "is_read": True,
            "read_at": now,
        },
    ]
    assert writer.update_calls[0]["read_at"] == result.read_at
    _assert_single_log_event_includes(
        log_output,
        "feedback_listing_marked_read",
        {"feedback_id": str(feedback_id)},
    )


def test_tc_10_delegates_read_status_read_to_reader() -> None:
    read_item = _make_item(
        feedback_id=_SECOND_ID,
        source_path="study/docker/compose.md",
        roadmap_item_id=None,
        body="Docker Compose 設定の補足メモ",
        is_read=True,
        created_at="2026-05-17T10:00:00+09:00",
        read_at="2026-05-19T12:00:00+09:00",
    )
    reader = _RecordingReader(items=[read_item])
    query = FeedbackListingQuery(date_from=None, date_to=None, read_status="read")

    result = list_feedbacks(query, reader=reader)

    assert result == _make_result(read_item)
    assert reader.calls == [
        {
            "date_from": None,
            "date_to": None,
            "read_status": "read",
        },
    ]


def test_tc_11_validates_date_range_by_instant_and_sorts_descending() -> None:
    lexicographically_later_item = _make_item(
        feedback_id=_SECOND_ID,
        source_path="study/python/datetime.md",
        roadmap_item_id=_SECOND_ROADMAP_ID,
        body="UTC 境界の確認",
        is_read=False,
        created_at="2026-05-20T14:30:00+09:00",
        read_at=None,
    )
    instant_later_item = _make_item(
        feedback_id=_FIRST_ID,
        source_path="study/typescript/generics.md",
        roadmap_item_id=_ROADMAP_ID,
        body="ジェネリクス制約の追記候補",
        is_read=False,
        created_at="2026-05-20T10:00:00Z",
        read_at=None,
    )
    reader = _RecordingReader(items=[lexicographically_later_item, instant_later_item])
    query = FeedbackListingQuery(
        date_from="2026-05-19T15:00:00Z",
        date_to="2026-05-20T14:59:59.500000Z",
        read_status="all",
    )

    result = list_feedbacks(query, reader=reader)

    assert result == _make_result(instant_later_item, lexicographically_later_item)
    assert [item.id for item in result.items] == [
        instant_later_item.id,
        lexicographically_later_item.id,
    ]
    assert reader.calls == [
        {
            "date_from": "2026-05-19T15:00:00Z",
            "date_to": "2026-05-20T14:59:59.500000Z",
            "read_status": "all",
        },
    ]


def test_tc_12_tie_breaks_same_instant_by_id() -> None:
    later_by_id = _make_item(
        feedback_id=_SECOND_ID,
        source_path="study/docker/compose.md",
        roadmap_item_id=None,
        body="Docker Compose 設定の補足メモ",
        is_read=True,
        created_at="2026-05-20T03:00:00Z",
        read_at="2026-05-20T06:00:00Z",
    )
    earlier_by_id = _make_item(
        feedback_id=_FIRST_ID,
        source_path="study/typescript/generics.md",
        roadmap_item_id=_ROADMAP_ID,
        body="ジェネリクス制約の追記候補",
        is_read=False,
        created_at="2026-05-20T12:00:00+09:00",
        read_at=None,
    )
    reader = _RecordingReader(items=[later_by_id, earlier_by_id])
    query = FeedbackListingQuery(date_from=None, date_to=None, read_status="all")

    result = list_feedbacks(query, reader=reader)

    assert result == _make_result(earlier_by_id, later_by_id)


def test_tc_13_delegates_one_sided_boundaries_and_skips_post_filtering() -> None:
    case_a_items = [
        _make_item(
            feedback_id=_THIRD_ID,
            source_path="study/sql/index.md",
            roadmap_item_id=_THIRD_ROADMAP_ID,
            body="索引設計の見直しメモ",
            is_read=False,
            created_at="2026-05-20T18:00:00+09:00",
            read_at=None,
        ),
        _make_item(
            feedback_id=_FIRST_ID,
            source_path="study/api/errors.md",
            roadmap_item_id=None,
            body="エラー分類の追記候補",
            is_read=True,
            created_at="2026-05-20T00:00:00Z",
            read_at="2026-05-20T12:00:00+09:00",
        ),
        _make_item(
            feedback_id=_SECOND_ID,
            source_path="study/python/timezone.md",
            roadmap_item_id=_SECOND_ROADMAP_ID,
            body="UTC 変換の注意点",
            is_read=False,
            created_at="2026-05-20T08:30:00-04:00",
            read_at=None,
        ),
    ]
    case_a_reader = _RecordingReader(items=case_a_items)
    case_a_query = FeedbackListingQuery(
        date_from="2026-05-20T00:00:00Z",
        date_to=None,
        read_status="all",
    )

    case_a_result = list_feedbacks(case_a_query, reader=case_a_reader)

    assert case_a_result == _make_result(
        case_a_items[2],
        case_a_items[0],
        case_a_items[1],
    )
    assert case_a_reader.calls == [
        {
            "date_from": "2026-05-20T00:00:00Z",
            "date_to": None,
            "read_status": "all",
        },
    ]

    case_b_items = [
        _make_item(
            feedback_id=_FIFTH_ID,
            source_path="study/frontend/state.md",
            roadmap_item_id=_FIFTH_ROADMAP_ID,
            body="状態管理の比較メモ",
            is_read=False,
            created_at="2026-05-20T21:00:00+09:00",
            read_at=None,
        ),
        _make_item(
            feedback_id=_FOURTH_ID,
            source_path="study/backend/cache.md",
            roadmap_item_id=_FOURTH_ROADMAP_ID,
            body="キャッシュ失効条件の確認",
            is_read=True,
            created_at="2026-05-19T23:00:00Z",
            read_at="2026-05-20T08:00:00+09:00",
        ),
    ]
    case_b_reader = _RecordingReader(items=case_b_items)
    case_b_query = FeedbackListingQuery(
        date_from=None,
        date_to="2026-05-20T23:59:59+09:00",
        read_status="read",
    )

    case_b_result = list_feedbacks(case_b_query, reader=case_b_reader)

    assert case_b_result == _make_result(case_b_items[0], case_b_items[1])
    assert case_b_reader.calls == [
        {
            "date_from": None,
            "date_to": "2026-05-20T23:59:59+09:00",
            "read_status": "read",
        },
    ]
    assert case_b_result.items[0].is_read is False


def test_tc_14_mark_feedback_as_read_is_idempotent_for_already_read_item() -> None:
    feedback_id = _SECOND_ID
    existing_item = _make_item(
        feedback_id=feedback_id,
        source_path="study/docker/compose.md",
        roadmap_item_id=None,
        body="Docker Compose 設定の補足メモ",
        is_read=True,
        created_at="2026-05-17T10:00:00+09:00",
        read_at="2026-05-19T12:00:00+09:00",
    )
    writer = _RecordingWriter(current_item=existing_item)

    with capture_logs() as log_output:
        result = mark_feedback_as_read(
            feedback_id,
            writer=writer,
            now="2026-05-21T10:00:00+09:00",
        )

    assert result == existing_item
    assert writer.get_calls == [feedback_id]
    assert writer.update_calls == []
    assert result.read_at == "2026-05-19T12:00:00+09:00"
    _assert_single_log_event_includes(
        log_output,
        "feedback_listing_marked_read",
        {"feedback_id": str(feedback_id)},
    )


@pytest.mark.parametrize(
    ("date_from", "date_to"),
    [
        ("2026-05-20T00:00:00.1Z", None),
        ("2026-05-20T00:00:00.12+09:00", None),
        (None, "2026-05-20T23:59:59.123Z"),
        (None, "2026-05-20T23:59:59.1234-04:00"),
    ],
)
def test_tc_15_accepts_fractional_seconds_for_listing_filters(
    date_from: str | None,
    date_to: str | None,
) -> None:
    reader = _RecordingReader(items=[])
    query = FeedbackListingQuery(
        date_from=date_from,
        date_to=date_to,
        read_status="all",
    )

    result = list_feedbacks(query, reader=reader)

    assert result == FeedbackListingResult(items=[], total_count=0)
    assert reader.calls == [
        {
            "date_from": date_from,
            "date_to": date_to,
            "read_status": "all",
        },
    ]


def test_tc_15_accepts_fractional_seconds_for_mark_feedback_as_read() -> None:
    feedback_id = _FIRST_ID
    now = "2026-05-21T09:00:00.12345+09:00"
    unread_item = _make_item(
        feedback_id=feedback_id,
        source_path="study/typescript/generics.md",
        roadmap_item_id=_ROADMAP_ID,
        body="ジェネリクス制約の追記候補",
        is_read=False,
        created_at="2026-05-20T21:30:00+09:00",
        read_at=None,
    )
    read_item = _make_item(
        feedback_id=feedback_id,
        source_path="study/typescript/generics.md",
        roadmap_item_id=_ROADMAP_ID,
        body="ジェネリクス制約の追記候補",
        is_read=True,
        created_at="2026-05-20T21:30:00+09:00",
        read_at=now,
    )
    writer = _RecordingWriter(current_item=unread_item, updated_item=read_item)

    result = mark_feedback_as_read(feedback_id, writer=writer, now=now)

    assert result == read_item
    assert writer.update_calls == [
        {
            "feedback_id": feedback_id,
            "is_read": True,
            "read_at": now,
        },
    ]


def test_tc_20_returns_empty_result_and_logs_success() -> None:
    reader = _RecordingReader(items=[])
    query = FeedbackListingQuery(
        date_from="2026-05-22T00:00:00+09:00",
        date_to=None,
        read_status="all",
    )

    with capture_logs() as log_output:
        result = list_feedbacks(query, reader=reader)

    assert result == FeedbackListingResult(items=[], total_count=0)
    assert reader.calls == [
        {
            "date_from": "2026-05-22T00:00:00+09:00",
            "date_to": None,
            "read_status": "all",
        },
    ]
    _assert_single_log_event_includes(
        log_output,
        "feedback_listing_queried",
        {
            "total_count": 0,
            "date_from": "2026-05-22T00:00:00+09:00",
            "date_to": None,
            "read_status": "all",
        },
    )


@pytest.mark.parametrize(
    ("query", "expected_call_count"),
    [
        (
            FeedbackListingQuery(
                date_from="2026-05-20 00:00:00+09:00",
                date_to=None,
                read_status="all",
            ),
            0,
        ),
        (
            FeedbackListingQuery(
                date_from=None,
                date_to="2026-05-20T00:00:00",
                read_status="all",
            ),
            0,
        ),
        (
            FeedbackListingQuery(
                date_from=None,
                date_to=None,
                read_status=cast("Literal['all', 'unread', 'read']", "archived"),
            ),
            0,
        ),
        (
            FeedbackListingQuery(
                date_from="2026-05-20T00:30:00-01:00",
                date_to="2026-05-20T01:00:00Z",
                read_status="all",
            ),
            0,
        ),
    ],
)
def test_tc_21_rejects_invalid_listing_input_before_reader_call(
    query: FeedbackListingQuery,
    expected_call_count: int,
) -> None:
    reader = _RecordingReader(items=[])

    with capture_logs() as log_output, pytest.raises(FeedbackListingInputError):
        list_feedbacks(query, reader=reader)

    assert len(reader.calls) == expected_call_count
    _assert_no_log_event(log_output, "feedback_listing_queried")
    _assert_no_log_event(log_output, "feedback_listing_store_failed")


@pytest.mark.parametrize(
    "now",
    [
        "2026-05-21 09:00:00+09:00",
        "2026-05-21T09:00:00",
    ],
)
def test_tc_22_rejects_invalid_now_before_writer_call(now: str) -> None:
    writer = _RecordingWriter(
        current_item=_make_item(
            feedback_id=_FIRST_ID,
            source_path="study/typescript/generics.md",
            roadmap_item_id=_ROADMAP_ID,
            body="ジェネリクス制約の追記候補",
            is_read=False,
            created_at="2026-05-20T21:30:00+09:00",
            read_at=None,
        ),
    )

    with capture_logs() as log_output, pytest.raises(FeedbackListingInputError):
        mark_feedback_as_read(_FIRST_ID, writer=writer, now=now)

    assert writer.get_calls == []
    assert writer.update_calls == []
    _assert_no_log_event(log_output, "feedback_listing_marked_read")
    _assert_no_log_event(log_output, "feedback_listing_not_found")
    _assert_no_log_event(log_output, "feedback_listing_store_failed")


def test_tc_23_raises_store_error_for_invalid_reader_created_at_and_logs_failure() -> (
    None
):
    invalid_item = _make_item(
        feedback_id=_FIRST_ID,
        source_path="study/typescript/generics.md",
        roadmap_item_id=_ROADMAP_ID,
        body="ジェネリクス制約の追記候補",
        is_read=False,
        created_at="2026-05-20 12:34:56+09:00",
        read_at=None,
    )
    reader = _RecordingReader(items=[invalid_item])
    query = FeedbackListingQuery(date_from=None, date_to=None, read_status="all")

    with capture_logs() as log_output, pytest.raises(FeedbackListingStoreError):
        list_feedbacks(query, reader=reader)

    assert reader.calls == [
        {
            "date_from": None,
            "date_to": None,
            "read_status": "all",
        },
    ]
    event = _assert_single_log_event_includes(
        log_output,
        "feedback_listing_store_failed",
        {
            "date_from": None,
            "date_to": None,
            "read_status": "all",
        },
    )
    assert "error_type" in event
    _assert_no_log_event(log_output, "feedback_listing_queried")


def test_tc_24_raises_store_error_for_invalid_writer_get_by_id_created_at() -> None:
    writer = _RecordingWriter(
        current_item=_make_item(
            feedback_id=_FIRST_ID,
            source_path="study/typescript/generics.md",
            roadmap_item_id=_ROADMAP_ID,
            body="ジェネリクス制約の追記候補",
            is_read=False,
            created_at="2026-05-20 21:30:00+09:00",
            read_at=None,
        ),
    )

    with capture_logs() as log_output, pytest.raises(FeedbackListingStoreError):
        mark_feedback_as_read(
            _FIRST_ID,
            writer=writer,
            now="2026-05-21T00:00:00Z",
        )

    assert writer.get_calls == [_FIRST_ID]
    assert writer.update_calls == []
    event = _assert_single_log_event_includes(
        log_output,
        "feedback_listing_store_failed",
        {"feedback_id": str(_FIRST_ID)},
    )
    assert "error_type" in event
    _assert_no_log_event(log_output, "feedback_listing_marked_read")
    _assert_no_log_event(log_output, "feedback_listing_not_found")


def test_tc_25_raises_store_error_for_invalid_writer_update_created_at() -> None:
    unread_item = _make_item(
        feedback_id=_FIRST_ID,
        source_path="study/typescript/generics.md",
        roadmap_item_id=_ROADMAP_ID,
        body="ジェネリクス制約の追記候補",
        is_read=False,
        created_at="2026-05-20T21:30:00+09:00",
        read_at=None,
    )
    invalid_updated_item = _make_item(
        feedback_id=_FIRST_ID,
        source_path="study/typescript/generics.md",
        roadmap_item_id=_ROADMAP_ID,
        body="ジェネリクス制約の追記候補",
        is_read=True,
        created_at="2026-05-20 21:30:00+09:00",
        read_at="2026-05-21T00:00:00Z",
    )
    writer = _RecordingWriter(
        current_item=unread_item,
        updated_item=invalid_updated_item,
    )

    with capture_logs() as log_output, pytest.raises(FeedbackListingStoreError):
        mark_feedback_as_read(
            _FIRST_ID,
            writer=writer,
            now="2026-05-21T00:00:00Z",
        )

    assert writer.get_calls == [_FIRST_ID]
    assert writer.update_calls == [
        {
            "feedback_id": _FIRST_ID,
            "is_read": True,
            "read_at": "2026-05-21T00:00:00Z",
        },
    ]
    event = _assert_single_log_event_includes(
        log_output,
        "feedback_listing_store_failed",
        {"feedback_id": str(_FIRST_ID)},
    )
    assert "error_type" in event
    _assert_no_log_event(log_output, "feedback_listing_marked_read")


def test_tc_30_works_with_protocol_only_stubs() -> None:
    listed_item = _make_item(
        feedback_id=_FIRST_ID,
        source_path="study/typescript/generics.md",
        roadmap_item_id=_ROADMAP_ID,
        body="ジェネリクス制約の追記候補",
        is_read=False,
        created_at="2026-05-20T21:30:00+09:00",
        read_at=None,
    )
    reader_calls: list[dict[str, str | None]] = []
    reader = _ProtocolOnlyReader(items=[listed_item], calls=reader_calls)

    list_result = list_feedbacks(
        FeedbackListingQuery(date_from=None, date_to=None, read_status="all"),
        reader=reader,
    )

    assert list_result == _make_result(listed_item)
    assert reader_calls == [
        {
            "date_from": None,
            "date_to": None,
            "read_status": "all",
        },
    ]

    unread_item = _make_item(
        feedback_id=_SECOND_ID,
        source_path="study/docker/compose.md",
        roadmap_item_id=None,
        body="Docker Compose 設定の補足メモ",
        is_read=False,
        created_at="2026-05-17T10:00:00+09:00",
        read_at=None,
    )
    updated_item = _make_item(
        feedback_id=_SECOND_ID,
        source_path="study/docker/compose.md",
        roadmap_item_id=None,
        body="Docker Compose 設定の補足メモ",
        is_read=True,
        created_at="2026-05-17T10:00:00+09:00",
        read_at="2026-05-21T00:00:00Z",
    )
    writer_get_calls: list[UUID] = []
    writer_update_calls: list[dict[str, object]] = []
    writer = _ProtocolOnlyWriter(
        current_item=unread_item,
        updated_item=updated_item,
        get_calls=writer_get_calls,
        update_calls=writer_update_calls,
    )

    mark_result = mark_feedback_as_read(
        _SECOND_ID,
        writer=writer,
        now="2026-05-21T00:00:00Z",
    )

    assert mark_result == updated_item
    assert writer_get_calls == [_SECOND_ID]
    assert writer_update_calls == [
        {
            "feedback_id": _SECOND_ID,
            "is_read": True,
            "read_at": "2026-05-21T00:00:00Z",
        },
    ]


def test_tc_31_raises_not_found_and_logs_failure_when_feedback_is_missing() -> None:
    writer = _RecordingWriter(current_item=None)

    with capture_logs() as log_output, pytest.raises(FeedbackListingNotFoundError):
        mark_feedback_as_read(
            _THIRD_ID,
            writer=writer,
            now="2026-05-21T00:00:00Z",
        )

    assert writer.get_calls == [_THIRD_ID]
    assert writer.update_calls == []
    _assert_single_log_event_includes(
        log_output,
        "feedback_listing_not_found",
        {"feedback_id": str(_THIRD_ID)},
    )
    _assert_no_log_event(log_output, "feedback_listing_marked_read")
    _assert_no_log_event(log_output, "feedback_listing_store_failed")


def test_tc_32_wraps_reader_failures_and_logs_failure() -> None:
    reader = _RecordingReader(error=TimeoutError("reader timeout"))
    query = FeedbackListingQuery(date_from=None, date_to=None, read_status="all")

    with capture_logs() as log_output, pytest.raises(FeedbackListingStoreError):
        list_feedbacks(query, reader=reader)

    event = _assert_single_log_event_includes(
        log_output,
        "feedback_listing_store_failed",
        {
            "date_from": None,
            "date_to": None,
            "read_status": "all",
            "error_type": "TimeoutError",
        },
    )
    assert event["error_type"] == "TimeoutError"
    _assert_no_log_event(log_output, "feedback_listing_queried")


@pytest.mark.parametrize(
    ("writer", "expected_get_calls", "expected_update_calls"),
    [
        (
            _RecordingWriter(get_error=ConnectionError("writer unavailable")),
            [_FIRST_ID],
            [],
        ),
        (
            _RecordingWriter(
                current_item=_make_item(
                    feedback_id=_FIRST_ID,
                    source_path="study/typescript/generics.md",
                    roadmap_item_id=_ROADMAP_ID,
                    body="ジェネリクス制約の追記候補",
                    is_read=False,
                    created_at="2026-05-20T21:30:00+09:00",
                    read_at=None,
                ),
                update_error=RuntimeError("update failed"),
            ),
            [_FIRST_ID],
            [
                {
                    "feedback_id": _FIRST_ID,
                    "is_read": True,
                    "read_at": "2026-05-21T09:00:00.123456+09:00",
                },
            ],
        ),
    ],
)
def test_tc_33_wraps_writer_failures_and_logs_failure(
    writer: _RecordingWriter,
    expected_get_calls: list[UUID],
    expected_update_calls: list[dict[str, object]],
) -> None:
    with capture_logs() as log_output, pytest.raises(FeedbackListingStoreError):
        mark_feedback_as_read(
            _FIRST_ID,
            writer=writer,
            now="2026-05-21T09:00:00.123456+09:00",
        )

    assert writer.get_calls == expected_get_calls
    assert writer.update_calls == expected_update_calls
    event = _assert_single_log_event_includes(
        log_output,
        "feedback_listing_store_failed",
        {"feedback_id": str(_FIRST_ID)},
    )
    assert "error_type" in event
    _assert_no_log_event(log_output, "feedback_listing_marked_read")
