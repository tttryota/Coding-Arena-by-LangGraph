from __future__ import annotations

import inspect
from dataclasses import fields, is_dataclass
from uuid import UUID

import pytest
from backend.roadmap.infrastructure.roadmap_item_crud import (  # type: ignore[import-not-found]
    add_roadmap_item,
    delete_roadmap_item,
    move_roadmap_item,
)

from roadmap.domain.roadmap_item_crud_types import (
    RoadmapItemAddInput,
    RoadmapItemAddResult,
    RoadmapItemCrudInputError,
    RoadmapItemCrudItem,
    RoadmapItemCrudNotFoundError,
    RoadmapItemCrudRoadmapRecord,
    RoadmapItemCrudStore,
    RoadmapItemCrudStoreError,
    RoadmapItemDeleteInput,
    RoadmapItemDeleteResult,
    RoadmapItemIdGenerator,
    RoadmapItemMoveInput,
    RoadmapItemMoveResult,
)

_ROADMAP_ID = UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")
_FOREIGN_ROADMAP_ID = UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb")


class _RecordingStore:
    def __init__(
        self,
        *,
        roadmap: RoadmapItemCrudRoadmapRecord | None = None,
        items_by_id: dict[UUID, RoadmapItemCrudItem | None] | None = None,
        find_roadmap_error: Exception | None = None,
        find_item_errors: dict[UUID, Exception] | None = None,
        replace_error: Exception | None = None,
    ) -> None:
        self._roadmap = roadmap
        self._items_by_id = dict(items_by_id or {})
        self._find_roadmap_error = find_roadmap_error
        self._find_item_errors = dict(find_item_errors or {})
        self._replace_error = replace_error
        self.find_roadmap_calls: list[UUID] = []
        self.find_item_calls: list[UUID] = []
        self.replace_items_calls: list[tuple[UUID, list[RoadmapItemCrudItem]]] = []

    def find_roadmap(self, roadmap_id: UUID) -> RoadmapItemCrudRoadmapRecord | None:
        self.find_roadmap_calls.append(roadmap_id)
        if self._find_roadmap_error is not None:
            raise self._find_roadmap_error
        return self._roadmap

    def find_item(self, item_id: UUID) -> RoadmapItemCrudItem | None:
        self.find_item_calls.append(item_id)
        if item_id in self._find_item_errors:
            raise self._find_item_errors[item_id]
        return self._items_by_id.get(item_id)

    def replace_items(self, roadmap_id: UUID, items: list[RoadmapItemCrudItem]) -> None:
        self.replace_items_calls.append((roadmap_id, list(items)))
        if self._replace_error is not None:
            raise self._replace_error


class _RecordingIdGenerator:
    def __init__(
        self,
        *,
        generated_ids: list[UUID] | None = None,
        error: Exception | None = None,
    ) -> None:
        self._generated_ids = list(generated_ids or [])
        self._error = error
        self.calls = 0

    def generate(self) -> UUID:
        self.calls += 1
        if self._error is not None:
            raise self._error
        assert self._generated_ids
        return self._generated_ids.pop(0)


def _item(
    *,
    item_id: str,
    roadmap_id: UUID = _ROADMAP_ID,
    parent_id: str | None,
    level: str,
    title: str,
    description: str,
    order: int,
    score: int,
) -> RoadmapItemCrudItem:
    return RoadmapItemCrudItem(
        id=UUID(item_id),
        roadmap_id=roadmap_id,
        parent_id=None if parent_id is None else UUID(parent_id),
        level=level,
        title=title,
        description=description,
        order=order,
        score=score,
    )


def _record(items: list[RoadmapItemCrudItem]) -> RoadmapItemCrudRoadmapRecord:
    return RoadmapItemCrudRoadmapRecord(roadmap_id=_ROADMAP_ID, items=list(items))


def _assert_replace_call(
    store: _RecordingStore,
    expected_items: list[RoadmapItemCrudItem],
) -> None:
    assert store.replace_items_calls == [(_ROADMAP_ID, expected_items)]


def _assert_frozen_dataclass(cls: type[object]) -> None:
    assert is_dataclass(cls)
    assert cls.__dataclass_params__.frozen is True


def _add_validation_snapshot() -> RoadmapItemCrudRoadmapRecord:
    return _record(
        [
            _item(
                item_id="11111111-1111-1111-1111-111111111111",
                parent_id=None,
                level="major",
                title="基礎",
                description="基本概念",
                order=0,
                score=0,
            ),
            _item(
                item_id="aaaa1111-1111-1111-1111-111111111111",
                parent_id="11111111-1111-1111-1111-111111111111",
                level="middle",
                title="文法",
                description="文法基礎",
                order=0,
                score=0,
            ),
            _item(
                item_id="bbbb1111-1111-1111-1111-111111111111",
                parent_id="aaaa1111-1111-1111-1111-111111111111",
                level="detail",
                title="変数",
                description="変数宣言",
                order=0,
                score=1,
            ),
            _item(
                item_id="cccc1111-1111-1111-1111-111111111111",
                parent_id="11111111-1111-1111-1111-111111111111",
                level="middle",
                title="型",
                description="型の基本",
                order=1,
                score=0,
            ),
        ],
    )


def _move_validation_snapshot() -> RoadmapItemCrudRoadmapRecord:
    return _record(
        [
            _item(
                item_id="11111111-1111-1111-1111-111111111111",
                parent_id=None,
                level="major",
                title="基礎",
                description="基本概念",
                order=0,
                score=0,
            ),
            _item(
                item_id="aaaa1111-1111-1111-1111-111111111111",
                parent_id="11111111-1111-1111-1111-111111111111",
                level="middle",
                title="文法",
                description="文法基礎",
                order=0,
                score=0,
            ),
            _item(
                item_id="cccc1111-1111-1111-1111-111111111111",
                parent_id="aaaa1111-1111-1111-1111-111111111111",
                level="detail",
                title="変数",
                description="変数宣言",
                order=0,
                score=1,
            ),
            _item(
                item_id="bbbb1111-1111-1111-1111-111111111111",
                parent_id="11111111-1111-1111-1111-111111111111",
                level="middle",
                title="型",
                description="型の基本",
                order=1,
                score=0,
            ),
            _item(
                item_id="dddd1111-1111-1111-1111-111111111111",
                parent_id="bbbb1111-1111-1111-1111-111111111111",
                level="detail",
                title="string",
                description="文字列型",
                order=0,
                score=2,
            ),
            _item(
                item_id="eeee1111-1111-1111-1111-111111111111",
                parent_id="bbbb1111-1111-1111-1111-111111111111",
                level="detail",
                title="number",
                description="数値型",
                order=1,
                score=3,
            ),
            _item(
                item_id="22222222-2222-2222-2222-222222222222",
                parent_id=None,
                level="major",
                title="応用",
                description="応用技術",
                order=1,
                score=0,
            ),
            _item(
                item_id="ffff1111-1111-1111-1111-111111111111",
                parent_id="22222222-2222-2222-2222-222222222222",
                level="middle",
                title="非同期",
                description="asyncio",
                order=0,
                score=0,
            ),
        ],
    )


def _delete_validation_snapshot() -> RoadmapItemCrudRoadmapRecord:
    return _record(
        [
            _item(
                item_id="11111111-1111-1111-1111-111111111111",
                parent_id=None,
                level="major",
                title="基礎",
                description="基本概念",
                order=0,
                score=0,
            ),
        ],
    )


def _snapshot_missing_message(item_id: str) -> str:
    return (
        "item must exist in roadmap snapshot: "
        f"roadmap_id={_ROADMAP_ID}, item_id={UUID(item_id)}"
    )


def _orphan_snapshot() -> RoadmapItemCrudRoadmapRecord:
    return _record(
        [
            _item(
                item_id="11111111-1111-1111-1111-111111111111",
                parent_id=None,
                level="major",
                title="基礎",
                description="基本概念",
                order=0,
                score=0,
            ),
            _item(
                item_id="22222222-2222-2222-2222-222222222222",
                parent_id="99999999-9999-9999-9999-999999999999",
                level="middle",
                title="孤立",
                description="orphan",
                order=0,
                score=0,
            ),
            _item(
                item_id="33333333-3333-3333-3333-333333333333",
                parent_id=None,
                level="major",
                title="応用",
                description="別ルート",
                order=1,
                score=0,
            ),
        ],
    )


