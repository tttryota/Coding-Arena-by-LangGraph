"""AlgoThemeFileReader のテスト。"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from pathlib import Path

from competitive.domain.competitive_types import ThemeSelectionError


class TestAlgoThemeFileReader:
    def test_list_themes_returns_all(self, tmp_path: Path) -> None:
        data = [
            {"id": "algo-001", "category": "探索", "label": "二分探索"},
            {"id": "algo-002", "category": "グラフ", "label": "DFS"},
        ]
        f = tmp_path / "themes.json"
        f.write_text(json.dumps(data), encoding="utf-8")

        from competitive.infrastructure.algo_theme_file_reader import (
            AlgoThemeFileReader,
        )

        reader = AlgoThemeFileReader(f)
        themes = reader.list_themes()

        assert len(themes) == 2
        assert themes[0]["id"] == "algo-001"
        assert themes[1]["label"] == "DFS"

    def test_pick_random_returns_valid_theme(self, tmp_path: Path) -> None:
        data = [
            {"id": "algo-001", "category": "探索", "label": "二分探索"},
            {"id": "algo-002", "category": "グラフ", "label": "DFS"},
        ]
        f = tmp_path / "themes.json"
        f.write_text(json.dumps(data), encoding="utf-8")

        from competitive.infrastructure.algo_theme_file_reader import (
            AlgoThemeFileReader,
        )

        reader = AlgoThemeFileReader(f)
        theme = reader.pick_random()

        assert theme["id"] in {"algo-001", "algo-002"}

    def test_get_by_id_returns_matching_theme(self, tmp_path: Path) -> None:
        data = [
            {"id": "algo-001", "category": "探索", "label": "二分探索"},
            {"id": "algo-002", "category": "グラフ", "label": "DFS"},
        ]
        f = tmp_path / "themes.json"
        f.write_text(json.dumps(data), encoding="utf-8")

        from competitive.infrastructure.algo_theme_file_reader import (
            AlgoThemeFileReader,
        )

        reader = AlgoThemeFileReader(f)
        theme = reader.get_by_id("algo-002")

        assert theme["id"] == "algo-002"
        assert theme["label"] == "DFS"

    def test_get_by_id_raises_on_missing(self, tmp_path: Path) -> None:
        data = [{"id": "algo-001", "category": "探索", "label": "二分探索"}]
        f = tmp_path / "themes.json"
        f.write_text(json.dumps(data), encoding="utf-8")

        from competitive.infrastructure.algo_theme_file_reader import (
            AlgoThemeFileReader,
        )

        reader = AlgoThemeFileReader(f)

        with pytest.raises(ThemeSelectionError) as exc_info:
            reader.get_by_id("algo-999")
        assert exc_info.value.error_code == "theme_not_found"

    def test_file_not_found_raises(self, tmp_path: Path) -> None:
        from competitive.infrastructure.algo_theme_file_reader import (
            AlgoThemeFileReader,
        )

        reader = AlgoThemeFileReader(tmp_path / "nonexistent.json")

        with pytest.raises(ThemeSelectionError) as exc_info:
            reader.list_themes()
        assert exc_info.value.error_code == "file_not_found"

    def test_pick_random_raises_on_empty(self, tmp_path: Path) -> None:
        f = tmp_path / "themes.json"
        f.write_text("[]", encoding="utf-8")

        from competitive.infrastructure.algo_theme_file_reader import (
            AlgoThemeFileReader,
        )

        reader = AlgoThemeFileReader(f)

        with pytest.raises(ThemeSelectionError) as exc_info:
            reader.pick_random()
        assert exc_info.value.error_code == "no_themes"

    def test_invalid_json_raises_theme_selection_error(
        self, tmp_path: Path,
    ) -> None:
        f = tmp_path / "themes.json"
        f.write_text("not valid json", encoding="utf-8")

        from competitive.infrastructure.algo_theme_file_reader import (
            AlgoThemeFileReader,
        )

        reader = AlgoThemeFileReader(f)

        with pytest.raises(ThemeSelectionError) as exc_info:
            reader.list_themes()
        assert exc_info.value.error_code == "invalid_format"

    def test_missing_key_raises_theme_selection_error(
        self, tmp_path: Path,
    ) -> None:
        data = [{"id": "algo-001", "category": "探索"}]  # label missing
        f = tmp_path / "themes.json"
        f.write_text(json.dumps(data), encoding="utf-8")

        from competitive.infrastructure.algo_theme_file_reader import (
            AlgoThemeFileReader,
        )

        reader = AlgoThemeFileReader(f)

        with pytest.raises(ThemeSelectionError) as exc_info:
            reader.list_themes()
        assert exc_info.value.error_code == "invalid_format"

    def test_duplicate_ids_raises(self, tmp_path: Path) -> None:
        data = [
            {"id": "algo-001", "category": "探索", "label": "二分探索"},
            {"id": "algo-001", "category": "ソート", "label": "バブルソート"},
        ]
        f = tmp_path / "themes.json"
        f.write_text(json.dumps(data), encoding="utf-8")

        from competitive.infrastructure.algo_theme_file_reader import (
            AlgoThemeFileReader,
        )

        reader = AlgoThemeFileReader(f)

        with pytest.raises(ThemeSelectionError) as exc_info:
            reader.list_themes()
        assert exc_info.value.error_code == "duplicate_ids"

    def test_caches_after_first_load(self, tmp_path: Path) -> None:
        data = [{"id": "algo-001", "category": "探索", "label": "二分探索"}]
        f = tmp_path / "themes.json"
        f.write_text(json.dumps(data), encoding="utf-8")

        from competitive.infrastructure.algo_theme_file_reader import (
            AlgoThemeFileReader,
        )

        reader = AlgoThemeFileReader(f)
        first = reader.list_themes()
        f.write_text("[]", encoding="utf-8")
        second = reader.list_themes()

        assert first is second
