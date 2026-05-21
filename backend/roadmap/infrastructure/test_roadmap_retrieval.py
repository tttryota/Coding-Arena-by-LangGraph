from __future__ import annotations

from typing import Literal
from uuid import UUID

import pytest
from structlog.testing import capture_logs

from roadmap.infrastructure.roadmap_retrieval import get_roadmap, list_roadmaps
from roadmap.infrastructure.roadmap_retrieval_types import (
    RoadmapItemRecord,
    RoadmapListItem,
    RoadmapListResult,
    RoadmapRecord,
    RoadmapRetrievalNotFoundError,
    RoadmapRetrievalStoreError,
    RoadmapTree,
    RoadmapTreeNode,
)
from shared.log_assertions import (
    assert_single_log_event as _assert_single_log_event,
)

_REQUEST_ROADMAP_ID = UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")
_RETURNED_ROADMAP_ID = UUID("abababab-abab-abab-abab-abababababab")
_EMPTY_ROADMAP_ID = UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb")
_FLOOR_ROADMAP_ID = UUID("cccccccc-cccc-cccc-cccc-cccccccccccc")
_NOT_FOUND_ROADMAP_ID = UUID("dddddddd-dddd-dddd-dddd-dddddddddddd")
_STORE_ERROR_ROADMAP_ID = UUID("eeeeeeee-eeee-eeee-eeee-eeeeeeeeeeee")
_MIDDLE_EMPTY_ROADMAP_ID = UUID("21212121-2121-2121-2121-212121212121")
_MAJOR_EMPTY_ROADMAP_ID = UUID("22222222-2222-2222-2222-222222222222")
_ALL_ZERO_ROADMAP_ID = UUID("23232323-2323-2323-2323-232323232323")
_ORDER_GAP_ROADMAP_ID = UUID("24242424-2424-2424-2424-242424242424")


class _RecordingReader:
    def __init__(
        self,
        *,
        roadmap: RoadmapRecord | None = None,
        roadmaps: list[RoadmapRecord] | None = None,
        find_roadmap_error: Exception | None = None,
        find_all_roadmaps_error: Exception | None = None,
    ) -> None:
        self._roadmap = roadmap
        self._roadmaps = list(roadmaps or [])
        self._find_roadmap_error = find_roadmap_error
        self._find_all_roadmaps_error = find_all_roadmaps_error
        self.find_roadmap_calls: list[UUID] = []
        self.find_all_roadmaps_calls = 0

    def find_roadmap(self, roadmap_id: UUID) -> RoadmapRecord | None:
        self.find_roadmap_calls.append(roadmap_id)
        if self._find_roadmap_error is not None:
            raise self._find_roadmap_error
        return self._roadmap

    def find_all_roadmaps(self) -> list[RoadmapRecord]:
        self.find_all_roadmaps_calls += 1
        if self._find_all_roadmaps_error is not None:
            raise self._find_all_roadmaps_error
        return list(self._roadmaps)

    def __getattr__(self, name: str) -> object:
        message = f"unexpected reader attribute access: {name}"
        raise AssertionError(message)


def _make_item(
    *,
    item_id: str,
    parent_id: str | None,
    level: Literal["major", "middle", "detail"],
    title: str,
    description: str,
    order: int,
    score: int,
    last_quiz_at: str | None,
) -> RoadmapItemRecord:
    return RoadmapItemRecord(
        id=UUID(item_id),
        parent_id=None if parent_id is None else UUID(parent_id),
        level=level,
        title=title,
        description=description,
        order=order,
        score=score,
        last_quiz_at=last_quiz_at,
    )


def _make_record(
    *,
    roadmap_id: UUID,
    topic: str,
    items: list[RoadmapItemRecord],
) -> RoadmapRecord:
    return RoadmapRecord(roadmap_id=roadmap_id, topic=topic, items=list(items))


def _make_node(
    *,
    item_id: str,
    title: str,
    description: str,
    level: Literal["major", "middle", "detail"],
    score: int,
    order: int,
    last_quiz_at: str | None,
    children: list[RoadmapTreeNode],
) -> RoadmapTreeNode:
    return RoadmapTreeNode(
        id=UUID(item_id),
        title=title,
        description=description,
        level=level,
        score=score,
        order=order,
        children=children,
        last_quiz_at=last_quiz_at,
    )