def test_tc_01_public_api_and_types_exist_in_target_modules() -> None:
    add_signature = inspect.signature(add_roadmap_item)
    move_signature = inspect.signature(move_roadmap_item)
    delete_signature = inspect.signature(delete_roadmap_item)

    assert (
        add_roadmap_item.__module__
        == "backend.roadmap.infrastructure.roadmap_item_crud"
    )
    assert (
        move_roadmap_item.__module__
        == "backend.roadmap.infrastructure.roadmap_item_crud"
    )
    assert (
        delete_roadmap_item.__module__
        == "backend.roadmap.infrastructure.roadmap_item_crud"
    )

    assert list(add_signature.parameters) == ["add_input", "store", "id_generator"]
    assert (
        add_signature.parameters["add_input"].kind
        is inspect.Parameter.POSITIONAL_OR_KEYWORD
    )
    assert add_signature.parameters["store"].kind is inspect.Parameter.KEYWORD_ONLY
    assert (
        add_signature.parameters["id_generator"].kind is inspect.Parameter.KEYWORD_ONLY
    )

    assert list(move_signature.parameters) == ["move_input", "store"]
    assert (
        move_signature.parameters["move_input"].kind
        is inspect.Parameter.POSITIONAL_OR_KEYWORD
    )
    assert move_signature.parameters["store"].kind is inspect.Parameter.KEYWORD_ONLY

    assert list(delete_signature.parameters) == ["delete_input", "store"]
    assert (
        delete_signature.parameters["delete_input"].kind
        is inspect.Parameter.POSITIONAL_OR_KEYWORD
    )
    assert delete_signature.parameters["store"].kind is inspect.Parameter.KEYWORD_ONLY
    assert "confirmed" not in delete_signature.parameters

    _assert_frozen_dataclass(RoadmapItemAddInput)
    _assert_frozen_dataclass(RoadmapItemMoveInput)
    _assert_frozen_dataclass(RoadmapItemDeleteInput)

    assert RoadmapItemAddInput.__module__ == (
        "backend.roadmap.infrastructure.roadmap_item_crud_types"
    )
    assert RoadmapItemMoveInput.__module__ == (
        "backend.roadmap.infrastructure.roadmap_item_crud_types"
    )
    assert RoadmapItemDeleteInput.__module__ == (
        "backend.roadmap.infrastructure.roadmap_item_crud_types"
    )
    assert RoadmapItemCrudItem.__module__ == (
        "backend.roadmap.infrastructure.roadmap_item_crud_types"
    )
    assert RoadmapItemCrudRoadmapRecord.__module__ == (
        "backend.roadmap.infrastructure.roadmap_item_crud_types"
    )
    assert RoadmapItemAddResult.__module__ == (
        "backend.roadmap.infrastructure.roadmap_item_crud_types"
    )
    assert RoadmapItemMoveResult.__module__ == (
        "backend.roadmap.infrastructure.roadmap_item_crud_types"
    )
    assert RoadmapItemDeleteResult.__module__ == (
        "backend.roadmap.infrastructure.roadmap_item_crud_types"
    )

    assert [field.name for field in fields(RoadmapItemAddInput)] == [
        "roadmap_id",
        "parent_id",
        "title",
        "description",
        "order",
    ]
    assert [field.name for field in fields(RoadmapItemMoveInput)] == [
        "roadmap_id",
        "item_id",
        "target_parent_id",
        "target_order",
    ]
    assert [field.name for field in fields(RoadmapItemDeleteInput)] == [
        "roadmap_id",
        "item_id",
    ]
    assert [field.name for field in fields(RoadmapItemCrudItem)] == [
        "id",
        "roadmap_id",
        "parent_id",
        "level",
        "title",
        "description",
        "order",
        "score",
    ]
    assert [field.name for field in fields(RoadmapItemCrudRoadmapRecord)] == [
        "roadmap_id",
        "items",
    ]
    assert [field.name for field in fields(RoadmapItemAddResult)] == ["created_item"]
    assert [field.name for field in fields(RoadmapItemMoveResult)] == ["moved_item"]
    assert [field.name for field in fields(RoadmapItemDeleteResult)] == [
        "deleted_item_ids",
        "deleted_count",
    ]

    assert RoadmapItemCrudStore.__module__ == (
        "backend.roadmap.infrastructure.roadmap_item_crud_types"
    )
    assert RoadmapItemIdGenerator.__module__ == (
        "backend.roadmap.infrastructure.roadmap_item_crud_types"
    )
    assert RoadmapItemCrudInputError.__module__ == (
        "backend.roadmap.infrastructure.roadmap_item_crud_types"
    )
    assert RoadmapItemCrudNotFoundError.__module__ == (
        "backend.roadmap.infrastructure.roadmap_item_crud_types"
    )
    assert RoadmapItemCrudStoreError.__module__ == (
        "backend.roadmap.infrastructure.roadmap_item_crud_types"
    )

    assert getattr(RoadmapItemCrudStore, "_is_protocol", False) is True
    assert getattr(RoadmapItemIdGenerator, "_is_protocol", False) is True
    assert list(inspect.signature(RoadmapItemCrudStore.find_roadmap).parameters) == [
        "self",
        "roadmap_id",
    ]
    assert list(inspect.signature(RoadmapItemCrudStore.find_item).parameters) == [
        "self",
        "item_id",
    ]
    assert list(inspect.signature(RoadmapItemCrudStore.replace_items).parameters) == [
        "self",
        "roadmap_id",
        "items",
    ]
    assert list(inspect.signature(RoadmapItemIdGenerator.generate).parameters) == [
        "self",
    ]

    assert issubclass(RoadmapItemCrudInputError, Exception)
    assert issubclass(RoadmapItemCrudNotFoundError, Exception)
    assert issubclass(RoadmapItemCrudStoreError, Exception)


def test_tc_02_adds_root_major_and_shifts_following_siblings() -> None:
    roadmap = _record(
        [
            _item(
                item_id="11111111-1111-1111-1111-111111111111",
                parent_id=None,
                level="major",
                title="基礎",
                description="基本概念",
                order=0,
                score=0,
            ),
            _item(
                item_id="22222222-2222-2222-2222-222222222222",
                parent_id=None,
                level="major",
                title="応用",
                description="応用技術",
                order=1,
                score=0,
            ),
        ],
    )
    store = _RecordingStore(roadmap=roadmap)
    id_generator = _RecordingIdGenerator(
        generated_ids=[UUID("33333333-3333-3333-3333-333333333333")],
    )

    result = add_roadmap_item(
        RoadmapItemAddInput(
            roadmap_id=_ROADMAP_ID,
            parent_id=None,
            title="設計",
            description="設計原則とレビュー観点",
            order=1,
        ),
        store=store,
        id_generator=id_generator,
    )

    expected_created_item = _item(
        item_id="33333333-3333-3333-3333-333333333333",
        parent_id=None,
        level="major",
        title="設計",
        description="設計原則とレビュー観点",
        order=1,
        score=0,
    )
    expected_items = [
        _item(
            item_id="11111111-1111-1111-1111-111111111111",
            parent_id=None,
            level="major",
            title="基礎",
            description="基本概念",
            order=0,
            score=0,
        ),
        expected_created_item,
        _item(
            item_id="22222222-2222-2222-2222-222222222222",
            parent_id=None,
            level="major",
            title="応用",
            description="応用技術",
            order=2,
            score=0,
        ),
    ]

    assert result.created_item == expected_created_item
    assert store.find_roadmap_calls == [_ROADMAP_ID]
    assert store.find_item_calls == []
    assert id_generator.calls == 1
    _assert_replace_call(store, expected_items)


