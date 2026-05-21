from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import MutableMapping


def find_log_events(
    log_output: list[MutableMapping[str, Any]],
    event_name: str,
    *,
    log_level: str | None = None,
) -> list[MutableMapping[str, Any]]:
    return [
        entry
        for entry in log_output
        if entry.get("event") == event_name
        and (log_level is None or entry.get("log_level") == log_level)
    ]


def assert_single_log_event(
    log_output: list[MutableMapping[str, Any]],
    event_name: str,
    expected_fields: dict[str, object],
    *,
    log_level: str | None = None,
    str_coerce_fields: frozenset[str] = frozenset(),
) -> MutableMapping[str, Any]:
    """ちょうど 1 件のログイベントが存在し、expected_fields を含むことを検証。

    str_coerce_fields に含まれるフィールドだけ str() で正規化して比較。
    それ以外は厳密一致。
    """
    events = find_log_events(log_output, event_name, log_level=log_level)
    assert len(events) == 1
    event = events[0]
    for field_name, expected_value in expected_fields.items():
        assert field_name in event
        actual = event[field_name]
        if field_name in str_coerce_fields:
            assert isinstance(expected_value, str)
            assert actual is not None, f"{field_name}: expected non-None"
            assert str(actual) == expected_value
        else:
            assert actual == expected_value
    return event


def assert_no_log_event(
    log_output: list[MutableMapping[str, Any]],
    event_name: str,
    *,
    log_level: str | None = None,
) -> None:
    assert find_log_events(log_output, event_name, log_level=log_level) == []
