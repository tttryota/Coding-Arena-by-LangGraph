from __future__ import annotations

from typing import TYPE_CHECKING, Literal
from uuid import UUID

import pytest
from structlog.testing import capture_logs

from roadmap.application.roadmap_persistence import save_roadmap
from roadmap.domain.roadmap_persistence_types import (
    FlatRoadmapItem,
    RoadmapItemInput,
    RoadmapPersistenceInputError,
    RoadmapPersistenceWriteError,
    RoadmapSaveInput,
    RoadmapSaveResult,
)
from shared.log_assertions import assert_no_log_event as _assert_no_log_event
from shared.log_assertions import (
    assert_single_log_event as _shared_assert_single_log_event,
)

if TYPE_CHECKING:
    from collections.abc import MutableMapping
    from typing import Any


_ROADMAP_ID = UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")
_MAJOR_ID = UUID("11111111-1111-1111-1111-111111111111")
_MIDDLE_ID = UUID("22222222-2222-2222-2222-222222222222")
_DETAIL_ID = UUID("33333333-3333-3333-3333-333333333333")
_DETAIL_ID_TWO = UUID("44444444-4444-4444-4444-444444444444")
_MIDDLE_ID_TWO = UUID("55555555-5555-5555-5555-555555555555")
_DETAIL_ID_THREE = UUID("66666666-6666-6666-6666-666666666666")
_MAJOR_ID_TWO = UUID("77777777-7777-7777-7777-777777777777")
_MIDDLE_ID_THREE = UUID("88888888-8888-8888-8888-888888888888")
_DETAIL_ID_FOUR = UUID("99999999-9999-9999-9999-999999999999")
_EMPTY_ROADMAP_ID = UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb")
_MIN_ROADMAP_ID = UUID("12121212-1212-1212-1212-121212121212")
_MIN_MAJOR_ID = UUID("13131313-1313-1313-1313-131313131313")
_MIN_MIDDLE_ID = UUID("14141414-1414-1414-1414-141414141414")
_MIN_DETAIL_ID = UUID("15151515-1515-1515-1515-151515151515")
_DFS_ROADMAP_ID = UUID("01010101-0101-0101-0101-010101010101")
_DFS_MAJOR_ID = UUID("02020202-0202-0202-0202-020202020202")
_DFS_MIDDLE_ID = UUID("03030303-0303-0303-0303-030303030303")
_DFS_DETAIL_ID = UUID("04040404-0404-0404-0404-040404040404")
_DFS_DETAIL_ID_TWO = UUID("05050505-0505-0505-0505-050505050505")
_DFS_MIDDLE_ID_TWO = UUID("06060606-0606-0606-0606-060606060606")
_DFS_DETAIL_ID_THREE = UUID("07070707-0707-0707-0707-070707070707")
_DFS_MAJOR_ID_TWO = UUID("08080808-0808-0808-0808-080808080808")
_DFS_MIDDLE_ID_THREE = UUID("09090909-0909-0909-0909-090909090909")
_WHITESPACE_ROADMAP_ID = UUID("21212121-2121-2121-2121-212121212121")
_WHITESPACE_MAJOR_ID = UUID("22222222-1111-1111-1111-111111111111")
_WHITESPACE_MIDDLE_ID = UUID("23232323-2323-2323-2323-232323232323")
_WHITESPACE_DETAIL_ID = UUID("24242424-2424-2424-2424-242424242424")
_MAJOR_ONLY_ROADMAP_ID = UUID("31313131-3131-3131-3131-313131313131")
_MAJOR_ONLY_ID = UUID("32323232-3232-3232-3232-323232323232")
_MIDDLE_ONLY_ROADMAP_ID = UUID("41414141-4141-4141-4141-414141414141")
_MIDDLE_ONLY_MAJOR_ID = UUID("42424242-4242-4242-4242-424242424242")
_MIDDLE_ONLY_MIDDLE_ID = UUID("43434343-4343-4343-4343-434343434343")

_ROADMAP_ID_COERCE = frozenset({"roadmap_id"})


class _SequenceIdGenerator:
    def __init__(self, generated_ids: list[UUID]) -> None:
        self._generated_ids = list(generated_ids)
        self.calls = 0

    def generate(self) -> UUID:
        self.calls += 1
        assert self._generated_ids
        return self._generated_ids.pop(0)