def test_tc_03_same_parent_move_removes_then_inserts_at_target_order() -> None:
    roadmap = _record(
        [
            _item(
                item_id="11111111-1111-1111-1111-111111111111",
                parent_id=None,
                level="major",
                title="基礎文法",
                description="Python 基礎",
                order=0,
                score=0,
            ),
            _item(
                item_id="aaaa1111-1111-1111-1111-111111111111",
                parent_id="11111111-1111-1111-1111-111111111111",
                level="middle",
                title="変数",
                description="代入と再代入",
                order=0,
                score=1,
            ),
            _item(
                item_id="bbbb2222-2222-2222-2222-222222222222",
                parent_id="11111111-1111-1111-1111-111111111111",
                level="middle",
                title="関数",
                description="引数と戻り値",
                order=1,
                score=2,
            ),
            _item(
                item_id="cccc3333-3333-3333-3333-333333333333",
                parent_id="11111111-1111-1111-1111-111111111111",
                level="middle",
                title="型推論",
                description="型ヒントの読み取り",
                order=2,
                score=3,
            ),
        ],
    )
    store = _RecordingStore(roadmap=roadmap)

    result = move_roadmap_item(
        RoadmapItemMoveInput(
            roadmap_id=_ROADMAP_ID,
            item_id=UUID("aaaa1111-1111-1111-1111-111111111111"),
            target_parent_id=UUID("11111111-1111-1111-1111-111111111111"),
            target_order=2,
        ),
        store=store,
    )

    expected_moved_item = _item(
        item_id="aaaa1111-1111-1111-1111-111111111111",
        parent_id="11111111-1111-1111-1111-111111111111",
        level="middle",
        title="変数",
        description="代入と再代入",
        order=2,
        score=1,
    )
    expected_items = [
        _item(
            item_id="11111111-1111-1111-1111-111111111111",
            parent_id=None,
            level="major",
            title="基礎文法",
            description="Python 基礎",
            order=0,
            score=0,
        ),
        _item(
            item_id="bbbb2222-2222-2222-2222-222222222222",
            parent_id="11111111-1111-1111-1111-111111111111",
            level="middle",
            title="関数",
            description="引数と戻り値",
            order=0,
            score=2,
        ),
        _item(
            item_id="cccc3333-3333-3333-3333-333333333333",
            parent_id="11111111-1111-1111-1111-111111111111",
            level="middle",
            title="型推論",
            description="型ヒントの読み取り",
            order=1,
            score=3,
        ),
        expected_moved_item,
    ]

    assert result.moved_item == expected_moved_item
    assert store.find_roadmap_calls == [_ROADMAP_ID]
    assert store.find_item_calls == []
    _assert_replace_call(store, expected_items)


def test_tc_04_delete_major_removes_subtree_in_preorder_and_compacts_root_orders() -> (
    None
):
    roadmap = _record(
        [
            _item(
                item_id="11111111-1111-1111-1111-111111111111",
                parent_id=None,
                level="major",
                title="基礎",
                description="基本概念",
                order=0,
                score=0,
            ),
            _item(
                item_id="aaaa1111-1111-1111-1111-111111111111",
                parent_id="11111111-1111-1111-1111-111111111111",
                level="middle",
                title="文法",
                description="文法基礎",
                order=0,
                score=0,
            ),
            _item(
                item_id="bbbb1111-1111-1111-1111-111111111111",
                parent_id="aaaa1111-1111-1111-1111-111111111111",
                level="detail",
                title="変数",
                description="変数宣言",
                order=0,
                score=1,
            ),
            _item(
                item_id="22222222-2222-2222-2222-222222222222",
                parent_id=None,
                level="major",
                title="応用",
                description="応用技術",
                order=1,
                score=0,
            ),
            _item(
                item_id="44444444-4444-4444-4444-444444444444",
                parent_id="22222222-2222-2222-2222-222222222222",
                level="middle",
                title="非同期",
                description="asyncio",
                order=0,
                score=0,
            ),
            _item(
                item_id="55555555-5555-5555-5555-555555555555",
                parent_id="44444444-4444-4444-4444-444444444444",
                level="detail",
                title="await",
                description="イベントループ",
                order=0,
                score=2,
            ),
            _item(
                item_id="33333333-3333-3333-3333-333333333333",
                parent_id=None,
                level="major",
                title="実践",
                description="ハンズオン",
                order=2,
                score=0,
            ),
            _item(
                item_id="cccc3333-3333-3333-3333-333333333333",
                parent_id="33333333-3333-3333-3333-333333333333",
                level="middle",
                title="演習",
                description="実践課題",
                order=0,
                score=0,
            ),
        ],
    )
    store = _RecordingStore(roadmap=roadmap)

    result = delete_roadmap_item(
        RoadmapItemDeleteInput(
            roadmap_id=_ROADMAP_ID,
            item_id=UUID("22222222-2222-2222-2222-222222222222"),
        ),
        store=store,
    )

    expected_items = [
        _item(
            item_id="11111111-1111-1111-1111-111111111111",
            parent_id=None,
            level="major",
            title="基礎",
            description="基本概念",
            order=0,
            score=0,
        ),
        _item(
            item_id="aaaa1111-1111-1111-1111-111111111111",
            parent_id="11111111-1111-1111-1111-111111111111",
            level="middle",
            title="文法",
            description="文法基礎",
            order=0,
            score=0,
        ),
        _item(
            item_id="bbbb1111-1111-1111-1111-111111111111",
            parent_id="aaaa1111-1111-1111-1111-111111111111",
            level="detail",
            title="変数",
            description="変数宣言",
            order=0,
            score=1,
        ),
        _item(
            item_id="33333333-3333-3333-3333-333333333333",
            parent_id=None,
            level="major",
            title="実践",
            description="ハンズオン",
            order=1,
            score=0,
        ),
        _item(
            item_id="cccc3333-3333-3333-3333-333333333333",
            parent_id="33333333-3333-3333-3333-333333333333",
            level="middle",
            title="演習",
            description="実践課題",
            order=0,
            score=0,
        ),
    ]

    assert result.deleted_item_ids == (
        UUID("22222222-2222-2222-2222-222222222222"),
        UUID("44444444-4444-4444-4444-444444444444"),
        UUID("55555555-5555-5555-5555-555555555555"),
    )
    assert result.deleted_count == 3
    assert store.find_roadmap_calls == [_ROADMAP_ID]
    assert store.find_item_calls == []
    _assert_replace_call(store, expected_items)


def test_tc_10_add_under_major_creates_middle_and_appends_at_end() -> None:
    roadmap = _record(
        [
            _item(
                item_id="11111111-1111-1111-1111-111111111111",
                parent_id=None,
                level="major",
                title="基礎",
                description="基本概念",
                order=0,
                score=0,
            ),
            _item(
                item_id="22222222-2222-2222-2222-222222222222",
                parent_id="11111111-1111-1111-1111-111111111111",
                level="middle",
                title="文法",
                description="文法基礎",
                order=0,
                score=0,
            ),
            _item(
                item_id="33333333-3333-3333-3333-333333333333",
                parent_id="11111111-1111-1111-1111-111111111111",
                level="middle",
                title="型",
                description="型の基本",
                order=1,
                score=0,
            ),
        ],
    )
    store = _RecordingStore(roadmap=roadmap)
    id_generator = _RecordingIdGenerator(
        generated_ids=[UUID("44444444-4444-4444-4444-444444444444")],
    )

    result = add_roadmap_item(
        RoadmapItemAddInput(
            roadmap_id=_ROADMAP_ID,
            parent_id=UUID("11111111-1111-1111-1111-111111111111"),
            title="  Generics  ",
            description="",
            order=None,
        ),
        store=store,
        id_generator=id_generator,
    )

    expected_created_item = _item(
        item_id="44444444-4444-4444-4444-444444444444",
        parent_id="11111111-1111-1111-1111-111111111111",
        level="middle",
        title="  Generics  ",
        description="",
        order=2,
        score=0,
    )
    expected_items = [
        _item(
            item_id="11111111-1111-1111-1111-111111111111",
            parent_id=None,
            level="major",
            title="基礎",
            description="基本概念",
            order=0,
            score=0,
        ),
        _item(
            item_id="22222222-2222-2222-2222-222222222222",
            parent_id="11111111-1111-1111-1111-111111111111",
            level="middle",
            title="文法",
            description="文法基礎",
            order=0,
            score=0,
        ),
        _item(
            item_id="33333333-3333-3333-3333-333333333333",
            parent_id="11111111-1111-1111-1111-111111111111",
            level="middle",
            title="型",
            description="型の基本",
            order=1,
            score=0,
        ),
        expected_created_item,
    ]

    assert result.created_item == expected_created_item
    assert store.find_roadmap_calls == [_ROADMAP_ID]
    assert store.find_item_calls == []
    assert id_generator.calls == 1
    _assert_replace_call(store, expected_items)