def _typescript_items_unsorted() -> list[RoadmapItemRecord]:
    return [
        _make_item(
            item_id="44444444-4444-4444-4444-444444444444",
            parent_id="22222222-2222-2222-2222-222222222222",
            level="detail",
            title="配列とタプル",
            description="配列型とタプル型の使い分け",
            order=1,
            score=60,
            last_quiz_at="2026-05-16T14:00:00+09:00",
        ),
        _make_item(
            item_id="77777777-7777-7777-7777-777777777777",
            parent_id=None,
            level="major",
            title="応用",
            description="TypeScript の応用技術",
            order=1,
            score=345,
            last_quiz_at="2026-05-20T00:00:00+09:00",
        ),
        _make_item(
            item_id="22222222-2222-2222-2222-222222222222",
            parent_id="11111111-1111-1111-1111-111111111111",
            level="middle",
            title="変数と型",
            description="型システムの基礎",
            order=0,
            score=222,
            last_quiz_at="2026-05-12T00:00:00+09:00",
        ),
        _make_item(
            item_id="99999999-9999-9999-9999-999999999999",
            parent_id="88888888-8888-8888-8888-888888888888",
            level="detail",
            title="基本構文",
            description="T extends U の基本",
            order=0,
            score=30,
            last_quiz_at="2026-05-18T11:00:00+09:00",
        ),
        _make_item(
            item_id="11111111-1111-1111-1111-111111111111",
            parent_id=None,
            level="major",
            title="基礎",
            description="TypeScript の基本概念",
            order=0,
            score=111,
            last_quiz_at="2026-05-11T00:00:00+09:00",
        ),
        _make_item(
            item_id="66666666-6666-6666-6666-666666666666",
            parent_id="55555555-5555-5555-5555-555555555555",
            level="detail",
            title="引数の型注釈",
            description="パラメータと戻り値の型指定",
            order=0,
            score=40,
            last_quiz_at="2026-05-17T09:00:00+09:00",
        ),
        _make_item(
            item_id="33333333-3333-3333-3333-333333333333",
            parent_id="22222222-2222-2222-2222-222222222222",
            level="detail",
            title="プリミティブ型",
            description="string, number, boolean 等の基本型",
            order=0,
            score=90,
            last_quiz_at="2026-05-15T10:00:00+09:00",
        ),
        _make_item(
            item_id="88888888-8888-8888-8888-888888888888",
            parent_id="77777777-7777-7777-7777-777777777777",
            level="middle",
            title="ジェネリクス",
            description="型パラメータによる汎用化",
            order=0,
            score=888,
            last_quiz_at="2026-05-13T00:00:00+09:00",
        ),
        _make_item(
            item_id="55555555-5555-5555-5555-555555555555",
            parent_id="11111111-1111-1111-1111-111111111111",
            level="middle",
            title="関数",
            description="関数の型付けと引数",
            order=1,
            score=555,
            last_quiz_at="2026-05-14T00:00:00+09:00",
        ),
    ]


def _typescript_expected_tree() -> RoadmapTree:
    return RoadmapTree(
        roadmap_id=_REQUEST_ROADMAP_ID,
        topic="TypeScript",
        overall_score=43,
        items=[
            _make_node(
                item_id="11111111-1111-1111-1111-111111111111",
                title="基礎",
                description="TypeScript の基本概念",
                level="major",
                score=57,
                order=0,
                last_quiz_at=None,
                children=[
                    _make_node(
                        item_id="22222222-2222-2222-2222-222222222222",
                        title="変数と型",
                        description="型システムの基礎",
                        level="middle",
                        score=75,
                        order=0,
                        last_quiz_at=None,
                        children=[
                            _make_node(
                                item_id="33333333-3333-3333-3333-333333333333",
                                title="プリミティブ型",
                                description="string, number, boolean 等の基本型",
                                level="detail",
                                score=90,
                                order=0,
                                last_quiz_at="2026-05-15T10:00:00+09:00",
                                children=[],
                            ),
                            _make_node(
                                item_id="44444444-4444-4444-4444-444444444444",
                                title="配列とタプル",
                                description="配列型とタプル型の使い分け",
                                level="detail",
                                score=60,
                                order=1,
                                last_quiz_at="2026-05-16T14:00:00+09:00",
                                children=[],
                            ),
                        ],
                    ),
                    _make_node(
                        item_id="55555555-5555-5555-5555-555555555555",
                        title="関数",
                        description="関数の型付けと引数",
                        level="middle",
                        score=40,
                        order=1,
                        last_quiz_at=None,
                        children=[
                            _make_node(
                                item_id="66666666-6666-6666-6666-666666666666",
                                title="引数の型注釈",
                                description="パラメータと戻り値の型指定",
                                level="detail",
                                score=40,
                                order=0,
                                last_quiz_at="2026-05-17T09:00:00+09:00",
                                children=[],
                            ),
                        ],
                    ),
                ],
            ),
            _make_node(
                item_id="77777777-7777-7777-7777-777777777777",
                title="応用",
                description="TypeScript の応用技術",
                level="major",
                score=30,
                order=1,
                last_quiz_at=None,
                children=[
                    _make_node(
                        item_id="88888888-8888-8888-8888-888888888888",
                        title="ジェネリクス",
                        description="型パラメータによる汎用化",
                        level="middle",
                        score=30,
                        order=0,
                        last_quiz_at=None,
                        children=[
                            _make_node(
                                item_id="99999999-9999-9999-9999-999999999999",
                                title="基本構文",
                                description="T extends U の基本",
                                level="detail",
                                score=30,
                                order=0,
                                last_quiz_at="2026-05-18T11:00:00+09:00",
                                children=[],
                            ),
                        ],
                    ),
                ],
            ),
        ],
    )


