from __future__ import annotations

from typing import Any

from backend.benchmark import markdown_toc


def _generate_toc(
    markdown: str, *, min_level: int = 1, max_level: int = 3
) -> Any:
    return markdown_toc.generate_toc(
        markdown,
        min_level=min_level,
        max_level=max_level,
    )


def _heading_rows(result: Any) -> list[tuple[str, int, str]]:
    return [
        (heading.text, heading.level, heading.anchor)
        for heading in result.headings
    ]


def test_generate_toc_with_empty_text_returns_empty_result() -> None:
    """Empty input should produce no headings and no TOC markdown."""
    result = _generate_toc("")

    assert _heading_rows(result) == []
    assert result.markdown == ""


def test_generate_toc_with_body_without_headings_returns_empty_result() -> None:
    """Plain body text should not produce any TOC entries."""
    result = _generate_toc("This is body text.\nStill body text.")

    assert _heading_rows(result) == []
    assert result.markdown == ""


def test_generate_toc_with_single_h1_returns_expected_heading_and_markdown() -> None:
    """A single H1 should be extracted with the expected slug and TOC line."""
    result = _generate_toc("# Introduction")

    assert _heading_rows(result) == [("Introduction", 1, "introduction")]
    assert result.markdown == "- [Introduction](#introduction)"


def test_generate_toc_with_mixed_h1_h2_h3_preserves_hierarchy() -> None:
    """Mixed heading levels should render with relative indentation."""
    result = _generate_toc(
        "# Intro\n\n## Install\n\n### Deep Dive\n\n## Usage"
    )

    assert _heading_rows(result) == [
        ("Intro", 1, "intro"),
        ("Install", 2, "install"),
        ("Deep Dive", 3, "deep-dive"),
        ("Usage", 2, "usage"),
    ]
    assert result.markdown == (
        "- [Intro](#intro)\n"
        "  - [Install](#install)\n"
        "    - [Deep Dive](#deep-dive)\n"
        "  - [Usage](#usage)"
    )


def test_generate_toc_skips_headings_inside_backtick_code_fences() -> None:
    """Headings inside backtick fences should be ignored."""
    result = _generate_toc(
        "# Before\n\n```python\n## Hidden\n```\n\n## After"
    )

    assert _heading_rows(result) == [
        ("Before", 1, "before"),
        ("After", 2, "after"),
    ]
    assert result.markdown == (
        "- [Before](#before)\n"
        "  - [After](#after)"
    )


def test_generate_toc_skips_tilde_fences_without_backtick_cross_close() -> None:
    """Tilde fences should ignore headings until a matching tilde close appears."""
    result = _generate_toc(
        "## Before\n\n~~~~\n### Hidden One\n```\n#### Hidden Two\n~~~~\n\n### After"
    )

    assert _heading_rows(result) == [
        ("Before", 2, "before"),
        ("After", 3, "after"),
    ]
    assert result.markdown == (
        "- [Before](#before)\n"
        "  - [After](#after)"
    )


def test_generate_toc_numbers_duplicate_anchors_for_three_identical_headings() -> None:
    """Duplicate headings should receive GitHub-style numeric suffixes."""
    result = _generate_toc("# Section\n\n# Section\n\n# Section")

    assert _heading_rows(result) == [
        ("Section", 1, "section"),
        ("Section", 1, "section-1"),
        ("Section", 1, "section-2"),
    ]
    assert result.markdown == (
        "- [Section](#section)\n"
        "- [Section](#section-1)\n"
        "- [Section](#section-2)"
    )


def test_generate_toc_filters_by_min_and_max_levels() -> None:
    """Only headings inside the requested level range should appear."""
    result = _generate_toc(
        "# Title\n\n## Install\n\n### Details\n\n#### Too Deep\n\n## Usage",
        min_level=2,
        max_level=3,
    )

    assert _heading_rows(result) == [
        ("Install", 2, "install"),
        ("Details", 3, "details"),
        ("Usage", 2, "usage"),
    ]
    assert result.markdown == (
        "- [Install](#install)\n"
        "  - [Details](#details)\n"
        "- [Usage](#usage)"
    )


def test_generate_toc_strips_bold_code_and_link_markup_from_heading_text() -> None:
    """Supported inline Markdown decorations should be flattened."""
    result = _generate_toc("# **bold** `code` [link](https://example.com)")

    assert _heading_rows(result) == [
        ("bold code link", 1, "bold-code-link")
    ]
    assert result.markdown == "- [bold code link](#bold-code-link)"


def test_generate_toc_preserves_word_internal_underscores() -> None:
    """Underscores inside a word should not be treated as emphasis."""
    result = _generate_toc("## foo_bar_baz")

    assert _heading_rows(result) == [("foo_bar_baz", 2, "foo_bar_baz")]
    assert result.markdown == "- [foo_bar_baz](#foo_bar_baz)"