def test_tc_11_add_under_middle_creates_detail_and_shifts_existing_details() -> None:
    roadmap = _record(
        [
            _item(
                item_id="11111111-1111-1111-1111-111111111111",
                parent_id=None,
                level="major",
                title="基礎",
                description="基本概念",
                order=0,
                score=0,
            ),
            _item(
                item_id="22222222-2222-2222-2222-222222222222",
                parent_id="11111111-1111-1111-1111-111111111111",
                level="middle",
                title="型",
                description="型の基本",
                order=0,
                score=0,
            ),
            _item(
                item_id="33333333-3333-3333-3333-333333333333",
                parent_id="22222222-2222-2222-2222-222222222222",
                level="detail",
                title="string",
                description="文字列型",
                order=0,
                score=1,
            ),
            _item(
                item_id="44444444-4444-4444-4444-444444444444",
                parent_id="22222222-2222-2222-2222-222222222222",
                level="detail",
                title="number",
                description="数値型",
                order=1,
                score=2,
            ),
        ],
    )
    store = _RecordingStore(roadmap=roadmap)
    id_generator = _RecordingIdGenerator(
        generated_ids=[UUID("55555555-5555-5555-5555-555555555555")],
    )

    result = add_roadmap_item(
        RoadmapItemAddInput(
            roadmap_id=_ROADMAP_ID,
            parent_id=UUID("22222222-2222-2222-2222-222222222222"),
            title="Union",
            description="   ",
            order=0,
        ),
        store=store,
        id_generator=id_generator,
    )

    expected_created_item = _item(
        item_id="55555555-5555-5555-5555-555555555555",
        parent_id="22222222-2222-2222-2222-222222222222",
        level="detail",
        title="Union",
        description="   ",
        order=0,
        score=0,
    )
    expected_items = [
        _item(
            item_id="11111111-1111-1111-1111-111111111111",
            parent_id=None,
            level="major",
            title="基礎",
            description="基本概念",
            order=0,
            score=0,
        ),
        _item(
            item_id="22222222-2222-2222-2222-222222222222",
            parent_id="11111111-1111-1111-1111-111111111111",
            level="middle",
            title="型",
            description="型の基本",
            order=0,
            score=0,
        ),
        expected_created_item,
        _item(
            item_id="33333333-3333-3333-3333-333333333333",
            parent_id="22222222-2222-2222-2222-222222222222",
            level="detail",
            title="string",
            description="文字列型",
            order=1,
            score=1,
        ),
        _item(
            item_id="44444444-4444-4444-4444-444444444444",
            parent_id="22222222-2222-2222-2222-222222222222",
            level="detail",
            title="number",
            description="数値型",
            order=2,
            score=2,
        ),
    ]

    assert result.created_item == expected_created_item
    assert store.find_roadmap_calls == [_ROADMAP_ID]
    assert store.find_item_calls == []
    assert id_generator.calls == 1
    _assert_replace_call(store, expected_items)


def test_tc_12_adds_root_major_at_end_when_parent_and_order_are_none() -> None:
    roadmap = _record(
        [
            _item(
                item_id="11111111-1111-1111-1111-111111111111",
                parent_id=None,
                level="major",
                title="基礎",
                description="基本概念",
                order=0,
                score=0,
            ),
            _item(
                item_id="22222222-2222-2222-2222-222222222222",
                parent_id=None,
                level="major",
                title="応用",
                description="応用技術",
                order=1,
                score=0,
            ),
        ],
    )
    store = _RecordingStore(roadmap=roadmap)
    id_generator = _RecordingIdGenerator(
        generated_ids=[UUID("33333333-3333-3333-3333-333333333333")],
    )

    result = add_roadmap_item(
        RoadmapItemAddInput(
            roadmap_id=_ROADMAP_ID,
            parent_id=None,
            title="実践",
            description="ハンズオン",
            order=None,
        ),
        store=store,
        id_generator=id_generator,
    )

    expected_created_item = _item(
        item_id="33333333-3333-3333-3333-333333333333",
        parent_id=None,
        level="major",
        title="実践",
        description="ハンズオン",
        order=2,
        score=0,
    )
    expected_items = [
        _item(
            item_id="11111111-1111-1111-1111-111111111111",
            parent_id=None,
            level="major",
            title="基礎",
            description="基本概念",
            order=0,
            score=0,
        ),
        _item(
            item_id="22222222-2222-2222-2222-222222222222",
            parent_id=None,
            level="major",
            title="応用",
            description="応用技術",
            order=1,
            score=0,
        ),
        expected_created_item,
    ]

    assert result.created_item == expected_created_item
    assert store.find_roadmap_calls == [_ROADMAP_ID]
    assert store.find_item_calls == []
    assert id_generator.calls == 1
    _assert_replace_call(store, expected_items)


def test_tc_13_move_detail_to_another_parent_reindexes_both_sibling_sets() -> None:
    roadmap = _record(
        [
            _item(
                item_id="11111111-1111-1111-1111-111111111111",
                parent_id=None,
                level="major",
                title="基礎",
                description="基本概念",
                order=0,
                score=0,
            ),
            _item(
                item_id="22222222-2222-2222-2222-222222222222",
                parent_id="11111111-1111-1111-1111-111111111111",
                level="middle",
                title="Python応用",
                description="実践Python",
                order=0,
                score=0,
            ),
            _item(
                item_id="dddd4444-4444-4444-4444-444444444444",
                parent_id="22222222-2222-2222-2222-222222222222",
                level="detail",
                title="デコレータ",
                description="関数を包む",
                order=0,
                score=1,
            ),
            _item(
                item_id="eeee5555-5555-5555-5555-555555555555",
                parent_id="22222222-2222-2222-2222-222222222222",
                level="detail",
                title="ユーティリティ型",
                description="型操作の定番",
                order=1,
                score=3,
            ),
            _item(
                item_id="33333333-3333-3333-3333-333333333333",
                parent_id="11111111-1111-1111-1111-111111111111",
                level="middle",
                title="型システム",
                description="静的型付け",
                order=1,
                score=0,
            ),
            _item(
                item_id="ffff6666-6666-6666-6666-666666666666",
                parent_id="33333333-3333-3333-3333-333333333333",
                level="detail",
                title="ジェネリクス",
                description="型パラメータ",
                order=0,
                score=2,
            ),
        ],
    )
    store = _RecordingStore(roadmap=roadmap)

    result = move_roadmap_item(
        RoadmapItemMoveInput(
            roadmap_id=_ROADMAP_ID,
            item_id=UUID("eeee5555-5555-5555-5555-555555555555"),
            target_parent_id=UUID("33333333-3333-3333-3333-333333333333"),
            target_order=1,
        ),
        store=store,
    )

    expected_moved_item = _item(
        item_id="eeee5555-5555-5555-5555-555555555555",
        parent_id="33333333-3333-3333-3333-333333333333",
        level="detail",
        title="ユーティリティ型",
        description="型操作の定番",
        order=1,
        score=3,
    )
    expected_items = [
        _item(
            item_id="11111111-1111-1111-1111-111111111111",
            parent_id=None,
            level="major",
            title="基礎",
            description="基本概念",
            order=0,
            score=0,
        ),
        _item(
            item_id="22222222-2222-2222-2222-222222222222",
            parent_id="11111111-1111-1111-1111-111111111111",
            level="middle",
            title="Python応用",
            description="実践Python",
            order=0,
            score=0,
        ),
        _item(
            item_id="dddd4444-4444-4444-4444-444444444444",
            parent_id="22222222-2222-2222-2222-222222222222",
            level="detail",
            title="デコレータ",
            description="関数を包む",
            order=0,
            score=1,
        ),
        _item(
            item_id="33333333-3333-3333-3333-333333333333",
            parent_id="11111111-1111-1111-1111-111111111111",
            level="middle",
            title="型システム",
            description="静的型付け",
            order=1,
            score=0,
        ),
        _item(
            item_id="ffff6666-6666-6666-6666-666666666666",
            parent_id="33333333-3333-3333-3333-333333333333",
            level="detail",
            title="ジェネリクス",
            description="型パラメータ",
            order=0,
            score=2,
        ),
        expected_moved_item,
    ]

    assert result.moved_item == expected_moved_item
    assert store.find_roadmap_calls == [_ROADMAP_ID]
    assert store.find_item_calls == []
    _assert_replace_call(store, expected_items)


