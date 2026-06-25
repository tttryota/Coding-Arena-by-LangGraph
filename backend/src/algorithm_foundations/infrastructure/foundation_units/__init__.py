"""Family registries for algorithm foundation units."""

from __future__ import annotations

from typing import TYPE_CHECKING

from . import (
    bits,
    data_structures_misc,
    dynamic_programming,
    flow_matching,
    geometry,
    graphs,
    greedy,
    hashmap,
    number_theory,
    prefix_sum,
    queue_deque,
    range_queries,
    search,
    sorting,
    stack,
    strings,
)

if TYPE_CHECKING:
    from .common import ProblemTemplate, SpecialThemeUnitDef


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


def build_special_problem_template(unit_id: str) -> ProblemTemplate | None:
    for builder in (
        stack.build_problem_template,
        queue_deque.build_problem_template,
        prefix_sum.build_problem_template,
        hashmap.build_problem_template,
    ):
        template = builder(unit_id)
        if template is not None:
            return template
    return None


def build_family_problem_template(
    *,
    theme_id: str,
    key: str,
    category: str,
) -> ProblemTemplate | None:
    for builder in (
        data_structures_misc.build_problem_template,
        dynamic_programming.build_problem_template,
        search.build_problem_template,
        graphs.build_problem_template,
        range_queries.build_problem_template,
        geometry.build_problem_template,
        greedy.build_problem_template,
        number_theory.build_problem_template,
        strings.build_problem_template,
        bits.build_problem_template,
        sorting.build_problem_template,
        flow_matching.build_problem_template,
    ):
        template = builder(theme_id=theme_id, key=key, category=category)
        if template is not None:
            return template
    return None


__all__ = [
    "SPECIAL_THEME_UNITS",
    "SPECIAL_UNIT_CONCEPT_OVERVIEWS",
    "build_family_problem_template",
    "build_special_problem_template",
]
