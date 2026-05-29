"""theme_selection ノードの Protocol 定義。"""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from competitive.domain.competitive_types import AlgoTheme


class ThemeReaderClient(Protocol):
    """テーマプリセットの読み込みインターフェース。"""

    def pick_random(self) -> AlgoTheme: ...

    def get_by_id(self, theme_id: str) -> AlgoTheme: ...


__all__ = ["ThemeReaderClient"]