def test_tc_14_move_root_major_allows_none_parent_and_reindexes_root_siblings() -> None:
    roadmap = _record(
        [
            _item(
                item_id="11111111-1111-1111-1111-111111111111",
                parent_id=None,
                level="major",
                title="基礎",
                description="基本概念",
                order=0,
                score=0,
            ),
            _item(
                item_id="22222222-2222-2222-2222-222222222222",
                parent_id=None,
                level="major",
                title="応用",
                description="応用技術",
                order=1,
                score=0,
            ),
            _item(
                item_id="33333333-3333-3333-3333-333333333333",
                parent_id=None,
                level="major",
                title="実践",
                description="ハンズオン",
                order=2,
                score=0,
            ),
        ],
    )
    store = _RecordingStore(roadmap=roadmap)

    result = move_roadmap_item(
        RoadmapItemMoveInput(
            roadmap_id=_ROADMAP_ID,
            item_id=UUID("11111111-1111-1111-1111-111111111111"),
            target_parent_id=None,
            target_order=2,
        ),
        store=store,
    )

    expected_moved_item = _item(
        item_id="11111111-1111-1111-1111-111111111111",
        parent_id=None,
        level="major",
        title="基礎",
        description="基本概念",
        order=2,
        score=0,
    )
    expected_items = [
        _item(
            item_id="22222222-2222-2222-2222-222222222222",
            parent_id=None,
            level="major",
            title="応用",
            description="応用技術",
            order=0,
            score=0,
        ),
        _item(
            item_id="33333333-3333-3333-3333-333333333333",
            parent_id=None,
            level="major",
            title="実践",
            description="ハンズオン",
            order=1,
            score=0,
        ),
        expected_moved_item,
    ]

    assert result.moved_item == expected_moved_item
    assert store.find_roadmap_calls == [_ROADMAP_ID]
    assert store.find_item_calls == []
    _assert_replace_call(store, expected_items)


def test_tc_15_delete_middle_removes_descendants_and_compacts_sibling_orders() -> None:
    roadmap = _record(
        [
            _item(
                item_id="11111111-1111-1111-1111-111111111111",
                parent_id=None,
                level="major",
                title="基礎",
                description="基本概念",
                order=0,
                score=0,
            ),
            _item(
                item_id="aaaa1111-1111-1111-1111-111111111111",
                parent_id="11111111-1111-1111-1111-111111111111",
                level="middle",
                title="文法",
                description="文法基礎",
                order=0,
                score=0,
            ),
            _item(
                item_id="bbbb1111-1111-1111-1111-111111111111",
                parent_id="11111111-1111-1111-1111-111111111111",
                level="middle",
                title="型",
                description="型の基本",
                order=1,
                score=0,
            ),
            _item(
                item_id="cccc1111-1111-1111-1111-111111111111",
                parent_id="bbbb1111-1111-1111-1111-111111111111",
                level="detail",
                title="string",
                description="文字列型",
                order=0,
                score=1,
            ),
            _item(
                item_id="dddd1111-1111-1111-1111-111111111111",
                parent_id="bbbb1111-1111-1111-1111-111111111111",
                level="detail",
                title="number",
                description="数値型",
                order=1,
                score=2,
            ),
            _item(
                item_id="eeee1111-1111-1111-1111-111111111111",
                parent_id="11111111-1111-1111-1111-111111111111",
                level="middle",
                title="実装",
                description="実装練習",
                order=2,
                score=0,
            ),
            _item(
                item_id="22222222-2222-2222-2222-222222222222",
                parent_id=None,
                level="major",
                title="応用",
                description="応用技術",
                order=1,
                score=0,
            ),
        ],
    )
    store = _RecordingStore(roadmap=roadmap)

    result = delete_roadmap_item(
        RoadmapItemDeleteInput(
            roadmap_id=_ROADMAP_ID,
            item_id=UUID("bbbb1111-1111-1111-1111-111111111111"),
        ),
        store=store,
    )

    expected_items = [
        _item(
            item_id="11111111-1111-1111-1111-111111111111",
            parent_id=None,
            level="major",
            title="基礎",
            description="基本概念",
            order=0,
            score=0,
        ),
        _item(
            item_id="aaaa1111-1111-1111-1111-111111111111",
            parent_id="11111111-1111-1111-1111-111111111111",
            level="middle",
            title="文法",
            description="文法基礎",
            order=0,
            score=0,
        ),
        _item(
            item_id="eeee1111-1111-1111-1111-111111111111",
            parent_id="11111111-1111-1111-1111-111111111111",
            level="middle",
            title="実装",
            description="実装練習",
            order=1,
            score=0,
        ),
        _item(
            item_id="22222222-2222-2222-2222-222222222222",
            parent_id=None,
            level="major",
            title="応用",
            description="応用技術",
            order=1,
            score=0,
        ),
    ]

    assert result.deleted_item_ids == (
        UUID("bbbb1111-1111-1111-1111-111111111111"),
        UUID("cccc1111-1111-1111-1111-111111111111"),
        UUID("dddd1111-1111-1111-1111-111111111111"),
    )
    assert result.deleted_count == 3
    assert store.find_roadmap_calls == [_ROADMAP_ID]
    assert store.find_item_calls == []
    _assert_replace_call(store, expected_items)


def test_tc_20_missing_roadmap_raises_not_found_for_add_move_and_delete() -> None:
    add_store = _RecordingStore(roadmap=None)
    add_id_generator = _RecordingIdGenerator(
        generated_ids=[UUID("99999999-9999-9999-9999-999999999999")],
    )

    with pytest.raises(RoadmapItemCrudNotFoundError):
        add_roadmap_item(
            RoadmapItemAddInput(
                roadmap_id=UUID("10101010-1010-1010-1010-101010101010"),
                parent_id=None,
                title="新規 major",
                description="desc",
                order=None,
            ),
            store=add_store,
            id_generator=add_id_generator,
        )

    assert add_store.find_roadmap_calls == [
        UUID("10101010-1010-1010-1010-101010101010"),
    ]
    assert add_store.find_item_calls == []
    assert add_store.replace_items_calls == []
    assert add_id_generator.calls == 0

    move_store = _RecordingStore(roadmap=None)

    with pytest.raises(RoadmapItemCrudNotFoundError):
        move_roadmap_item(
            RoadmapItemMoveInput(
                roadmap_id=UUID("20202020-2020-2020-2020-202020202020"),
                item_id=UUID("11111111-1111-1111-1111-111111111111"),
                target_parent_id=None,
                target_order=0,
            ),
            store=move_store,
        )

    assert move_store.find_roadmap_calls == [
        UUID("20202020-2020-2020-2020-202020202020"),
    ]
    assert move_store.find_item_calls == []
    assert move_store.replace_items_calls == []

    delete_store = _RecordingStore(roadmap=None)

    with pytest.raises(RoadmapItemCrudNotFoundError):
        delete_roadmap_item(
            RoadmapItemDeleteInput(
                roadmap_id=UUID("30303030-3030-3030-3030-303030303030"),
                item_id=UUID("11111111-1111-1111-1111-111111111111"),
            ),
            store=delete_store,
        )

    assert delete_store.find_roadmap_calls == [
        UUID("30303030-3030-3030-3030-303030303030"),
    ]
    assert delete_store.find_item_calls == []
    assert delete_store.replace_items_calls == []