def _order_gap_items_unsorted() -> list[RoadmapItemRecord]:
    return [
        _make_item(
            item_id="24444444-4444-4444-4444-444444444444",
            parent_id="24222222-2222-2222-2222-222222222222",
            level="detail",
            title="高度な絞り込み",
            description="条件を組み合わせる",
            order=0,
            score=20,
            last_quiz_at="2026-05-19T10:00:00+09:00",
        ),
        _make_item(
            item_id="24222222-2222-2222-2222-222222222222",
            parent_id="24111111-1111-1111-1111-111111111111",
            level="middle",
            title="応用検索",
            description="複数条件の検索を扱う",
            order=2,
            score=0,
            last_quiz_at=None,
        ),
        _make_item(
            item_id="24111111-1111-1111-1111-111111111111",
            parent_id=None,
            level="major",
            title="検索",
            description="検索機能の学習",
            order=0,
            score=0,
            last_quiz_at=None,
        ),
        _make_item(
            item_id="24333333-3333-3333-3333-333333333333",
            parent_id="24211111-1111-1111-1111-111111111111",
            level="detail",
            title="キーワード検索",
            description="単一条件で検索する",
            order=0,
            score=80,
            last_quiz_at="2026-05-18T10:00:00+09:00",
        ),
        _make_item(
            item_id="24211111-1111-1111-1111-111111111111",
            parent_id="24111111-1111-1111-1111-111111111111",
            level="middle",
            title="基本検索",
            description="基本的な検索を学ぶ",
            order=0,
            score=0,
            last_quiz_at=None,
        ),
    ]


def test_tc_01_get_roadmap_builds_minimum_tree_and_logs_success() -> None:
    reader = _RecordingReader(
        roadmap=_make_record(
            roadmap_id=_RETURNED_ROADMAP_ID,
            topic="  TypeScript 入門  ",
            items=[
                _make_item(
                    item_id="11111111-1111-1111-1111-111111111111",
                    parent_id=None,
                    level="major",
                    title=" 基礎 ",
                    description=" 導入 ",
                    order=0,
                    score=999,
                    last_quiz_at="2026-05-01T00:00:00+09:00",
                ),
                _make_item(
                    item_id="22222222-2222-2222-2222-222222222222",
                    parent_id="11111111-1111-1111-1111-111111111111",
                    level="middle",
                    title=" 型 ",
                    description=" 基本 ",
                    order=0,
                    score=123,
                    last_quiz_at="2026-05-02T00:00:00+09:00",
                ),
                _make_item(
                    item_id="33333333-3333-3333-3333-333333333333",
                    parent_id="22222222-2222-2222-2222-222222222222",
                    level="detail",
                    title=" string ",
                    description=" 文字列 ",
                    order=0,
                    score=88,
                    last_quiz_at="2026-05-03T09:30:00+09:00",
                ),
            ],
        ),
    )

    with capture_logs() as log_output:
        result = get_roadmap(_REQUEST_ROADMAP_ID, reader=reader)

    assert result == RoadmapTree(
        roadmap_id=_RETURNED_ROADMAP_ID,
        topic="  TypeScript 入門  ",
        overall_score=88,
        items=[
            _make_node(
                item_id="11111111-1111-1111-1111-111111111111",
                title=" 基礎 ",
                description=" 導入 ",
                level="major",
                score=88,
                order=0,
                last_quiz_at=None,
                children=[
                    _make_node(
                        item_id="22222222-2222-2222-2222-222222222222",
                        title=" 型 ",
                        description=" 基本 ",
                        level="middle",
                        score=88,
                        order=0,
                        last_quiz_at=None,
                        children=[
                            _make_node(
                                item_id="33333333-3333-3333-3333-333333333333",
                                title=" string ",
                                description=" 文字列 ",
                                level="detail",
                                score=88,
                                order=0,
                                last_quiz_at="2026-05-03T09:30:00+09:00",
                                children=[],
                            ),
                        ],
                    ),
                ],
            ),
        ],
    )
    assert reader.find_roadmap_calls == [_REQUEST_ROADMAP_ID]
    _assert_single_log_event(
        log_output,
        "roadmap_retrieved",
        {
            "roadmap_id": str(_RETURNED_ROADMAP_ID),
            "topic": "  TypeScript 入門  ",
            "overall_score": 88,
            "item_count": 3,
        },
        log_level="info",
        str_coerce_fields=frozenset({"roadmap_id"}),
    )


