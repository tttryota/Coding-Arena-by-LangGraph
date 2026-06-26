"""Static unit-bank registry for algorithm foundations."""

from __future__ import annotations

from importlib import import_module
from pkgutil import walk_packages
from typing import Final

from algorithm_foundations.domain.foundation_types import (
    AlgorithmFoundationCatalogError,
    AlgorithmFoundationUnitBank,
)


def _load_registry() -> dict[str, AlgorithmFoundationUnitBank]:
    registry: dict[str, AlgorithmFoundationUnitBank] = {}
    for module_info in walk_packages(__path__, prefix=f"{__name__}."):
        if module_info.name.endswith(".common"):
            continue
        module = import_module(module_info.name)
        unit_bank = getattr(module, "UNIT_BANK", None)
        if unit_bank is None:
            continue
        unit_id = unit_bank["unit_id"]
        if unit_id in registry:
            raise AlgorithmFoundationCatalogError(
                error_code="duplicate_unit_bank",
                message=f"Duplicate static unit bank found for {unit_id}",
            )
        registry[unit_id] = unit_bank
    return registry


UNIT_BANK_REGISTRY: Final[dict[str, AlgorithmFoundationUnitBank]] = _load_registry()

__all__ = ["UNIT_BANK_REGISTRY"]
