"""AlgoThemeReader Protocol のファイルベース concrete 実装。"""

from __future__ import annotations

import json
import random
from pathlib import Path

from competitive.domain.competitive_types import AlgoTheme, ThemeSelectionError


class AlgoThemeFileReader:
    def __init__(self, preset_file_path: str | Path) -> None:
        self._path = Path(preset_file_path)
        self._themes: list[AlgoTheme] | None = None

    def _parse_themes(self, data: list[object]) -> list[AlgoTheme]:
        themes: list[AlgoTheme] = []
        for item in data:
            if not isinstance(item, dict):
                msg = f"Theme item must be dict: {item}"
                raise TypeError(msg)
            expected_keys = {"id", "category", "label"}
            if set(item.keys()) != expected_keys:
                msg = f"Theme must have exactly {expected_keys}, got {set(item.keys())}"
                raise TypeError(msg)
            tid, cat, label = item["id"], item["category"], item["label"]
            if not all(isinstance(v, str) for v in (tid, cat, label)):
                msg = f"Theme values must be str: {item}"
                raise TypeError(msg)
            themes.append(AlgoTheme(id=tid, category=cat, label=label))
        ids = [t["id"] for t in themes]
        if len(ids) != len(set(ids)):
            msg = f"Duplicate theme IDs found in: {self._path}"
            raise ThemeSelectionError(error_code="duplicate_ids", message=msg)
        return themes

    def _load(self) -> list[AlgoTheme]:
        if self._themes is not None:
            return self._themes
        if not self._path.exists():
            msg = f"Theme file not found: {self._path}"
            raise ThemeSelectionError(error_code="file_not_found", message=msg)
        try:
            data = json.loads(self._path.read_text(encoding="utf-8"))
            self._themes = self._parse_themes(data)
        except ThemeSelectionError:
            raise
        except (json.JSONDecodeError, KeyError, TypeError) as exc:
            msg = f"Invalid theme file format: {self._path}: {exc}"
            raise ThemeSelectionError(
                error_code="invalid_format", message=msg,
            ) from exc
        return self._themes

    def list_themes(self) -> list[AlgoTheme]:
        """全テーマを返す。"""
        return self._load()

    def pick_random(self) -> AlgoTheme:
        """ランダムに1テーマを選択する。"""
        themes = self._load()
        if not themes:
            msg = "No themes available"
            raise ThemeSelectionError(error_code="no_themes", message=msg)
        return random.choice(themes)  # noqa: S311

    def get_by_id(self, theme_id: str) -> AlgoTheme:
        """ID指定でテーマを取得する。"""
        themes = self._load()
        for theme in themes:
            if theme["id"] == theme_id:
                return theme
        msg = f"Theme not found: {theme_id}"
        raise ThemeSelectionError(error_code="theme_not_found", message=msg)


__all__ = ["AlgoThemeFileReader"]