class _RecordingWriter:
    def __init__(self, *, error: Exception | None = None) -> None:
        self._error = error
        self.calls: list[tuple[UUID, str, list[FlatRoadmapItem]]] = []

    def save_items(
        self,
        roadmap_id: UUID,
        topic: str,
        items: list[FlatRoadmapItem],
    ) -> None:
        self.calls.append((roadmap_id, topic, list(items)))
        if self._error is not None:
            raise self._error


def _assert_single_log_event_includes(
    log_output: list[MutableMapping[str, Any]],
    event_name: str,
    expected_fields: dict[str, object],
) -> MutableMapping[str, Any]:
    return _shared_assert_single_log_event(
        log_output,
        event_name,
        expected_fields,
        str_coerce_fields=_ROADMAP_ID_COERCE,
    )


def _detail(
    *,
    title: str = "変数",
    description: str = "説明",
    children: list[RoadmapItemInput] | None = None,
) -> RoadmapItemInput:
    return RoadmapItemInput(
        title=title,
        description=description,
        level="detail",
        children=list(children or []),
    )


def _middle(
    *,
    title: str = "文法",
    description: str = "説明",
    children: list[RoadmapItemInput] | None = None,
) -> RoadmapItemInput:
    return RoadmapItemInput(
        title=title,
        description=description,
        level="middle",
        children=list(children or []),
    )


def _major(
    *,
    title: str = "基礎",
    description: str = "説明",
    children: list[RoadmapItemInput] | None = None,
) -> RoadmapItemInput:
    return RoadmapItemInput(
        title=title,
        description=description,
        level="major",
        children=list(children or []),
    )


def _make_input(
    *,
    topic: str = "TypeScript",
    items: list[RoadmapItemInput] | None = None,
    created_at: str = "2026-05-21T10:00:00+09:00",
) -> RoadmapSaveInput:
    return RoadmapSaveInput(
        topic=topic,
        items=list(items or []),
        created_at=created_at,
    )


def _make_minimal_valid_input(
    *,
    topic: str = "Go",
    major_title: str = "基礎",
    middle_title: str = "文法",
    detail_title: str = "変数",
    detail_description: str = "識別子の基本",
    created_at: str = "2026-05-21T11:00:00+09:00",
) -> RoadmapSaveInput:
    return _make_input(
        topic=topic,
        created_at=created_at,
        items=[
            _major(
                title=major_title,
                description="Go の基礎",
                children=[
                    _middle(
                        title=middle_title,
                        description="文法の入り口",
                        children=[
                            _detail(
                                title=detail_title,
                                description=detail_description,
                            ),
                        ],
                    ),
                ],
            ),
        ],
    )


def _assert_input_error(
    roadmap_input: RoadmapSaveInput,
) -> str:
    writer = _RecordingWriter()
    id_generator = _SequenceIdGenerator([_ROADMAP_ID])

    with pytest.raises(RoadmapPersistenceInputError) as exc_info:
        save_roadmap(
            roadmap_input,
            writer=writer,
            id_generator=id_generator,
        )

    assert id_generator.calls == 0
    assert writer.calls == []
    return str(exc_info.value)