def test_tc_10_get_roadmap_reconstructs_unsorted_tree_and_aggregates_scores() -> None:
    reader = _RecordingReader(
        roadmap=_make_record(
            roadmap_id=_REQUEST_ROADMAP_ID,
            topic="TypeScript",
            items=_typescript_items_unsorted(),
        ),
    )

    result = get_roadmap(_REQUEST_ROADMAP_ID, reader=reader)

    assert result == _typescript_expected_tree()
    assert reader.find_roadmap_calls == [_REQUEST_ROADMAP_ID]


def test_tc_11_get_roadmap_floors_scores_at_each_level() -> None:
    reader = _RecordingReader(
        roadmap=_make_record(
            roadmap_id=_FLOOR_ROADMAP_ID,
            topic="Python",
            items=[
                _make_item(
                    item_id="aa111111-1111-1111-1111-111111111111",
                    parent_id=None,
                    level="major",
                    title="基礎",
                    description="",
                    order=0,
                    score=0,
                    last_quiz_at=None,
                ),
                _make_item(
                    item_id="aa222222-2222-2222-2222-222222222222",
                    parent_id="aa111111-1111-1111-1111-111111111111",
                    level="middle",
                    title="データ構造",
                    description="",
                    order=0,
                    score=0,
                    last_quiz_at=None,
                ),
                _make_item(
                    item_id="aa333333-3333-3333-3333-333333333333",
                    parent_id="aa222222-2222-2222-2222-222222222222",
                    level="detail",
                    title="リスト",
                    description="",
                    order=0,
                    score=80,
                    last_quiz_at=None,
                ),
                _make_item(
                    item_id="aa444444-4444-4444-4444-444444444444",
                    parent_id="aa222222-2222-2222-2222-222222222222",
                    level="detail",
                    title="辞書",
                    description="",
                    order=1,
                    score=70,
                    last_quiz_at=None,
                ),
                _make_item(
                    item_id="aa555555-5555-5555-5555-555555555555",
                    parent_id="aa222222-2222-2222-2222-222222222222",
                    level="detail",
                    title="集合",
                    description="",
                    order=2,
                    score=50,
                    last_quiz_at=None,
                ),
            ],
        ),
    )

    result = get_roadmap(_FLOOR_ROADMAP_ID, reader=reader)

    assert result == RoadmapTree(
        roadmap_id=_FLOOR_ROADMAP_ID,
        topic="Python",
        overall_score=66,
        items=[
            _make_node(
                item_id="aa111111-1111-1111-1111-111111111111",
                title="基礎",
                description="",
                level="major",
                score=66,
                order=0,
                last_quiz_at=None,
                children=[
                    _make_node(
                        item_id="aa222222-2222-2222-2222-222222222222",
                        title="データ構造",
                        description="",
                        level="middle",
                        score=66,
                        order=0,
                        last_quiz_at=None,
                        children=[
                            _make_node(
                                item_id="aa333333-3333-3333-3333-333333333333",
                                title="リスト",
                                description="",
                                level="detail",
                                score=80,
                                order=0,
                                last_quiz_at=None,
                                children=[],
                            ),
                            _make_node(
                                item_id="aa444444-4444-4444-4444-444444444444",
                                title="辞書",
                                description="",
                                level="detail",
                                score=70,
                                order=1,
                                last_quiz_at=None,
                                children=[],
                            ),
                            _make_node(
                                item_id="aa555555-5555-5555-5555-555555555555",
                                title="集合",
                                description="",
                                level="detail",
                                score=50,
                                order=2,
                                last_quiz_at=None,
                                children=[],
                            ),
                        ],
                    ),
                ],
            ),
        ],
    )