def test_tc_21_add_distinguishes_invalid_input_from_reference_resolution() -> None:
    foreign_parent = _item(
        item_id="88888888-8888-8888-8888-888888888888",
        roadmap_id=_FOREIGN_ROADMAP_ID,
        parent_id=None,
        level="major",
        title="foreign",
        description="other roadmap",
        order=0,
        score=0,
    )
    cases = [
        {
            "add_input": RoadmapItemAddInput(
                roadmap_id=_ROADMAP_ID,
                parent_id=UUID("11111111-1111-1111-1111-111111111111"),
                title="",
                description="desc",
                order=0,
            ),
            "expected_exception": RoadmapItemCrudInputError,
            "items_by_id": {},
            "expected_find_item_calls": [],
        },
        {
            "add_input": RoadmapItemAddInput(
                roadmap_id=_ROADMAP_ID,
                parent_id=UUID("11111111-1111-1111-1111-111111111111"),
                title="   ",
                description="desc",
                order=0,
            ),
            "expected_exception": RoadmapItemCrudInputError,
            "items_by_id": {},
            "expected_find_item_calls": [],
        },
        {
            "add_input": RoadmapItemAddInput(
                roadmap_id=_ROADMAP_ID,
                parent_id=UUID("11111111-1111-1111-1111-111111111111"),
                title="新規 middle",
                description="desc",
                order=-1,
            ),
            "expected_exception": RoadmapItemCrudInputError,
            "items_by_id": {},
            "expected_find_item_calls": [],
        },
        {
            "add_input": RoadmapItemAddInput(
                roadmap_id=_ROADMAP_ID,
                parent_id=UUID("11111111-1111-1111-1111-111111111111"),
                title="新規 middle",
                description="desc",
                order=3,
            ),
            "expected_exception": RoadmapItemCrudInputError,
            "items_by_id": {},
            "expected_find_item_calls": [],
        },
        {
            "add_input": RoadmapItemAddInput(
                roadmap_id=_ROADMAP_ID,
                parent_id=UUID("bbbb1111-1111-1111-1111-111111111111"),
                title="detail の子",
                description="desc",
                order=0,
            ),
            "expected_exception": RoadmapItemCrudInputError,
            "items_by_id": {},
            "expected_find_item_calls": [],
        },
        {
            "add_input": RoadmapItemAddInput(
                roadmap_id=_ROADMAP_ID,
                parent_id=UUID("99999999-9999-9999-9999-999999999999"),
                title="lookup",
                description="desc",
                order=0,
            ),
            "expected_exception": RoadmapItemCrudNotFoundError,
            "items_by_id": {},
            "expected_find_item_calls": [UUID("99999999-9999-9999-9999-999999999999")],
        },
        {
            "add_input": RoadmapItemAddInput(
                roadmap_id=_ROADMAP_ID,
                parent_id=UUID("88888888-8888-8888-8888-888888888888"),
                title="lookup",
                description="desc",
                order=0,
            ),
            "expected_exception": RoadmapItemCrudInputError,
            "items_by_id": {
                UUID("88888888-8888-8888-8888-888888888888"): foreign_parent,
            },
            "expected_find_item_calls": [UUID("88888888-8888-8888-8888-888888888888")],
        },
    ]

    for case in cases:
        store = _RecordingStore(
            roadmap=_add_validation_snapshot(),
            items_by_id=case["items_by_id"],
        )
        id_generator = _RecordingIdGenerator(
            generated_ids=[UUID("77777777-7777-7777-7777-777777777777")],
        )

        with pytest.raises(case["expected_exception"]):
            add_roadmap_item(
                case["add_input"],
                store=store,
                id_generator=id_generator,
            )

        assert store.find_roadmap_calls == [_ROADMAP_ID]
        assert store.find_item_calls == case["expected_find_item_calls"]
        assert store.replace_items_calls == []
        assert id_generator.calls == 0


def test_tc_22_move_distinguishes_not_found_hierarchy_cycle_and_range_errors() -> None:
    foreign_item = _item(
        item_id="77777777-7777-7777-7777-777777777777",
        roadmap_id=_FOREIGN_ROADMAP_ID,
        parent_id=None,
        level="major",
        title="foreign item",
        description="other roadmap",
        order=0,
        score=0,
    )
    foreign_parent = _item(
        item_id="66666666-6666-6666-6666-666666666666",
        roadmap_id=_FOREIGN_ROADMAP_ID,
        parent_id=None,
        level="major",
        title="foreign parent",
        description="other roadmap",
        order=0,
        score=0,
    )
    cases = [
        {
            "move_input": RoadmapItemMoveInput(
                roadmap_id=_ROADMAP_ID,
                item_id=UUID("99999999-9999-9999-9999-999999999999"),
                target_parent_id=UUID("11111111-1111-1111-1111-111111111111"),
                target_order=0,
            ),
            "expected_exception": RoadmapItemCrudNotFoundError,
            "items_by_id": {},
            "expected_find_item_calls": [UUID("99999999-9999-9999-9999-999999999999")],
        },
        {
            "move_input": RoadmapItemMoveInput(
                roadmap_id=_ROADMAP_ID,
                item_id=UUID("aaaa1111-1111-1111-1111-111111111111"),
                target_parent_id=UUID("88888888-8888-8888-8888-888888888888"),
                target_order=0,
            ),
            "expected_exception": RoadmapItemCrudNotFoundError,
            "items_by_id": {},
            "expected_find_item_calls": [UUID("88888888-8888-8888-8888-888888888888")],
        },
        {
            "move_input": RoadmapItemMoveInput(
                roadmap_id=_ROADMAP_ID,
                item_id=UUID("77777777-7777-7777-7777-777777777777"),
                target_parent_id=UUID("11111111-1111-1111-1111-111111111111"),
                target_order=0,
            ),
            "expected_exception": RoadmapItemCrudInputError,
            "items_by_id": {UUID("77777777-7777-7777-7777-777777777777"): foreign_item},
            "expected_find_item_calls": [UUID("77777777-7777-7777-7777-777777777777")],
        },
        {
            "move_input": RoadmapItemMoveInput(
                roadmap_id=_ROADMAP_ID,
                item_id=UUID("aaaa1111-1111-1111-1111-111111111111"),
                target_parent_id=UUID("66666666-6666-6666-6666-666666666666"),
                target_order=0,
            ),
            "expected_exception": RoadmapItemCrudInputError,
            "items_by_id": {
                UUID("66666666-6666-6666-6666-666666666666"): foreign_parent,
            },
            "expected_find_item_calls": [UUID("66666666-6666-6666-6666-666666666666")],
        },
        {
            "move_input": RoadmapItemMoveInput(
                roadmap_id=_ROADMAP_ID,
                item_id=UUID("aaaa1111-1111-1111-1111-111111111111"),
                target_parent_id=UUID("cccc1111-1111-1111-1111-111111111111"),
                target_order=0,
            ),
            "expected_exception": RoadmapItemCrudInputError,
            "items_by_id": {},
            "expected_find_item_calls": [],
        },
        {
            "move_input": RoadmapItemMoveInput(
                roadmap_id=_ROADMAP_ID,
                item_id=UUID("aaaa1111-1111-1111-1111-111111111111"),
                target_parent_id=None,
                target_order=0,
            ),
            "expected_exception": RoadmapItemCrudInputError,
            "items_by_id": {},
            "expected_find_item_calls": [],
        },
        {
            "move_input": RoadmapItemMoveInput(
                roadmap_id=_ROADMAP_ID,
                item_id=UUID("11111111-1111-1111-1111-111111111111"),
                target_parent_id=UUID("22222222-2222-2222-2222-222222222222"),
                target_order=0,
            ),
            "expected_exception": RoadmapItemCrudInputError,
            "items_by_id": {},
            "expected_find_item_calls": [],
        },
        {
            "move_input": RoadmapItemMoveInput(
                roadmap_id=_ROADMAP_ID,
                item_id=UUID("cccc1111-1111-1111-1111-111111111111"),
                target_parent_id=UUID("11111111-1111-1111-1111-111111111111"),
                target_order=0,
            ),
            "expected_exception": RoadmapItemCrudInputError,
            "items_by_id": {},
            "expected_find_item_calls": [],
        },
        {
            "move_input": RoadmapItemMoveInput(
                roadmap_id=_ROADMAP_ID,
                item_id=UUID("aaaa1111-1111-1111-1111-111111111111"),
                target_parent_id=UUID("aaaa1111-1111-1111-1111-111111111111"),
                target_order=0,
            ),
            "expected_exception": RoadmapItemCrudInputError,
            "items_by_id": {},
            "expected_find_item_calls": [],
        },
        {
            "move_input": RoadmapItemMoveInput(
                roadmap_id=_ROADMAP_ID,
                item_id=UUID("11111111-1111-1111-1111-111111111111"),
                target_parent_id=UUID("bbbb1111-1111-1111-1111-111111111111"),
                target_order=0,
            ),
            "expected_exception": RoadmapItemCrudInputError,
            "items_by_id": {},
            "expected_find_item_calls": [],
        },
        {
            "move_input": RoadmapItemMoveInput(
                roadmap_id=_ROADMAP_ID,
                item_id=UUID("dddd1111-1111-1111-1111-111111111111"),
                target_parent_id=UUID("bbbb1111-1111-1111-1111-111111111111"),
                target_order=-1,
            ),
            "expected_exception": RoadmapItemCrudInputError,
            "items_by_id": {},
            "expected_find_item_calls": [],
        },
        {
            "move_input": RoadmapItemMoveInput(
                roadmap_id=_ROADMAP_ID,
                item_id=UUID("dddd1111-1111-1111-1111-111111111111"),
                target_parent_id=UUID("bbbb1111-1111-1111-1111-111111111111"),
                target_order=2,
            ),
            "expected_exception": RoadmapItemCrudInputError,
            "items_by_id": {},
            "expected_find_item_calls": [],
        },
    ]

    for case in cases:
        store = _RecordingStore(
            roadmap=_move_validation_snapshot(),
            items_by_id=case["items_by_id"],
        )

        with pytest.raises(case["expected_exception"]):
            move_roadmap_item(case["move_input"], store=store)

        assert store.find_roadmap_calls == [_ROADMAP_ID]
        assert store.find_item_calls == case["expected_find_item_calls"]
        assert store.replace_items_calls == []


