"""theme_selection ノードの Protocol 定義。"""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from competitive.domain.competitive_types import AlgoTheme, AlgoThemeWithHistory


class ThemeReaderClient(Protocol):
    """テーマプリセットの読み込みインターフェース。"""

    def pick_next(self) -> AlgoTheme: ...

    def get_by_id(self, theme_id: str) -> AlgoTheme: ...

    def list_themes(self) -> list[AlgoThemeWithHistory]: ...


__all__ = ["ThemeReaderClient"]