def test_tc_12_list_roadmaps_preserves_reader_order_and_logs_success() -> None:
    rust_record = _make_record(
        roadmap_id=_EMPTY_ROADMAP_ID,
        topic="Rust",
        items=[],
    )
    typescript_record = _make_record(
        roadmap_id=_REQUEST_ROADMAP_ID,
        topic="TypeScript",
        items=_typescript_items_unsorted(),
    )
    reader = _RecordingReader(roadmaps=[rust_record, typescript_record])

    with capture_logs() as log_output:
        result = list_roadmaps(reader=reader)

    assert result == RoadmapListResult(
        items=[
            RoadmapListItem(
                roadmap_id=_EMPTY_ROADMAP_ID,
                topic="Rust",
                overall_score=0,
            ),
            RoadmapListItem(
                roadmap_id=_REQUEST_ROADMAP_ID,
                topic="TypeScript",
                overall_score=43,
            ),
        ],
        total_count=2,
    )
    assert reader.find_all_roadmaps_calls == 1
    _assert_single_log_event(
        log_output,
        "roadmap_list_retrieved",
        {"total_count": 2},
        log_level="info",
    )


def test_tc_13_get_roadmap_builds_tree_when_sibling_order_has_gaps() -> None:
    reader = _RecordingReader(
        roadmap=_make_record(
            roadmap_id=_ORDER_GAP_ROADMAP_ID,
            topic="Search",
            items=_order_gap_items_unsorted(),
        ),
    )

    result = get_roadmap(_ORDER_GAP_ROADMAP_ID, reader=reader)

    assert result == RoadmapTree(
        roadmap_id=_ORDER_GAP_ROADMAP_ID,
        topic="Search",
        overall_score=50,
        items=[
            _make_node(
                item_id="24111111-1111-1111-1111-111111111111",
                title="検索",
                description="検索機能の学習",
                level="major",
                score=50,
                order=0,
                last_quiz_at=None,
                children=[
                    _make_node(
                        item_id="24211111-1111-1111-1111-111111111111",
                        title="基本検索",
                        description="基本的な検索を学ぶ",
                        level="middle",
                        score=80,
                        order=0,
                        last_quiz_at=None,
                        children=[
                            _make_node(
                                item_id="24333333-3333-3333-3333-333333333333",
                                title="キーワード検索",
                                description="単一条件で検索する",
                                level="detail",
                                score=80,
                                order=0,
                                last_quiz_at="2026-05-18T10:00:00+09:00",
                                children=[],
                            ),
                        ],
                    ),
                    _make_node(
                        item_id="24222222-2222-2222-2222-222222222222",
                        title="応用検索",
                        description="複数条件の検索を扱う",
                        level="middle",
                        score=20,
                        order=2,
                        last_quiz_at=None,
                        children=[
                            _make_node(
                                item_id="24444444-4444-4444-4444-444444444444",
                                title="高度な絞り込み",
                                description="条件を組み合わせる",
                                level="detail",
                                score=20,
                                order=0,
                                last_quiz_at="2026-05-19T10:00:00+09:00",
                                children=[],
                            ),
                        ],
                    ),
                ],
            ),
        ],
    )


def test_tc_14_list_roadmaps_returns_result_when_sibling_order_has_gaps() -> None:
    reader = _RecordingReader(
        roadmaps=[
            _make_record(
                roadmap_id=_ORDER_GAP_ROADMAP_ID,
                topic="Search",
                items=_order_gap_items_unsorted(),
            ),
        ],
    )

    result = list_roadmaps(reader=reader)

    assert result == RoadmapListResult(
        items=[
            RoadmapListItem(
                roadmap_id=_ORDER_GAP_ROADMAP_ID,
                topic="Search",
                overall_score=50,
            ),
        ],
        total_count=1,
    )


