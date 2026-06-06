"""roadmap item の追加・移動・削除を扱う。"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import replace
from typing import TYPE_CHECKING, NoReturn

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
    RoadmapItemLevel,
    RoadmapItemMoveInput,
    RoadmapItemMoveResult,
)

if TYPE_CHECKING:
    from uuid import UUID


MAJOR_LEVEL: RoadmapItemLevel = "major"
MIDDLE_LEVEL: RoadmapItemLevel = "middle"
DETAIL_LEVEL: RoadmapItemLevel = "detail"
INITIAL_SCORE = 0
MIN_ROOT_MAJOR_COUNT = 1
MIN_ORDER_INDEX = 0
ORDER_SHIFT_STEP = 1
BLANK_TITLE = ""

DETAIL_CHILDREN_ERROR = "detail must not have children"
SNAPSHOT_ITEM_MISSING_ERROR = (
    "item must exist in roadmap snapshot: roadmap_id={roadmap_id}, item_id={item_id}"
)


def add_roadmap_item(
    add_input: RoadmapItemAddInput,
    *,
    store: RoadmapItemCrudStore,
    id_generator: RoadmapItemIdGenerator,
) -> RoadmapItemAddResult:
    """指定位置へ roadmap item を追加する。"""
    roadmap = _find_roadmap(add_input.roadmap_id, store=store)
    items_by_id = {item.id: item for item in roadmap.items}

    _validate_title(add_input.title)
    parent_item, item_level = _resolve_add_parent(
        add_input.parent_id,
        roadmap=roadmap,
        items_by_id=items_by_id,
        store=store,
    )
    sibling_parent_id = None if parent_item is None else parent_item.id
    siblings = _list_siblings_for_parent(roadmap.items, sibling_parent_id)
    insert_order = _resolve_optional_order(add_input.order, sibling_count=len(siblings))

    try:
        created_id = id_generator.generate()
    except Exception as exception:
        message = f"id generation failed for roadmap_id={add_input.roadmap_id}"
        raise RoadmapItemCrudStoreError(message) from exception

    created_item = RoadmapItemCrudItem(
        id=created_id,
        roadmap_id=roadmap.roadmap_id,
        parent_id=sibling_parent_id,
        level=item_level,
        title=add_input.title,
        description=add_input.description,
        order=insert_order,
        score=INITIAL_SCORE,
    )

    updated_items = _insert_item(
        roadmap.items,
        created_item=created_item,
        parent_id=sibling_parent_id,
        insert_order=insert_order,
    )
    updated_items = _canonicalize_items(
        updated_items,
        roadmap_id=roadmap.roadmap_id,
    )
    _replace_items(roadmap.roadmap_id, updated_items, store=store)
    return RoadmapItemAddResult(created_item=created_item)


def move_roadmap_item(
    move_input: RoadmapItemMoveInput,
    *,
    store: RoadmapItemCrudStore,
) -> RoadmapItemMoveResult:
    """roadmap item を別の親・順序へ移動する。"""
    roadmap = _find_roadmap(move_input.roadmap_id, store=store)
    items_by_id = {item.id: item for item in roadmap.items}
    moving_item = _resolve_existing_item(
        move_input.item_id,
        roadmap=roadmap,
        items_by_id=items_by_id,
        store=store,
    )
    target_parent = _resolve_move_parent(
        move_input.target_parent_id,
        moving_item=moving_item,
        roadmap=roadmap,
        store=store,
    )
    if target_parent is not None and _is_descendant(
        ancestor_id=moving_item.id,
        candidate_descendant_id=target_parent.id,
        items=roadmap.items,
    ):
        # 自分自身や子孫の下へ入れると木構造が循環するので事前に拒否する。
        message = (
            "target parent must not be self or descendant: "
            f"roadmap_id={move_input.roadmap_id}, "
            f"item_id={moving_item.id}, "
            f"target_parent_id={target_parent.id}"
        )
        raise RoadmapItemCrudInputError(message)

    target_parent_id = None if target_parent is None else target_parent.id
    updated_items, moved_item = _move_item(
        roadmap.items,
        moving_item=moving_item,
        target_parent_id=target_parent_id,
        target_order=move_input.target_order,
    )
    updated_items = _canonicalize_items(
        updated_items,
        roadmap_id=roadmap.roadmap_id,
    )
    _replace_items(roadmap.roadmap_id, updated_items, store=store)
    return RoadmapItemMoveResult(moved_item=moved_item)


def delete_roadmap_item(
    delete_input: RoadmapItemDeleteInput,
    *,
    store: RoadmapItemCrudStore,
) -> RoadmapItemDeleteResult:
    """roadmap item とその子孫を削除する。"""
    roadmap = _find_roadmap(delete_input.roadmap_id, store=store)
    items_by_id = {item.id: item for item in roadmap.items}
    deleting_item = _resolve_existing_item(
        delete_input.item_id,
        roadmap=roadmap,
        items_by_id=items_by_id,
        store=store,
    )
    if (
        deleting_item.level == MAJOR_LEVEL
        and len(_list_siblings_for_parent(roadmap.items, None)) == MIN_ROOT_MAJOR_COUNT
    ):
        # major を 0 件にすると roadmap の骨格が崩れるため、最後の 1 件は残す。
        message = (
            "last major must not be deleted: "
            f"roadmap_id={delete_input.roadmap_id}, item_id={deleting_item.id}"
        )
        raise RoadmapItemCrudInputError(message)

    deleted_ids = _collect_subtree_ids(deleting_item.id, roadmap.items)
    snapshot_items = tuple(roadmap.items)
    deleted_item_ids = tuple(
        item.id for item in snapshot_items if item.id in deleted_ids
    )
    deleted_count = len(deleted_item_ids)
    remaining_items = [item for item in snapshot_items if item.id not in deleted_ids]
    compacted_items = _compact_parent_orders(
        remaining_items,
        parent_id=deleting_item.parent_id,
    )
    updated_items = _canonicalize_items(
        compacted_items,
        roadmap_id=roadmap.roadmap_id,
    )
    _replace_items(roadmap.roadmap_id, updated_items, store=store)
    return RoadmapItemDeleteResult(
        deleted_item_ids=deleted_item_ids,
        deleted_count=deleted_count,
    )


def _find_roadmap(
    roadmap_id: UUID,
    *,
    store: RoadmapItemCrudStore,
) -> RoadmapItemCrudRoadmapRecord:
    """roadmap を取得し、store 例外を CRUD 用例外へ変換する。"""
    try:
        roadmap = store.find_roadmap(roadmap_id)
    except Exception as exception:
        message = f"roadmap lookup failed for roadmap_id={roadmap_id}"
        raise RoadmapItemCrudStoreError(message) from exception
    if roadmap is None:
        message = f"roadmap not found: {roadmap_id}"
        raise RoadmapItemCrudNotFoundError(message)
    return roadmap


def _resolve_add_parent(
    parent_id: UUID | None,
    *,
    roadmap: RoadmapItemCrudRoadmapRecord,
    items_by_id: dict[UUID, RoadmapItemCrudItem],
    store: RoadmapItemCrudStore,
) -> tuple[RoadmapItemCrudItem | None, RoadmapItemLevel]:
    """追加先 parent と、新規 item に許可される level を決める。"""
    if parent_id is None:
        return None, MAJOR_LEVEL
    parent_item = items_by_id.get(parent_id)
    if parent_item is None:
        _raise_for_missing_reference(parent_id, roadmap=roadmap, store=store)
    if parent_item.level == DETAIL_LEVEL:
        message = (
            f"{DETAIL_CHILDREN_ERROR}: "
            f"roadmap_id={roadmap.roadmap_id}, parent_id={parent_item.id}"
        )
        raise RoadmapItemCrudInputError(message)
    if parent_item.level == MAJOR_LEVEL:
        return parent_item, MIDDLE_LEVEL
    return parent_item, DETAIL_LEVEL


def _resolve_move_parent(
    target_parent_id: UUID | None,
    *,
    moving_item: RoadmapItemCrudItem,
    roadmap: RoadmapItemCrudRoadmapRecord,
    store: RoadmapItemCrudStore,
) -> RoadmapItemCrudItem | None:
    """移動先 parent が level 規約を満たすか検証する。"""
    if target_parent_id is None:
        if moving_item.level != MAJOR_LEVEL:
            message = (
                "only major can move to root: "
                f"roadmap_id={roadmap.roadmap_id}, item_id={moving_item.id}, "
                f"moving_item.level={moving_item.level}"
            )
            raise RoadmapItemCrudInputError(message)
        return None
    target_parent = {item.id: item for item in roadmap.items}.get(target_parent_id)
    if target_parent is None:
        _raise_for_missing_reference(target_parent_id, roadmap=roadmap, store=store)
    if target_parent.level == DETAIL_LEVEL:
        message = (
            f"{DETAIL_CHILDREN_ERROR}: "
            f"roadmap_id={roadmap.roadmap_id}, "
            f"target_parent_id={target_parent.id}, item_id={moving_item.id}"
        )
        raise RoadmapItemCrudInputError(message)
    expected_level = (
        MIDDLE_LEVEL if target_parent.level == MAJOR_LEVEL else DETAIL_LEVEL
    )
    if moving_item.level != expected_level:
        message = (
            "move level relationship is invalid: "
            f"roadmap_id={roadmap.roadmap_id}, "
            f"item_id={moving_item.id}, "
            f"target_parent_id={target_parent.id}, "
            f"moving_item.level={moving_item.level}, "
            f"target_parent.level={target_parent.level}, "
            f"expected_moving_level={expected_level}"
        )
        raise RoadmapItemCrudInputError(message)
    return target_parent


def _resolve_existing_item(
    item_id: UUID,
    *,
    roadmap: RoadmapItemCrudRoadmapRecord,
    items_by_id: dict[UUID, RoadmapItemCrudItem],
    store: RoadmapItemCrudStore,
) -> RoadmapItemCrudItem:
    """snapshot 上に item が存在することを保証する。"""
    item = items_by_id.get(item_id)
    if item is not None:
        return item
    _raise_for_missing_reference(item_id, roadmap=roadmap, store=store)
    message = "unreachable after missing reference check"
    raise AssertionError(message)


def _raise_for_missing_reference(
    item_id: UUID,
    *,
    roadmap: RoadmapItemCrudRoadmapRecord,
    store: RoadmapItemCrudStore,
) -> NoReturn:
    """snapshot と個別 lookup の差分から not found / cross-roadmap を判定する。"""
    try:
        found_item = store.find_item(item_id)
    except Exception as exception:
        message = (
            f"item lookup failed for roadmap_id={roadmap.roadmap_id}, item_id={item_id}"
        )
        raise RoadmapItemCrudStoreError(message) from exception
    if found_item is None:
        message = f"item not found: {item_id}"
        raise RoadmapItemCrudNotFoundError(message)
    if found_item.roadmap_id != roadmap.roadmap_id:
        message = (
            "item belongs to a different roadmap: "
            f"roadmap_id={roadmap.roadmap_id}, "
            f"item_id={item_id}, "
            f"item_roadmap_id={found_item.roadmap_id}"
        )
        raise RoadmapItemCrudInputError(message)
    message = _build_snapshot_item_missing_message(
        roadmap_id=roadmap.roadmap_id,
        item_id=item_id,
    )
    raise RoadmapItemCrudStoreError(message)


def _build_snapshot_item_missing_message(*, roadmap_id: UUID, item_id: UUID) -> str:
    """snapshot 不整合時の共通メッセージを組み立てる。"""
    return SNAPSHOT_ITEM_MISSING_ERROR.format(roadmap_id=roadmap_id, item_id=item_id)


def _validate_title(title: str) -> None:
    """空白タイトルを拒否する。"""
    if title.strip() == BLANK_TITLE:
        message = f"title must be non-blank: got {title!r}"
        raise RoadmapItemCrudInputError(message)


def _build_order_out_of_range_message(
    *,
    field_name: str,
    value: int,
    sibling_count: int,
) -> str:
    """順序範囲エラーの文言を共通化する。"""
    return (
        f"{field_name} is out of range: "
        f"field_name={field_name}, "
        f"value={value}, "
        f"allowed_range={MIN_ORDER_INDEX}..{sibling_count}, "
        f"sibling_count={sibling_count}"
    )


def _resolve_optional_order(order: int | None, *, sibling_count: int) -> int:
    """省略時は末尾追加とし、指定時は範囲検証を行う。"""
    if order is None:
        return sibling_count
    if order < MIN_ORDER_INDEX or order > sibling_count:
        message = _build_order_out_of_range_message(
            field_name="order",
            value=order,
            sibling_count=sibling_count,
        )
        raise RoadmapItemCrudInputError(message)
    return order


def _resolve_required_order(target_order: int, *, sibling_count: int) -> int:
    if target_order < MIN_ORDER_INDEX or target_order > sibling_count:
        message = _build_order_out_of_range_message(
            field_name="target_order",
            value=target_order,
            sibling_count=sibling_count,
        )
        raise RoadmapItemCrudInputError(message)
    return target_order


def _list_siblings_for_parent(
    items: list[RoadmapItemCrudItem],
    parent_id: UUID | None,
) -> list[RoadmapItemCrudItem]:
    return sorted(
        [item for item in items if item.parent_id == parent_id],
        key=lambda item: item.order,
    )


def _insert_item(
    items: list[RoadmapItemCrudItem],
    *,
    created_item: RoadmapItemCrudItem,
    parent_id: UUID | None,
    insert_order: int,
) -> list[RoadmapItemCrudItem]:
    updated_items: list[RoadmapItemCrudItem] = []
    for item in items:
        if item.parent_id == parent_id and item.order >= insert_order:
            updated_items.append(replace(item, order=item.order + ORDER_SHIFT_STEP))
            continue
        updated_items.append(item)
    updated_items.append(created_item)
    return updated_items


def _move_item(
    items: list[RoadmapItemCrudItem],
    *,
    moving_item: RoadmapItemCrudItem,
    target_parent_id: UUID | None,
    target_order: int,
) -> tuple[list[RoadmapItemCrudItem], RoadmapItemCrudItem]:
    without_moving = [item for item in items if item.id != moving_item.id]
    compacted_items = _compact_parent_orders(
        without_moving,
        parent_id=moving_item.parent_id,
    )
    target_siblings = _list_siblings_for_parent(compacted_items, target_parent_id)
    final_target_order = _resolve_required_order(
        target_order,
        sibling_count=len(target_siblings),
    )
    moved_item = replace(
        moving_item,
        parent_id=target_parent_id,
        order=final_target_order,
    )

    updated_items: list[RoadmapItemCrudItem] = []
    for item in compacted_items:
        if item.parent_id == target_parent_id and item.order >= final_target_order:
            updated_items.append(replace(item, order=item.order + ORDER_SHIFT_STEP))
            continue
        updated_items.append(item)
    updated_items.append(moved_item)
    return updated_items, moved_item


def _compact_parent_orders(
    items: list[RoadmapItemCrudItem],
    *,
    parent_id: UUID | None,
) -> list[RoadmapItemCrudItem]:
    siblings = _list_siblings_for_parent(items, parent_id)
    order_by_id = {item.id: index for index, item in enumerate(siblings)}

    compacted_items: list[RoadmapItemCrudItem] = []
    for item in items:
        if item.parent_id == parent_id:
            compacted_items.append(replace(item, order=order_by_id[item.id]))
            continue
        compacted_items.append(item)
    return compacted_items


def _collect_subtree_ids(
    root_item_id: UUID,
    items: list[RoadmapItemCrudItem],
) -> set[UUID]:
    children_by_parent = _build_children_by_parent(items)
    stack = [root_item_id]
    subtree_ids: set[UUID] = set()
    while stack:
        current_id = stack.pop()
        if current_id in subtree_ids:
            continue
        subtree_ids.add(current_id)
        children = children_by_parent.get(current_id, [])
        for child in reversed(children):
            stack.append(child.id)
    return subtree_ids


def _is_descendant(
    *,
    ancestor_id: UUID,
    candidate_descendant_id: UUID,
    items: list[RoadmapItemCrudItem],
) -> bool:
    return candidate_descendant_id in _collect_subtree_ids(ancestor_id, items)


def _build_children_by_parent(
    items: list[RoadmapItemCrudItem],
) -> dict[UUID | None, list[RoadmapItemCrudItem]]:
    children: dict[UUID | None, list[RoadmapItemCrudItem]] = defaultdict(list)
    for item in items:
        children[item.parent_id].append(item)
    for sibling_list in children.values():
        sibling_list.sort(key=lambda item: item.order)
    return children


def _canonicalize_items(
    items: list[RoadmapItemCrudItem],
    *,
    roadmap_id: UUID,
) -> list[RoadmapItemCrudItem]:
    children_by_parent = _build_children_by_parent(items)
    ordered_items: list[RoadmapItemCrudItem] = []
    visited_item_ids: set[UUID] = set()

    def visit(parent_id: UUID | None) -> None:
        for item in children_by_parent.get(parent_id, []):
            if item.id in visited_item_ids:
                continue
            visited_item_ids.add(item.id)
            ordered_items.append(item)
            visit(item.id)

    visit(None)
    if len(ordered_items) != len(items):
        unvisited_item_ids = [
            str(item.id) for item in items if item.id not in visited_item_ids
        ]
        message = (
            "roadmap snapshot must be fully connected from root: "
            f"roadmap_id={roadmap_id}, "
            f"visited_count={len(ordered_items)}, "
            f"item_count={len(items)}, "
            f"unvisited_item_ids={unvisited_item_ids}"
        )
        raise RoadmapItemCrudStoreError(message)
    return ordered_items


def _replace_items(
    roadmap_id: UUID,
    items: list[RoadmapItemCrudItem],
    *,
    store: RoadmapItemCrudStore,
) -> None:
    try:
        store.replace_items(roadmap_id, items)
    except Exception as exception:
        message = f"replace items failed for roadmap_id={roadmap_id}"
        raise RoadmapItemCrudStoreError(message) from exception


__all__ = [
    "add_roadmap_item",
    "delete_roadmap_item",
    "move_roadmap_item",
]
