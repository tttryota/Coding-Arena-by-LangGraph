"""Family registries for algorithm foundation units."""

from __future__ import annotations

from typing import TYPE_CHECKING

from . import (
    hashmap,
    prefix_sum,
    queue_deque,
    stack,
)

if TYPE_CHECKING:
    from .common import SpecialThemeUnitDef


def _merge_special_theme_units(*families: tuple[SpecialThemeUnitDef, ...]) -> dict[str, list[tuple[str, str, str]]]:
    merged: dict[str, list[tuple[int, str, str, str]]] = {}
    for family in families:
        for theme_id, order, slug, title, unit_kind in family:
            units = merged.setdefault(theme_id, [])
            if any(existing_order == order for existing_order, *_ in units):
                message = f"duplicate special unit order detected: {theme_id=} {order=}"
                raise ValueError(
                    message,
                )
            if any(existing_slug == slug for _, existing_slug, *_ in units):
                message = f"duplicate special unit slug detected: {theme_id=} {slug=}"
                raise ValueError(
                    message,
                )
            units.append((order, slug, title, unit_kind))
    return {
        theme_id: [
            (slug, title, unit_kind)
            for _, slug, title, unit_kind in sorted(units, key=lambda item: item[0])
        ]
        for theme_id, units in merged.items()
    }


SPECIAL_THEME_UNITS = _merge_special_theme_units(
    stack.SPECIAL_THEME_UNITS,
    queue_deque.SPECIAL_THEME_UNITS,
    prefix_sum.SPECIAL_THEME_UNITS,
    hashmap.SPECIAL_THEME_UNITS,
)

SPECIAL_UNIT_CONCEPT_OVERVIEWS = {
    **stack.SPECIAL_UNIT_CONCEPT_OVERVIEWS,
    **queue_deque.SPECIAL_UNIT_CONCEPT_OVERVIEWS,
    **prefix_sum.SPECIAL_UNIT_CONCEPT_OVERVIEWS,
    **hashmap.SPECIAL_UNIT_CONCEPT_OVERVIEWS,
}

__all__ = [
    "SPECIAL_THEME_UNITS",
    "SPECIAL_UNIT_CONCEPT_OVERVIEWS",
]