def test_tc_20_get_roadmap_returns_empty_roadmap() -> None:
    reader = _RecordingReader(
        roadmap=_make_record(
            roadmap_id=_EMPTY_ROADMAP_ID,
            topic="Rust",
            items=[],
        ),
    )

    result = get_roadmap(_EMPTY_ROADMAP_ID, reader=reader)

    assert result == RoadmapTree(
        roadmap_id=_EMPTY_ROADMAP_ID,
        topic="Rust",
        overall_score=0,
        items=[],
    )


def test_tc_21_get_roadmap_uses_zero_for_middle_without_details() -> None:
    reader = _RecordingReader(
        roadmap=_make_record(
            roadmap_id=_MIDDLE_EMPTY_ROADMAP_ID,
            topic="Edge Case A",
            items=[
                _make_item(
                    item_id="21111111-1111-1111-1111-111111111111",
                    parent_id=None,
                    level="major",
                    title="Major",
                    description="",
                    order=0,
                    score=999,
                    last_quiz_at="2026-05-01T00:00:00+09:00",
                ),
                _make_item(
                    item_id="21111111-1111-1111-1111-111111111112",
                    parent_id="21111111-1111-1111-1111-111111111111",
                    level="middle",
                    title="Middle A",
                    description="",
                    order=0,
                    score=123,
                    last_quiz_at="2026-05-02T00:00:00+09:00",
                ),
                _make_item(
                    item_id="21111111-1111-1111-1111-111111111113",
                    parent_id="21111111-1111-1111-1111-111111111111",
                    level="middle",
                    title="Middle B",
                    description="",
                    order=1,
                    score=456,
                    last_quiz_at="2026-05-03T00:00:00+09:00",
                ),
                _make_item(
                    item_id="21111111-1111-1111-1111-111111111114",
                    parent_id="21111111-1111-1111-1111-111111111113",
                    level="detail",
                    title="Detail B1",
                    description="",
                    order=0,
                    score=100,
                    last_quiz_at="2026-05-04T09:00:00+09:00",
                ),
                _make_item(
                    item_id="21111111-1111-1111-1111-111111111115",
                    parent_id="21111111-1111-1111-1111-111111111113",
                    level="detail",
                    title="Detail B2",
                    description="",
                    order=1,
                    score=50,
                    last_quiz_at="2026-05-05T09:00:00+09:00",
                ),
            ],
        ),
    )

    result = get_roadmap(_MIDDLE_EMPTY_ROADMAP_ID, reader=reader)

    assert result == RoadmapTree(
        roadmap_id=_MIDDLE_EMPTY_ROADMAP_ID,
        topic="Edge Case A",
        overall_score=37,
        items=[
            _make_node(
                item_id="21111111-1111-1111-1111-111111111111",
                title="Major",
                description="",
                level="major",
                score=37,
                order=0,
                last_quiz_at=None,
                children=[
                    _make_node(
                        item_id="21111111-1111-1111-1111-111111111112",
                        title="Middle A",
                        description="",
                        level="middle",
                        score=0,
                        order=0,
                        last_quiz_at=None,
                        children=[],
                    ),
                    _make_node(
                        item_id="21111111-1111-1111-1111-111111111113",
                        title="Middle B",
                        description="",
                        level="middle",
                        score=75,
                        order=1,
                        last_quiz_at=None,
                        children=[
                            _make_node(
                                item_id="21111111-1111-1111-1111-111111111114",
                                title="Detail B1",
                                description="",
                                level="detail",
                                score=100,
                                order=0,
                                last_quiz_at="2026-05-04T09:00:00+09:00",
                                children=[],
                            ),
                            _make_node(
                                item_id="21111111-1111-1111-1111-111111111115",
                                title="Detail B2",
                                description="",
                                level="detail",
                                score=50,
                                order=1,
                                last_quiz_at="2026-05-05T09:00:00+09:00",
                                children=[],
                            ),
                        ],
                    ),
                ],
            ),
        ],
    )