def test_generate_toc_preserves_hiragana_in_anchor() -> None:
    """Hiragana characters should remain in the generated slug."""
    result = _generate_toc("# ひらがな")

    assert _heading_rows(result) == [("ひらがな", 1, "ひらがな")]
    assert result.markdown == "- [ひらがな](#ひらがな)"


def test_generate_toc_preserves_katakana_in_anchor() -> None:
    """Katakana characters should remain in the generated slug."""
    result = _generate_toc("# カタカナ")

    assert _heading_rows(result) == [("カタカナ", 1, "カタカナ")]
    assert result.markdown == "- [カタカナ](#カタカナ)"


def test_generate_toc_preserves_kanji_in_anchor() -> None:
    """Kanji characters should remain in the generated slug."""
    result = _generate_toc("# 漢字")

    assert _heading_rows(result) == [("漢字", 1, "漢字")]
    assert result.markdown == "- [漢字](#漢字)"


def test_generate_toc_uses_relative_indentation_when_levels_are_skipped() -> None:
    """Indentation depth should reflect the raw level gap without normalization."""
    result = _generate_toc("## Parent\n\n#### Child")

    assert _heading_rows(result) == [
        ("Parent", 2, "parent"),
        ("Child", 4, "child"),
    ]
    assert result.markdown == (
        "- [Parent](#parent)\n"
        "    - [Child](#child)"
    )


def test_generate_toc_strips_atx_closing_hashes() -> None:
    """Trailing ATX closing hashes should not remain in the heading text."""
    result = _generate_toc("## Heading ##")

    assert _heading_rows(result) == [("Heading", 2, "heading")]
    assert result.markdown == "- [Heading](#heading)"


def test_generate_toc_numbers_duplicate_japanese_headings() -> None:
    """Japanese duplicate headings should also receive numeric suffixes."""
    result = _generate_toc("# はじめに\n\n# はじめに")

    assert _heading_rows(result) == [
        ("はじめに", 1, "はじめに"),
        ("はじめに", 1, "はじめに-1"),
    ]
    assert result.markdown == (
        "- [はじめに](#はじめに)\n"
        "- [はじめに](#はじめに-1)"
    )


def test_generate_toc_ignores_all_following_headings_after_unclosed_fence() -> None:
    """An unclosed fence should consume the rest of the document."""
    result = _generate_toc("# Before\n\n```python\n## Hidden\n# Hidden Too")

    assert _heading_rows(result) == [("Before", 1, "before")]
    assert result.markdown == "- [Before](#before)"


def test_generate_toc_returns_empty_when_min_level_exceeds_max_level() -> None:
    """An invalid level range should behave like an empty filter."""
    result = _generate_toc("# Title\n\n## Child", min_level=4, max_level=2)

    assert _heading_rows(result) == []
    assert result.markdown == ""


def test_generate_toc_does_not_recognize_headings_with_leading_space() -> None:
    """ATX headings must start at column zero."""
    result = _generate_toc(" # Not a heading")

    assert _heading_rows(result) == []
    assert result.markdown == ""


def test_generate_toc_does_not_recognize_seven_hash_headings() -> None:
    """Seven or more leading hashes should not count as ATX headings."""
    result = _generate_toc("####### Not a heading")

    assert _heading_rows(result) == []
    assert result.markdown == ""


def test_generate_toc_keeps_empty_slug_for_punctuation_only_heading() -> None:
    """A heading can produce an empty anchor and still render a TOC entry."""
    result = _generate_toc("## !!!")

    assert _heading_rows(result) == [("!!!", 2, "")]
    assert result.markdown == "- [!!!](#)"


def test_generate_toc_applies_known_link_parenthesis_limitation() -> None:
    """Link parsing should stop at the first closing parenthesis as documented."""
    result = _generate_toc(
        "# [text](https://example.com/foo_(bar))"
    )

    assert _heading_rows(result) == [("text)", 1, "text")]
    assert result.markdown == "- [text)](#text)"


def test_generate_toc_matches_the_full_spec_example() -> None:
    """The published example should render exactly as documented."""
    result = _generate_toc(
        "# はじめに\n\n"
        "本文テキスト\n\n"
        "## インストール\n\n"
        "手順の説明\n\n"
        "## 使い方\n\n"
        "### 基本的な使い方\n\n"
        "### 応用例\n\n"
        "## はじめに\n"
    )

    assert _heading_rows(result) == [
        ("はじめに", 1, "はじめに"),
        ("インストール", 2, "インストール"),
        ("使い方", 2, "使い方"),
        ("基本的な使い方", 3, "基本的な使い方"),
        ("応用例", 3, "応用例"),
        ("はじめに", 2, "はじめに-1"),
    ]
    assert result.markdown == (
        "- [はじめに](#はじめに)\n"
        "  - [インストール](#インストール)\n"
        "  - [使い方](#使い方)\n"
        "    - [基本的な使い方](#基本的な使い方)\n"
        "    - [応用例](#応用例)\n"
        "  - [はじめに](#はじめに-1)"
    )