def test_tc_23_delete_distinguishes_not_found_foreign_and_last_major_errors() -> None:
    foreign_item = _item(
        item_id="99999999-9999-9999-9999-999999999999",
        roadmap_id=_FOREIGN_ROADMAP_ID,
        parent_id=None,
        level="major",
        title="foreign",
        description="other roadmap",
        order=0,
        score=0,
    )

    missing_store = _RecordingStore(roadmap=_add_validation_snapshot())
    with pytest.raises(RoadmapItemCrudNotFoundError):
        delete_roadmap_item(
            RoadmapItemDeleteInput(
                roadmap_id=_ROADMAP_ID,
                item_id=UUID("88888888-8888-8888-8888-888888888888"),
            ),
            store=missing_store,
        )

    assert missing_store.find_roadmap_calls == [_ROADMAP_ID]
    assert missing_store.find_item_calls == [
        UUID("88888888-8888-8888-8888-888888888888"),
    ]
    assert missing_store.replace_items_calls == []

    foreign_store = _RecordingStore(
        roadmap=_add_validation_snapshot(),
        items_by_id={UUID("99999999-9999-9999-9999-999999999999"): foreign_item},
    )
    with pytest.raises(RoadmapItemCrudInputError):
        delete_roadmap_item(
            RoadmapItemDeleteInput(
                roadmap_id=_ROADMAP_ID,
                item_id=UUID("99999999-9999-9999-9999-999999999999"),
            ),
            store=foreign_store,
        )

    assert foreign_store.find_roadmap_calls == [_ROADMAP_ID]
    assert foreign_store.find_item_calls == [
        UUID("99999999-9999-9999-9999-999999999999"),
    ]
    assert foreign_store.replace_items_calls == []

    last_major_store = _RecordingStore(roadmap=_delete_validation_snapshot())
    with pytest.raises(RoadmapItemCrudInputError):
        delete_roadmap_item(
            RoadmapItemDeleteInput(
                roadmap_id=_ROADMAP_ID,
                item_id=UUID("11111111-1111-1111-1111-111111111111"),
            ),
            store=last_major_store,
        )

    assert last_major_store.find_roadmap_calls == [_ROADMAP_ID]
    assert last_major_store.find_item_calls == []
    assert last_major_store.replace_items_calls == []


def test_tc_24_snapshot_lookup_inconsistency_raises_store_error_across_entrypoints() -> None:
    missing_parent_id = UUID("88888888-8888-8888-8888-888888888888")
    add_store = _RecordingStore(
        roadmap=_delete_validation_snapshot(),
        items_by_id={
            missing_parent_id: _item(
                item_id="88888888-8888-8888-8888-888888888888",
                parent_id=None,
                level="major",
                title="ghost parent",
                description="snapshot missing",
                order=0,
                score=0,
            ),
        },
    )
    add_id_generator = _RecordingIdGenerator(
        generated_ids=[UUID("aaaaaaaa-1111-1111-1111-111111111111")],
    )

    with pytest.raises(RoadmapItemCrudStoreError) as exc_info:
        add_roadmap_item(
            RoadmapItemAddInput(
                roadmap_id=_ROADMAP_ID,
                parent_id=missing_parent_id,
                title="lookup parent",
                description="desc",
                order=0,
            ),
            store=add_store,
            id_generator=add_id_generator,
        )

    assert str(exc_info.value) == _snapshot_missing_message(
        "88888888-8888-8888-8888-888888888888",
    )
    assert add_store.find_roadmap_calls == [_ROADMAP_ID]
    assert add_store.find_item_calls == [missing_parent_id]
    assert add_store.replace_items_calls == []
    assert add_id_generator.calls == 0

    missing_move_item_id = UUID("77777777-7777-7777-7777-777777777777")
    move_store = _RecordingStore(
        roadmap=_record(
            [
                _item(
                    item_id="11111111-1111-1111-1111-111111111111",
                    parent_id=None,
                    level="major",
                    title="基礎",
                    description="基本概念",
                    order=0,
                    score=0,
                ),
                _item(
                    item_id="22222222-2222-2222-2222-222222222222",
                    parent_id=None,
                    level="major",
                    title="応用",
                    description="応用技術",
                    order=1,
                    score=0,
                ),
            ],
        ),
        items_by_id={
            missing_move_item_id: _item(
                item_id="77777777-7777-7777-7777-777777777777",
                parent_id=None,
                level="major",
                title="ghost item",
                description="snapshot missing",
                order=0,
                score=0,
            ),
        },
    )

    with pytest.raises(RoadmapItemCrudStoreError) as exc_info:
        move_roadmap_item(
            RoadmapItemMoveInput(
                roadmap_id=_ROADMAP_ID,
                item_id=missing_move_item_id,
                target_parent_id=None,
                target_order=1,
            ),
            store=move_store,
        )

    assert str(exc_info.value) == _snapshot_missing_message(
        "77777777-7777-7777-7777-777777777777",
    )
    assert move_store.find_roadmap_calls == [_ROADMAP_ID]
    assert move_store.find_item_calls == [missing_move_item_id]
    assert move_store.replace_items_calls == []

    missing_delete_item_id = UUID("66666666-6666-6666-6666-666666666666")
    delete_store = _RecordingStore(
        roadmap=_delete_validation_snapshot(),
        items_by_id={
            missing_delete_item_id: _item(
                item_id="66666666-6666-6666-6666-666666666666",
                parent_id=None,
                level="major",
                title="ghost delete",
                description="snapshot missing",
                order=0,
                score=0,
            ),
        },
    )

    with pytest.raises(RoadmapItemCrudStoreError) as exc_info:
        delete_roadmap_item(
            RoadmapItemDeleteInput(
                roadmap_id=_ROADMAP_ID,
                item_id=missing_delete_item_id,
            ),
            store=delete_store,
        )

    assert str(exc_info.value) == _snapshot_missing_message(
        "66666666-6666-6666-6666-666666666666",
    )
    assert delete_store.find_roadmap_calls == [_ROADMAP_ID]
    assert delete_store.find_item_calls == [missing_delete_item_id]
    assert delete_store.replace_items_calls == []


def test_tc_25_unreachable_snapshot_nodes_fail_closed_before_replace() -> None:
    add_store = _RecordingStore(roadmap=_orphan_snapshot())
    add_id_generator = _RecordingIdGenerator(
        generated_ids=[UUID("44444444-4444-4444-4444-444444444444")],
    )

    with pytest.raises(RoadmapItemCrudStoreError) as exc_info:
        add_roadmap_item(
            RoadmapItemAddInput(
                roadmap_id=_ROADMAP_ID,
                parent_id=None,
                title="新規 major",
                description="desc",
                order=None,
            ),
            store=add_store,
            id_generator=add_id_generator,
        )

    assert "roadmap snapshot must be fully connected from root" in str(exc_info.value)
    assert "22222222-2222-2222-2222-222222222222" in str(exc_info.value)
    assert add_store.find_roadmap_calls == [_ROADMAP_ID]
    assert add_store.find_item_calls == []
    assert add_store.replace_items_calls == []
    assert add_id_generator.calls == 1

    move_store = _RecordingStore(roadmap=_orphan_snapshot())
    with pytest.raises(RoadmapItemCrudStoreError) as exc_info:
        move_roadmap_item(
            RoadmapItemMoveInput(
                roadmap_id=_ROADMAP_ID,
                item_id=UUID("11111111-1111-1111-1111-111111111111"),
                target_parent_id=None,
                target_order=1,
            ),
            store=move_store,
        )

    assert "roadmap snapshot must be fully connected from root" in str(exc_info.value)
    assert "22222222-2222-2222-2222-222222222222" in str(exc_info.value)
    assert move_store.find_roadmap_calls == [_ROADMAP_ID]
    assert move_store.find_item_calls == []
    assert move_store.replace_items_calls == []

    delete_store = _RecordingStore(roadmap=_orphan_snapshot())
    with pytest.raises(RoadmapItemCrudStoreError) as exc_info:
        delete_roadmap_item(
            RoadmapItemDeleteInput(
                roadmap_id=_ROADMAP_ID,
                item_id=UUID("33333333-3333-3333-3333-333333333333"),
            ),
            store=delete_store,
        )

    assert "roadmap snapshot must be fully connected from root" in str(exc_info.value)
    assert "22222222-2222-2222-2222-222222222222" in str(exc_info.value)
    assert delete_store.find_roadmap_calls == [_ROADMAP_ID]
    assert delete_store.find_item_calls == []
    assert delete_store.replace_items_calls == []