def test_tc_22_get_roadmap_uses_zero_for_major_without_middle_children() -> None:
    reader = _RecordingReader(
        roadmap=_make_record(
            roadmap_id=_MAJOR_EMPTY_ROADMAP_ID,
            topic="Edge Case B",
            items=[
                _make_item(
                    item_id="22111111-1111-1111-1111-111111111111",
                    parent_id=None,
                    level="major",
                    title="Major A",
                    description="",
                    order=0,
                    score=999,
                    last_quiz_at="2026-05-01T00:00:00+09:00",
                ),
                _make_item(
                    item_id="22111111-1111-1111-1111-111111111112",
                    parent_id=None,
                    level="major",
                    title="Major B",
                    description="",
                    order=1,
                    score=888,
                    last_quiz_at="2026-05-02T00:00:00+09:00",
                ),
                _make_item(
                    item_id="22111111-1111-1111-1111-111111111113",
                    parent_id="22111111-1111-1111-1111-111111111112",
                    level="middle",
                    title="Middle B1",
                    description="",
                    order=0,
                    score=777,
                    last_quiz_at="2026-05-03T00:00:00+09:00",
                ),
                _make_item(
                    item_id="22111111-1111-1111-1111-111111111114",
                    parent_id="22111111-1111-1111-1111-111111111113",
                    level="detail",
                    title="Detail B1",
                    description="",
                    order=0,
                    score=80,
                    last_quiz_at="2026-05-04T09:00:00+09:00",
                ),
            ],
        ),
    )

    result = get_roadmap(_MAJOR_EMPTY_ROADMAP_ID, reader=reader)

    assert result == RoadmapTree(
        roadmap_id=_MAJOR_EMPTY_ROADMAP_ID,
        topic="Edge Case B",
        overall_score=40,
        items=[
            _make_node(
                item_id="22111111-1111-1111-1111-111111111111",
                title="Major A",
                description="",
                level="major",
                score=0,
                order=0,
                last_quiz_at=None,
                children=[],
            ),
            _make_node(
                item_id="22111111-1111-1111-1111-111111111112",
                title="Major B",
                description="",
                level="major",
                score=80,
                order=1,
                last_quiz_at=None,
                children=[
                    _make_node(
                        item_id="22111111-1111-1111-1111-111111111113",
                        title="Middle B1",
                        description="",
                        level="middle",
                        score=80,
                        order=0,
                        last_quiz_at=None,
                        children=[
                            _make_node(
                                item_id="22111111-1111-1111-1111-111111111114",
                                title="Detail B1",
                                description="",
                                level="detail",
                                score=80,
                                order=0,
                                last_quiz_at="2026-05-04T09:00:00+09:00",
                                children=[],
                            ),
                        ],
                    ),
                ],
            ),
        ],
    )


def test_tc_23_get_roadmap_keeps_all_zero_scores_zero() -> None:
    reader = _RecordingReader(
        roadmap=_make_record(
            roadmap_id=_ALL_ZERO_ROADMAP_ID,
            topic="Edge Case C",
            items=[
                _make_item(
                    item_id="23111111-1111-1111-1111-111111111111",
                    parent_id=None,
                    level="major",
                    title="Major",
                    description="",
                    order=0,
                    score=999,
                    last_quiz_at="2026-05-01T00:00:00+09:00",
                ),
                _make_item(
                    item_id="23111111-1111-1111-1111-111111111112",
                    parent_id="23111111-1111-1111-1111-111111111111",
                    level="middle",
                    title="Middle A",
                    description="",
                    order=0,
                    score=888,
                    last_quiz_at="2026-05-02T00:00:00+09:00",
                ),
                _make_item(
                    item_id="23111111-1111-1111-1111-111111111113",
                    parent_id="23111111-1111-1111-1111-111111111111",
                    level="middle",
                    title="Middle B",
                    description="",
                    order=1,
                    score=777,
                    last_quiz_at="2026-05-03T00:00:00+09:00",
                ),
                _make_item(
                    item_id="23111111-1111-1111-1111-111111111114",
                    parent_id="23111111-1111-1111-1111-111111111112",
                    level="detail",
                    title="Detail A1",
                    description="",
                    order=0,
                    score=0,
                    last_quiz_at="2026-05-04T09:00:00+09:00",
                ),
                _make_item(
                    item_id="23111111-1111-1111-1111-111111111115",
                    parent_id="23111111-1111-1111-1111-111111111112",
                    level="detail",
                    title="Detail A2",
                    description="",
                    order=1,
                    score=0,
                    last_quiz_at="2026-05-05T09:00:00+09:00",
                ),
                _make_item(
                    item_id="23111111-1111-1111-1111-111111111116",
                    parent_id="23111111-1111-1111-1111-111111111113",
                    level="detail",
                    title="Detail B1",
                    description="",
                    order=0,
                    score=0,
                    last_quiz_at="2026-05-06T09:00:00+09:00",
                ),
            ],
        ),
    )

    result = get_roadmap(_ALL_ZERO_ROADMAP_ID, reader=reader)

    assert result == RoadmapTree(
        roadmap_id=_ALL_ZERO_ROADMAP_ID,
        topic="Edge Case C",
        overall_score=0,
        items=[
            _make_node(
                item_id="23111111-1111-1111-1111-111111111111",
                title="Major",
                description="",
                level="major",
                score=0,
                order=0,
                last_quiz_at=None,
                children=[
                    _make_node(
                        item_id="23111111-1111-1111-1111-111111111112",
                        title="Middle A",
                        description="",
                        level="middle",
                        score=0,
                        order=0,
                        last_quiz_at=None,
                        children=[
                            _make_node(
                                item_id="23111111-1111-1111-1111-111111111114",
                                title="Detail A1",
                                description="",
                                level="detail",
                                score=0,
                                order=0,
                                last_quiz_at="2026-05-04T09:00:00+09:00",
                                children=[],
                            ),
                            _make_node(
                                item_id="23111111-1111-1111-1111-111111111115",
                                title="Detail A2",
                                description="",
                                level="detail",
                                score=0,
                                order=1,
                                last_quiz_at="2026-05-05T09:00:00+09:00",
                                children=[],
                            ),
                        ],
                    ),
                    _make_node(
                        item_id="23111111-1111-1111-1111-111111111113",
                        title="Middle B",
                        description="",
                        level="middle",
                        score=0,
                        order=1,
                        last_quiz_at=None,
                        children=[
                            _make_node(
                                item_id="23111111-1111-1111-1111-111111111116",
                                title="Detail B1",
                                description="",
                                level="detail",
                                score=0,
                                order=0,
                                last_quiz_at="2026-05-06T09:00:00+09:00",
                                children=[],
                            ),
                        ],
                    ),
                ],
            ),
        ],
    )