class TestSaveRoadmap:
    def test_tc_01_flattens_example_one_and_saves_all_fields(self) -> None:
        # Arrange
        roadmap_input = _make_input(
            items=[
                _major(
                    title="基礎",
                    description="TypeScript の基本概念",
                    children=[
                        _middle(
                            title="変数と型",
                            description="型システムの基礎",
                            children=[
                                _detail(
                                    title="プリミティブ型",
                                    description=("string, number, boolean 等の基本型"),
                                ),
                                _detail(
                                    title="配列とタプル",
                                    description=("配列型とタプル型の使い分け"),
                                ),
                            ],
                        ),
                        _middle(
                            title="関数",
                            description="関数の型付けと引数",
                            children=[
                                _detail(
                                    title="引数の型注釈",
                                    description="パラメータと戻り値の型指定",
                                ),
                            ],
                        ),
                    ],
                ),
                _major(
                    title="応用",
                    description="TypeScript の応用技術",
                    children=[
                        _middle(
                            title="ジェネリクス",
                            description="型パラメータによる汎用化",
                            children=[
                                _detail(
                                    title="基本構文",
                                    description="T extends U の基本",
                                ),
                            ],
                        ),
                    ],
                ),
            ],
        )
        id_generator = _SequenceIdGenerator(
            [
                _ROADMAP_ID,
                _MAJOR_ID,
                _MIDDLE_ID,
                _DETAIL_ID,
                _DETAIL_ID_TWO,
                _MIDDLE_ID_TWO,
                _DETAIL_ID_THREE,
                _MAJOR_ID_TWO,
                _MIDDLE_ID_THREE,
                _DETAIL_ID_FOUR,
            ],
        )
        writer = _RecordingWriter()
        expected_items = [
            FlatRoadmapItem(
                id=_MAJOR_ID,
                roadmap_id=_ROADMAP_ID,
                parent_id=None,
                level="major",
                title="基礎",
                description="TypeScript の基本概念",
                order=0,
                score=0,
                created_at="2026-05-21T10:00:00+09:00",
                updated_at="2026-05-21T10:00:00+09:00",
            ),
            FlatRoadmapItem(
                id=_MIDDLE_ID,
                roadmap_id=_ROADMAP_ID,
                parent_id=_MAJOR_ID,
                level="middle",
                title="変数と型",
                description="型システムの基礎",
                order=0,
                score=0,
                created_at="2026-05-21T10:00:00+09:00",
                updated_at="2026-05-21T10:00:00+09:00",
            ),
            FlatRoadmapItem(
                id=_DETAIL_ID,
                roadmap_id=_ROADMAP_ID,
                parent_id=_MIDDLE_ID,
                level="detail",
                title="プリミティブ型",
                description="string, number, boolean 等の基本型",
                order=0,
                score=0,
                created_at="2026-05-21T10:00:00+09:00",
                updated_at="2026-05-21T10:00:00+09:00",
            ),
            FlatRoadmapItem(
                id=_DETAIL_ID_TWO,
                roadmap_id=_ROADMAP_ID,
                parent_id=_MIDDLE_ID,
                level="detail",
                title="配列とタプル",
                description="配列型とタプル型の使い分け",
                order=1,
                score=0,
                created_at="2026-05-21T10:00:00+09:00",
                updated_at="2026-05-21T10:00:00+09:00",
            ),
            FlatRoadmapItem(
                id=_MIDDLE_ID_TWO,
                roadmap_id=_ROADMAP_ID,
                parent_id=_MAJOR_ID,
                level="middle",
                title="関数",
                description="関数の型付けと引数",
                order=1,
                score=0,
                created_at="2026-05-21T10:00:00+09:00",
                updated_at="2026-05-21T10:00:00+09:00",
            ),
            FlatRoadmapItem(
                id=_DETAIL_ID_THREE,
                roadmap_id=_ROADMAP_ID,
                parent_id=_MIDDLE_ID_TWO,
                level="detail",
                title="引数の型注釈",
                description="パラメータと戻り値の型指定",
                order=0,
                score=0,
                created_at="2026-05-21T10:00:00+09:00",
                updated_at="2026-05-21T10:00:00+09:00",
            ),
            FlatRoadmapItem(
                id=_MAJOR_ID_TWO,
                roadmap_id=_ROADMAP_ID,
                parent_id=None,
                level="major",
                title="応用",
                description="TypeScript の応用技術",
                order=1,
                score=0,
                created_at="2026-05-21T10:00:00+09:00",
                updated_at="2026-05-21T10:00:00+09:00",
            ),
            FlatRoadmapItem(
                id=_MIDDLE_ID_THREE,
                roadmap_id=_ROADMAP_ID,
                parent_id=_MAJOR_ID_TWO,
                level="middle",
                title="ジェネリクス",
                description="型パラメータによる汎用化",
                order=0,
                score=0,
                created_at="2026-05-21T10:00:00+09:00",
                updated_at="2026-05-21T10:00:00+09:00",
            ),
            FlatRoadmapItem(
                id=_DETAIL_ID_FOUR,
                roadmap_id=_ROADMAP_ID,
                parent_id=_MIDDLE_ID_THREE,
                level="detail",
                title="基本構文",
                description="T extends U の基本",
                order=0,
                score=0,
                created_at="2026-05-21T10:00:00+09:00",
                updated_at="2026-05-21T10:00:00+09:00",
            ),
        ]

        # Act
        result = save_roadmap(
            roadmap_input,
            writer=writer,
            id_generator=id_generator,
        )

        # Assert
        assert result == RoadmapSaveResult(
            roadmap_id=_ROADMAP_ID,
            saved_count=9,
        )
        assert id_generator.calls == 10
        assert writer.calls == [
            (_ROADMAP_ID, "TypeScript", expected_items),
        ]

    def test_tc_02_saves_empty_roadmap(self) -> None:
        # Arrange
        roadmap_input = _make_input(
            topic="Rust",
            items=[],
            created_at="2026-05-21T10:30:00+09:00",
        )
        id_generator = _SequenceIdGenerator([_EMPTY_ROADMAP_ID])
        writer = _RecordingWriter()

        # Act
        result = save_roadmap(
            roadmap_input,
            writer=writer,
            id_generator=id_generator,
        )

        # Assert
        assert result == RoadmapSaveResult(
            roadmap_id=_EMPTY_ROADMAP_ID,
            saved_count=0,
        )
        assert id_generator.calls == 1
        assert writer.calls == [
            (_EMPTY_ROADMAP_ID, "Rust", []),
        ]

    def test_tc_03_saves_minimal_valid_three_record_tree(self) -> None:
        # Arrange
        roadmap_input = _make_minimal_valid_input()
        id_generator = _SequenceIdGenerator(
            [_MIN_ROADMAP_ID, _MIN_MAJOR_ID, _MIN_MIDDLE_ID, _MIN_DETAIL_ID],
        )
        writer = _RecordingWriter()

        # Act
        result = save_roadmap(
            roadmap_input,
            writer=writer,
            id_generator=id_generator,
        )

        # Assert
        assert result == RoadmapSaveResult(
            roadmap_id=_MIN_ROADMAP_ID,
            saved_count=3,
        )
        assert writer.calls == [
            (
                _MIN_ROADMAP_ID,
                "Go",
                [
                    FlatRoadmapItem(
                        id=_MIN_MAJOR_ID,
                        roadmap_id=_MIN_ROADMAP_ID,
                        parent_id=None,
                        level="major",
                        title="基礎",
                        description="Go の基礎",
                        order=0,
                        score=0,
                        created_at="2026-05-21T11:00:00+09:00",
                        updated_at="2026-05-21T11:00:00+09:00",
                    ),
                    FlatRoadmapItem(
                        id=_MIN_MIDDLE_ID,
                        roadmap_id=_MIN_ROADMAP_ID,
                        parent_id=_MIN_MAJOR_ID,
                        level="middle",
                        title="文法",
                        description="文法の入り口",
                        order=0,
                        score=0,
                        created_at="2026-05-21T11:00:00+09:00",
                        updated_at="2026-05-21T11:00:00+09:00",
                    ),
                    FlatRoadmapItem(
                        id=_MIN_DETAIL_ID,
                        roadmap_id=_MIN_ROADMAP_ID,
                        parent_id=_MIN_MIDDLE_ID,
                        level="detail",
                        title="変数",
                        description="識別子の基本",
                        order=0,
                        score=0,
                        created_at="2026-05-21T11:00:00+09:00",
                        updated_at="2026-05-21T11:00:00+09:00",
                    ),
                ],
            ),
        ]

    def test_tc_10_preserves_dfs_preorder_and_sibling_order(self) -> None:
        # Arrange
        roadmap_input = _make_input(
            topic="Algorithms",
            items=[
                _major(
                    title="探索",
                    children=[
                        _middle(
                            title="深さ優先探索",
                            children=[
                                _detail(title="再帰"),
                                _detail(title="スタック"),
                            ],
                        ),
                        _middle(
                            title="幅優先探索",
                            children=[
                                _detail(title="キュー"),
                            ],
                        ),
                    ],
                ),
                _major(
                    title="グラフ",
                    children=[
                        _middle(title="最短経路", children=[]),
                    ],
                ),
            ],
        )
        id_generator = _SequenceIdGenerator(
            [
                _DFS_ROADMAP_ID,
                _DFS_MAJOR_ID,
                _DFS_MIDDLE_ID,
                _DFS_DETAIL_ID,
                _DFS_DETAIL_ID_TWO,
                _DFS_MIDDLE_ID_TWO,
                _DFS_DETAIL_ID_THREE,
                _DFS_MAJOR_ID_TWO,
                _DFS_MIDDLE_ID_THREE,
            ],
        )
        writer = _RecordingWriter()

        # Act
        save_roadmap(
            roadmap_input,
            writer=writer,
            id_generator=id_generator,
        )

        # Assert
        assert len(writer.calls) == 1
        _, _, saved_items = writer.calls[0]
        assert [item.id for item in saved_items] == [
            _DFS_MAJOR_ID,
            _DFS_MIDDLE_ID,
            _DFS_DETAIL_ID,
            _DFS_DETAIL_ID_TWO,
            _DFS_MIDDLE_ID_TWO,
            _DFS_DETAIL_ID_THREE,
            _DFS_MAJOR_ID_TWO,
            _DFS_MIDDLE_ID_THREE,
        ]
        assert [item.title for item in saved_items] == [
            "探索",
            "深さ優先探索",
            "再帰",
            "スタック",
            "幅優先探索",
            "キュー",
            "グラフ",
            "最短経路",
        ]
        assert [item.order for item in saved_items] == [0, 0, 0, 1, 1, 0, 1, 0]
        assert [item.parent_id for item in saved_items] == [
            None,
            _DFS_MAJOR_ID,
            _DFS_MIDDLE_ID,
            _DFS_MIDDLE_ID,
            _DFS_MAJOR_ID,
            _DFS_MIDDLE_ID_TWO,
            None,
            _DFS_MAJOR_ID_TWO,
        ]

    def test_tc_11_preserves_whitespace_in_saved_topic_and_titles(self) -> None:
        # Arrange
        roadmap_input = _make_minimal_valid_input(
            topic="  TypeScript 入門  ",
            major_title="  基礎  ",
            middle_title="  型  ",
            detail_title="  string  ",
            detail_description="",
            created_at="2026-05-21T12:00:00+09:00",
        )
        id_generator = _SequenceIdGenerator(
            [
                _WHITESPACE_ROADMAP_ID,
                _WHITESPACE_MAJOR_ID,
                _WHITESPACE_MIDDLE_ID,
                _WHITESPACE_DETAIL_ID,
            ],
        )
        writer = _RecordingWriter()

        # Act
        save_roadmap(
            roadmap_input,
            writer=writer,
            id_generator=id_generator,
        )

        # Assert
        assert len(writer.calls) == 1
        roadmap_id, saved_topic, saved_items = writer.calls[0]
        assert roadmap_id == _WHITESPACE_ROADMAP_ID
        assert saved_topic == "  TypeScript 入門  "
        assert [item.title for item in saved_items] == [
            "  基礎  ",
            "  型  ",
            "  string  ",
        ]
        assert saved_items[2].description == ""
        assert [item.created_at for item in saved_items] == [
            "2026-05-21T12:00:00+09:00",
            "2026-05-21T12:00:00+09:00",
            "2026-05-21T12:00:00+09:00",
        ]
        assert [item.updated_at for item in saved_items] == [
            "2026-05-21T12:00:00+09:00",
            "2026-05-21T12:00:00+09:00",
            "2026-05-21T12:00:00+09:00",
        ]

    def test_tc_12_accepts_major_with_empty_children(self) -> None:
        # Arrange
        roadmap_input = _make_input(
            topic="Rust",
            created_at="2026-05-21T12:30:00+09:00",
            items=[
                _major(
                    title="所有権",
                    description="借用とムーブの前提",
                    children=[],
                ),
            ],
        )
        id_generator = _SequenceIdGenerator(
            [_MAJOR_ONLY_ROADMAP_ID, _MAJOR_ONLY_ID],
        )
        writer = _RecordingWriter()

        # Act
        result = save_roadmap(
            roadmap_input,
            writer=writer,
            id_generator=id_generator,
        )

        # Assert
        assert result == RoadmapSaveResult(
            roadmap_id=_MAJOR_ONLY_ROADMAP_ID,
            saved_count=1,
        )
        assert writer.calls == [
            (
                _MAJOR_ONLY_ROADMAP_ID,
                "Rust",
                [
                    FlatRoadmapItem(
                        id=_MAJOR_ONLY_ID,
                        roadmap_id=_MAJOR_ONLY_ROADMAP_ID,
                        parent_id=None,
                        level="major",
                        title="所有権",
                        description="借用とムーブの前提",
                        order=0,
                        score=0,
                        created_at="2026-05-21T12:30:00+09:00",
                        updated_at="2026-05-21T12:30:00+09:00",
                    ),
                ],
            ),
        ]

    def test_tc_13_accepts_middle_with_empty_children(self) -> None:
        # Arrange
        roadmap_input = _make_input(
            topic="Rust",
            created_at="2026-05-21T12:45:00+09:00",
            items=[
                _major(
                    title="所有権",
                    description="借用とムーブの前提",
                    children=[
                        _middle(
                            title="借用",
                            description="参照の基本",
                            children=[],
                        ),
                    ],
                ),
            ],
        )
        id_generator = _SequenceIdGenerator(
            [
                _MIDDLE_ONLY_ROADMAP_ID,
                _MIDDLE_ONLY_MAJOR_ID,
                _MIDDLE_ONLY_MIDDLE_ID,
            ],
        )
        writer = _RecordingWriter()

        # Act
        result = save_roadmap(
            roadmap_input,
            writer=writer,
            id_generator=id_generator,
        )

        # Assert
        assert result == RoadmapSaveResult(
            roadmap_id=_MIDDLE_ONLY_ROADMAP_ID,
            saved_count=2,
        )
        assert writer.calls == [
            (
                _MIDDLE_ONLY_ROADMAP_ID,
                "Rust",
                [
                    FlatRoadmapItem(
                        id=_MIDDLE_ONLY_MAJOR_ID,
                        roadmap_id=_MIDDLE_ONLY_ROADMAP_ID,
                        parent_id=None,
                        level="major",
                        title="所有権",
                        description="借用とムーブの前提",
                        order=0,
                        score=0,
                        created_at="2026-05-21T12:45:00+09:00",
                        updated_at="2026-05-21T12:45:00+09:00",
                    ),
                    FlatRoadmapItem(
                        id=_MIDDLE_ONLY_MIDDLE_ID,
                        roadmap_id=_MIDDLE_ONLY_ROADMAP_ID,
                        parent_id=_MIDDLE_ONLY_MAJOR_ID,
                        level="middle",
                        title="借用",
                        description="参照の基本",
                        order=0,
                        score=0,
                        created_at="2026-05-21T12:45:00+09:00",
                        updated_at="2026-05-21T12:45:00+09:00",
                    ),
                ],
            ),
        ]

    @pytest.mark.parametrize("topic", ["", "   "])
    def test_tc_20_rejects_blank_topic(self, topic: str) -> None:
        # Arrange
        roadmap_input = _make_minimal_valid_input(topic=topic)

        # Act / Assert
        assert _assert_input_error(roadmap_input) == (
            f"topic must be non-blank: got {topic!r}"
        )

    @pytest.mark.parametrize(
        ("major_title", "middle_title", "detail_title", "expected_path", "value"),
        [
            ("", "文法", "変数", "items[0]", ""),
            ("  ", "文法", "変数", "items[0]", "  "),
            ("基礎", "", "変数", "items[0].children[0]", ""),
            ("基礎", "  ", "変数", "items[0].children[0]", "  "),
            ("基礎", "文法", "", "items[0].children[0].children[0]", ""),
            ("基礎", "文法", "  ", "items[0].children[0].children[0]", "  "),
        ],
    )
    def test_tc_21_rejects_blank_titles_at_any_level(
        self,
        major_title: str,
        middle_title: str,
        detail_title: str,
        expected_path: str,
        value: str,
    ) -> None:
        # Arrange
        roadmap_input = _make_minimal_valid_input(
            major_title=major_title,
            middle_title=middle_title,
            detail_title=detail_title,
        )

        # Act / Assert
        assert _assert_input_error(roadmap_input) == (
            f"title must be non-blank at {expected_path}: got {value!r}"
        )

    @pytest.mark.parametrize(
        ("created_at", "expected_message"),
        [
            (
                "2026-05-21T10:00:00",
                "created_at must include a UTC offset: got '2026-05-21T10:00:00'",
            ),
            (
                "not-a-datetime",
                "created_at must be a valid ISO 8601 string with UTC offset: "
                "got 'not-a-datetime'",
            ),
        ],
    )
    def test_tc_22_requires_iso8601_timestamp_with_offset(
        self,
        created_at: str,
        expected_message: str,
    ) -> None:
        # Arrange
        roadmap_input = _make_minimal_valid_input(created_at=created_at)

        # Act / Assert
        assert _assert_input_error(roadmap_input) == expected_message

    @pytest.mark.parametrize("root_level", ["middle", "detail"])
    def test_tc_23_rejects_non_major_root_level(
        self,
        root_level: Literal["middle", "detail"],
    ) -> None:
        # Arrange
        invalid_root = RoadmapItemInput(
            title="不正なルート",
            description="root level mismatch",
            level=root_level,
            children=[],
        )
        roadmap_input = _make_input(items=[invalid_root])

        # Act / Assert
        assert _assert_input_error(roadmap_input) == (
            "level relationship is invalid at items[0]: "
            f"expected 'major', got {root_level!r}"
        )

    @pytest.mark.parametrize(
        ("items", "expected_message"),
        [
            (
                [
                    _major(
                        title="基礎",
                        children=[
                            _detail(title="detail skip middle"),
                        ],
                    ),
                ],
                "level relationship is invalid at items[0].children[0]: "
                "expected 'middle', got 'detail'",
            ),
            (
                [
                    _major(
                        title="基礎",
                        children=[
                            _middle(
                                title="中間",
                                children=[
                                    _major(title="major under middle"),
                                ],
                            ),
                        ],
                    ),
                ],
                "level relationship is invalid at "
                "items[0].children[0].children[0]: "
                "expected 'detail', got 'major'",
            ),
        ],
        ids=["detail_under_major", "major_under_middle"],
    )
    def test_tc_24_rejects_invalid_parent_child_level_relationship(
        self,
        items: list[RoadmapItemInput],
        expected_message: str,
    ) -> None:
        # Arrange
        roadmap_input = _make_input(items=items)

        # Act / Assert
        assert _assert_input_error(roadmap_input) == expected_message

    def test_tc_25_rejects_detail_with_non_empty_children(self) -> None:
        # Arrange
        roadmap_input = _make_input(
            items=[
                _major(
                    children=[
                        _middle(
                            children=[
                                _detail(
                                    title="再帰 detail",
                                    children=[
                                        _detail(title="不正な子"),
                                    ],
                                ),
                            ],
                        ),
                    ],
                ),
            ],
        )

        # Act / Assert
        assert _assert_input_error(roadmap_input) == (
            "children must be empty for 'detail' items at "
            "items[0].children[0].children[0]: got 1 child(ren)"
        )

    def test_tc_30_logs_success_and_calls_dependencies_expected_times(self) -> None:
        # Arrange
        roadmap_input = _make_minimal_valid_input()
        id_generator = _SequenceIdGenerator(
            [_MIN_ROADMAP_ID, _MIN_MAJOR_ID, _MIN_MIDDLE_ID, _MIN_DETAIL_ID],
        )
        writer = _RecordingWriter()

        # Act
        with capture_logs() as log_output:
            result = save_roadmap(
                roadmap_input,
                writer=writer,
                id_generator=id_generator,
            )

        # Assert
        assert result == RoadmapSaveResult(
            roadmap_id=_MIN_ROADMAP_ID,
            saved_count=3,
        )
        assert id_generator.calls == 4
        assert len(writer.calls) == 1
        _assert_single_log_event_includes(
            log_output,
            "roadmap_persisted",
            {
                "roadmap_id": "12121212-1212-1212-1212-121212121212",
                "topic": "Go",
                "saved_count": 3,
            },
        )
        _assert_no_log_event(log_output, "roadmap_persistence_failed")

    def test_tc_31_wraps_writer_errors_and_logs_failure(self) -> None:
        # Arrange
        roadmap_input = _make_minimal_valid_input()
        original_error = RuntimeError("insert failed")
        id_generator = _SequenceIdGenerator(
            [_MIN_ROADMAP_ID, _MIN_MAJOR_ID, _MIN_MIDDLE_ID, _MIN_DETAIL_ID],
        )
        writer = _RecordingWriter(error=original_error)

        # Act
        with (
            capture_logs() as log_output,
            pytest.raises(
                RoadmapPersistenceWriteError,
            ) as exc_info,
        ):
            save_roadmap(
                roadmap_input,
                writer=writer,
                id_generator=id_generator,
            )

        # Assert
        assert exc_info.value.__cause__ is original_error
        assert str(exc_info.value) == (
            "roadmap persistence failed: topic='Go', item_count=3"
        )
        assert id_generator.calls == 4
        assert len(writer.calls) == 1
        _assert_single_log_event_includes(
            log_output,
            "roadmap_persistence_failed",
            {
                "topic": "Go",
                "error_type": "RuntimeError",
            },
        )
        _assert_no_log_event(log_output, "roadmap_persisted")