def test_tc_30_add_wraps_id_generator_failure_and_skips_replace() -> None:
    store = _RecordingStore(roadmap=_add_validation_snapshot())
    error = RuntimeError("uuid failed")
    id_generator = _RecordingIdGenerator(error=error)

    with pytest.raises(RoadmapItemCrudStoreError) as exc_info:
        add_roadmap_item(
            RoadmapItemAddInput(
                roadmap_id=_ROADMAP_ID,
                parent_id=UUID("11111111-1111-1111-1111-111111111111"),
                title="新規 middle",
                description="desc",
                order=1,
            ),
            store=store,
            id_generator=id_generator,
        )

    assert exc_info.value.__cause__ is error
    assert store.find_roadmap_calls == [_ROADMAP_ID]
    assert store.find_item_calls == []
    assert store.replace_items_calls == []
    assert id_generator.calls == 1


def test_tc_31_wraps_find_roadmap_and_find_item_failures() -> None:
    find_roadmap_error = ConnectionError("lookup failed")

    add_find_roadmap_store = _RecordingStore(
        find_roadmap_error=find_roadmap_error,
    )
    add_find_roadmap_id_generator = _RecordingIdGenerator(
        generated_ids=[UUID("12121212-1212-1212-1212-121212121212")],
    )
    with pytest.raises(RoadmapItemCrudStoreError) as exc_info:
        add_roadmap_item(
            RoadmapItemAddInput(
                roadmap_id=_ROADMAP_ID,
                parent_id=None,
                title="新規 major",
                description="desc",
                order=None,
            ),
            store=add_find_roadmap_store,
            id_generator=add_find_roadmap_id_generator,
        )

    assert exc_info.value.__cause__ is find_roadmap_error
    assert add_find_roadmap_store.find_roadmap_calls == [_ROADMAP_ID]
    assert add_find_roadmap_store.find_item_calls == []
    assert add_find_roadmap_store.replace_items_calls == []
    assert add_find_roadmap_id_generator.calls == 0

    move_find_roadmap_store = _RecordingStore(
        find_roadmap_error=find_roadmap_error,
    )
    with pytest.raises(RoadmapItemCrudStoreError) as exc_info:
        move_roadmap_item(
            RoadmapItemMoveInput(
                roadmap_id=_ROADMAP_ID,
                item_id=UUID("11111111-1111-1111-1111-111111111111"),
                target_parent_id=None,
                target_order=0,
            ),
            store=move_find_roadmap_store,
        )

    assert exc_info.value.__cause__ is find_roadmap_error
    assert move_find_roadmap_store.find_roadmap_calls == [_ROADMAP_ID]
    assert move_find_roadmap_store.find_item_calls == []
    assert move_find_roadmap_store.replace_items_calls == []

    add_find_item_error = TimeoutError("parent lookup timed out")
    add_find_item_store = _RecordingStore(
        roadmap=_delete_validation_snapshot(),
        find_item_errors={
            UUID("99999999-9999-9999-9999-999999999999"): add_find_item_error,
        },
    )
    add_find_item_id_generator = _RecordingIdGenerator(
        generated_ids=[UUID("13131313-1313-1313-1313-131313131313")],
    )
    with pytest.raises(RoadmapItemCrudStoreError) as exc_info:
        add_roadmap_item(
            RoadmapItemAddInput(
                roadmap_id=_ROADMAP_ID,
                parent_id=UUID("99999999-9999-9999-9999-999999999999"),
                title="lookup",
                description="desc",
                order=0,
            ),
            store=add_find_item_store,
            id_generator=add_find_item_id_generator,
        )

    assert exc_info.value.__cause__ is add_find_item_error
    assert add_find_item_store.find_roadmap_calls == [_ROADMAP_ID]
    assert add_find_item_store.find_item_calls == [
        UUID("99999999-9999-9999-9999-999999999999"),
    ]
    assert add_find_item_store.replace_items_calls == []
    assert add_find_item_id_generator.calls == 0

    delete_find_item_error = TimeoutError("delete lookup timed out")
    delete_find_item_store = _RecordingStore(
        roadmap=_delete_validation_snapshot(),
        find_item_errors={
            UUID("88888888-8888-8888-8888-888888888888"): delete_find_item_error,
        },
    )
    with pytest.raises(RoadmapItemCrudStoreError) as exc_info:
        delete_roadmap_item(
            RoadmapItemDeleteInput(
                roadmap_id=_ROADMAP_ID,
                item_id=UUID("88888888-8888-8888-8888-888888888888"),
            ),
            store=delete_find_item_store,
        )

    assert exc_info.value.__cause__ is delete_find_item_error
    assert delete_find_item_store.find_roadmap_calls == [_ROADMAP_ID]
    assert delete_find_item_store.find_item_calls == [
        UUID("88888888-8888-8888-8888-888888888888"),
    ]
    assert delete_find_item_store.replace_items_calls == []


def test_tc_32_wraps_replace_items_failure_for_add_move_and_delete() -> None:
    replace_error = OSError("write failed")

    add_store = _RecordingStore(
        roadmap=_delete_validation_snapshot(),
        replace_error=replace_error,
    )
    add_id_generator = _RecordingIdGenerator(
        generated_ids=[UUID("14141414-1414-1414-1414-141414141414")],
    )
    with pytest.raises(RoadmapItemCrudStoreError) as exc_info:
        add_roadmap_item(
            RoadmapItemAddInput(
                roadmap_id=_ROADMAP_ID,
                parent_id=None,
                title="応用",
                description="desc",
                order=None,
            ),
            store=add_store,
            id_generator=add_id_generator,
        )

    assert exc_info.value.__cause__ is replace_error
    assert add_store.find_roadmap_calls == [_ROADMAP_ID]
    assert add_store.find_item_calls == []
    assert len(add_store.replace_items_calls) == 1
    assert add_id_generator.calls == 1

    move_store = _RecordingStore(
        roadmap=_record(
            [
                _item(
                    item_id="11111111-1111-1111-1111-111111111111",
                    parent_id=None,
                    level="major",
                    title="基礎",
                    description="基本概念",
                    order=0,
                    score=0,
                ),
                _item(
                    item_id="22222222-2222-2222-2222-222222222222",
                    parent_id=None,
                    level="major",
                    title="応用",
                    description="応用技術",
                    order=1,
                    score=0,
                ),
            ],
        ),
        replace_error=replace_error,
    )
    with pytest.raises(RoadmapItemCrudStoreError) as exc_info:
        move_roadmap_item(
            RoadmapItemMoveInput(
                roadmap_id=_ROADMAP_ID,
                item_id=UUID("11111111-1111-1111-1111-111111111111"),
                target_parent_id=None,
                target_order=1,
            ),
            store=move_store,
        )

    assert exc_info.value.__cause__ is replace_error
    assert move_store.find_roadmap_calls == [_ROADMAP_ID]
    assert move_store.find_item_calls == []
    assert len(move_store.replace_items_calls) == 1

    delete_store = _RecordingStore(
        roadmap=_record(
            [
                _item(
                    item_id="11111111-1111-1111-1111-111111111111",
                    parent_id=None,
                    level="major",
                    title="基礎",
                    description="基本概念",
                    order=0,
                    score=0,
                ),
                _item(
                    item_id="aaaa1111-1111-1111-1111-111111111111",
                    parent_id="11111111-1111-1111-1111-111111111111",
                    level="middle",
                    title="文法",
                    description="文法基礎",
                    order=0,
                    score=0,
                ),
                _item(
                    item_id="22222222-2222-2222-2222-222222222222",
                    parent_id=None,
                    level="major",
                    title="応用",
                    description="応用技術",
                    order=1,
                    score=0,
                ),
            ],
        ),
        replace_error=replace_error,
    )
    with pytest.raises(RoadmapItemCrudStoreError) as exc_info:
        delete_roadmap_item(
            RoadmapItemDeleteInput(
                roadmap_id=_ROADMAP_ID,
                item_id=UUID("aaaa1111-1111-1111-1111-111111111111"),
            ),
            store=delete_store,
        )

    assert exc_info.value.__cause__ is replace_error
    assert delete_store.find_roadmap_calls == [_ROADMAP_ID]
    assert delete_store.find_item_calls == []
    assert len(delete_store.replace_items_calls) == 1
