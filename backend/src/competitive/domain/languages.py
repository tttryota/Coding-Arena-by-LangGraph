"""競プロ出題言語レジストリ。"""

from __future__ import annotations

from typing import TypedDict, cast


class CompetitiveLanguageOption(TypedDict):
    """競プロで選択可能な言語。"""

    id: str
    label: str
    editor_placeholder: str
    enabled_order: int


SUPPORTED_LANGUAGES: tuple[CompetitiveLanguageOption, ...] = (
    {
        "id": "python",
        "label": "Python",
        "editor_placeholder": "# Python で解答を書いてください",
        "enabled_order": 0,
    },
    {
        "id": "typescript",
        "label": "TypeScript",
        "editor_placeholder": "// TypeScript で解答を書いてください",
        "enabled_order": 1,
    },
)


def list_supported_languages() -> list[CompetitiveLanguageOption]:
    """表示順でソート済みの言語一覧を返す。"""
    return sorted(
        (cast("CompetitiveLanguageOption", {**item}) for item in SUPPORTED_LANGUAGES),
        key=lambda item: item["enabled_order"],
    )


def default_language() -> str:
    """デフォルト言語IDを返す。"""
    return SUPPORTED_LANGUAGES[0]["id"]


def is_supported_language(language: str) -> bool:
    """登録済みの言語か判定する。"""
    return any(item["id"] == language for item in SUPPORTED_LANGUAGES)


def get_language_option(language: str) -> CompetitiveLanguageOption:
    """言語IDに対応する定義を返す。"""
    for item in SUPPORTED_LANGUAGES:
        if item["id"] == language:
            return cast("CompetitiveLanguageOption", {**item})
    msg = f"Unsupported programming language: {language}"
    raise ValueError(msg)


__all__ = [
    "SUPPORTED_LANGUAGES",
    "CompetitiveLanguageOption",
    "default_language",
    "get_language_option",
    "is_supported_language",
    "list_supported_languages",
]