def test_tc_24_list_roadmaps_returns_empty_result_and_logs_success() -> None:
    reader = _RecordingReader(roadmaps=[])

    with capture_logs() as log_output:
        result = list_roadmaps(reader=reader)

    assert result == RoadmapListResult(items=[], total_count=0)
    assert reader.find_all_roadmaps_calls == 1
    _assert_single_log_event(
        log_output,
        "roadmap_list_retrieved",
        {"total_count": 0},
        log_level="info",
    )


def test_tc_30_get_roadmap_raises_not_found_and_logs_warning() -> None:
    reader = _RecordingReader(roadmap=None)

    with capture_logs() as log_output, pytest.raises(RoadmapRetrievalNotFoundError):
        get_roadmap(_NOT_FOUND_ROADMAP_ID, reader=reader)

    assert reader.find_roadmap_calls == [_NOT_FOUND_ROADMAP_ID]
    _assert_single_log_event(
        log_output,
        "roadmap_not_found",
        {"roadmap_id": str(_NOT_FOUND_ROADMAP_ID)},
        log_level="warning",
        str_coerce_fields=frozenset({"roadmap_id"}),
    )


def test_tc_31_get_roadmap_wraps_reader_error_and_logs_error() -> None:
    reader = _RecordingReader(find_roadmap_error=TimeoutError("reader timeout"))

    with capture_logs() as log_output, pytest.raises(RoadmapRetrievalStoreError):
        get_roadmap(_STORE_ERROR_ROADMAP_ID, reader=reader)

    assert reader.find_roadmap_calls == [_STORE_ERROR_ROADMAP_ID]
    _assert_single_log_event(
        log_output,
        "roadmap_retrieval_store_failed",
        {
            "roadmap_id": str(_STORE_ERROR_ROADMAP_ID),
            "error_type": "TimeoutError",
        },
        log_level="error",
        str_coerce_fields=frozenset({"roadmap_id"}),
    )


def test_tc_32_list_roadmaps_wraps_reader_error_and_logs_error() -> None:
    reader = _RecordingReader(
        find_all_roadmaps_error=ConnectionError("db unavailable"),
    )

    with capture_logs() as log_output, pytest.raises(RoadmapRetrievalStoreError):
        list_roadmaps(reader=reader)

    assert reader.find_all_roadmaps_calls == 1
    _assert_single_log_event(
        log_output,
        "roadmap_retrieval_store_failed",
        {"error_type": "ConnectionError"},
        log_level="error",
    )
