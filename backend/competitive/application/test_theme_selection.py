"""theme_selection ノードのテスト。"""

from __future__ import annotations

import pytest

from competitive.domain.competitive_types import ThemeSelectionError


class FakeThemeReader:
    def __init__(self, themes: list[dict[str, str]]) -> None:
        self._themes = themes

    def pick_next(self) -> dict[str, str]:
        if not self._themes:
            raise ThemeSelectionError(error_code="no_themes", message="empty")
        return self._themes[0]

    def get_by_id(self, theme_id: str) -> dict[str, str]:
        for t in self._themes:
            if t["id"] == theme_id:
                return t
        raise ThemeSelectionError(
            error_code="theme_not_found", message=f"Not found: {theme_id}",
        )

    def list_themes(self) -> list[dict[str, object]]:
        return [
            {**t, "display_order": i, "attempt_count": 0, "best_score": None, "last_attempted_at": None}
            for i, t in enumerate(self._themes)
        ]


class TestSelectTheme:
    def test_next_selection(self) -> None:
        from competitive.application.theme_selection import select_theme

        reader = FakeThemeReader([
            {"id": "algo-001", "category": "探索", "label": "二分探索"},
        ])
        result = select_theme(
            {"session_id": "test-001"}, reader=reader,
        )

        assert result["algo_theme_id"] == "algo-001"
        assert result["algo_theme_label"] == "二分探索"
        assert result["algo_theme_category"] == "探索"
        assert result["status"] == "in_progress"
        assert result["session_id"] == "test-001"

    def test_specified_theme_id(self) -> None:
        from competitive.application.theme_selection import select_theme

        reader = FakeThemeReader([
            {"id": "algo-001", "category": "探索", "label": "二分探索"},
            {"id": "algo-002", "category": "グラフ", "label": "DFS"},
        ])
        result = select_theme(
            {"session_id": "test-002", "algo_theme_id": "algo-002"},
            reader=reader,
        )

        assert result["algo_theme_id"] == "algo-002"
        assert result["algo_theme_label"] == "DFS"

    def test_missing_theme_raises(self) -> None:
        from competitive.application.theme_selection import select_theme

        reader = FakeThemeReader([])

        with pytest.raises(ThemeSelectionError):
            select_theme({"session_id": "test-003"}, reader=reader)

    def test_missing_session_id_raises(self) -> None:
        from competitive.application.theme_selection import select_theme

        reader = FakeThemeReader([
            {"id": "algo-001", "category": "探索", "label": "二分探索"},
        ])

        with pytest.raises(ValueError, match="session_id must be provided"):
            select_theme({}, reader=reader)
