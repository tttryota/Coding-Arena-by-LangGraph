from __future__ import annotations

from backend.benchmark.markdown_toc import generate_toc


class TestEmptyInput:
    def test_generate_toc_empty_string_returns_empty_headings_and_markdown(
        self,
    ) -> None:
        result = generate_toc("")

        assert result.headings == ()
        assert result.markdown == ""

    def test_generate_toc_no_headings_returns_empty_headings_and_markdown(
        self,
    ) -> None:
        result = generate_toc("本文テキストのみ\n改行もある")

        assert result.headings == ()
        assert result.markdown == ""


class TestBasicHeadingExtraction:
    def test_generate_toc_single_h1_returns_correct_text_level_anchor_markdown(
        self,
    ) -> None:
        result = generate_toc("# Hello")

        assert len(result.headings) == 1
        heading = result.headings[0]
        assert heading.text == "Hello"
        assert heading.level == 1
        assert heading.anchor == "hello"
        assert result.markdown == "- [Hello](#hello)"

    def test_generate_toc_mixed_h1_h2_h3_returns_four_headings_with_correct_indent(
        self,
    ) -> None:
        text = "# Title\n\n## Section A\n\n### Sub A\n\n## Section B"

        result = generate_toc(text)

        assert len(result.headings) == 4
        expected_markdown = (
            "- [Title](#title)\n"
            "  - [Section A](#section-a)\n"
            "    - [Sub A](#sub-a)\n"
            "  - [Section B](#section-b)"
        )
        assert result.markdown == expected_markdown


class TestCodeBlockSkipping:
    def test_generate_toc_backtick_code_block_skips_headings_inside(self) -> None:
        text = "# Real\n\n```\n# Fake\n```\n\n## Also Real"

        result = generate_toc(text)

        assert len(result.headings) == 2
        assert result.headings[0].text == "Real"
        assert result.headings[1].text == "Also Real"

    def test_generate_toc_tilde_fence_skips_and_backtick_tilde_independent(
        self,
    ) -> None:
        text = (
            "# Before\n"
            "\n"
            "~~~\n"
            "# Inside Tilde\n"
            "~~~\n"
            "\n"
            "````\n"
            "# Inside Backtick\n"
            "~~~\n"
            "# Still Inside Backtick\n"
            "````\n"
            "\n"
            "## After"
        )

        result = generate_toc(text)

        assert len(result.headings) == 2
        assert result.headings[0].text == "Before"
        assert result.headings[1].text == "After"


class TestDuplicateAnchors:
    def test_generate_toc_three_same_headings_get_numbered_anchors(self) -> None:
        text = "# Section\n\n## Section\n\n### Section"

        result = generate_toc(text)

        assert result.headings[0].anchor == "section"
        assert result.headings[1].anchor == "section-1"
        assert result.headings[2].anchor == "section-2"
        assert "- [Section](#section)\n" in result.markdown
        assert "- [Section](#section-1)\n" in result.markdown
        assert "- [Section](#section-2)" in result.markdown

    def test_generate_toc_japanese_duplicate_headings_get_numbered_anchors(
        self,
    ) -> None:
        text = "# はじめに\n\n## はじめに"

        result = generate_toc(text)

        assert result.headings[0].anchor == "はじめに"
        assert result.headings[1].anchor == "はじめに-1"
        assert "(#はじめに)" in result.markdown
        assert "(#はじめに-1)" in result.markdown


class TestLevelFiltering:
    def test_generate_toc_min2_max3_extracts_only_h2_h3_with_correct_indent(
        self,
    ) -> None:
        text = "# H1\n\n## H2\n\n### H3\n\n#### H4"

        result = generate_toc(text, min_level=2, max_level=3)

        assert len(result.headings) == 2
        assert result.headings[0].text == "H2"
        assert result.headings[1].text == "H3"
        expected_markdown = "- [H2](#h2)\n  - [H3](#h3)"
        assert result.markdown == expected_markdown


class TestDecorationStripping:
    def test_generate_toc_strips_bold_code_link_from_heading(self) -> None:
        text = "# **bold** and `code` and [link](http://example.com)"

        result = generate_toc(text)

        assert result.headings[0].text == "bold and code and link"
        assert result.headings[0].anchor == "bold-and-code-and-link"
        assert result.markdown == "- [bold and code and link](#bold-and-code-and-link)"

    def test_generate_toc_preserves_word_internal_underscores(self) -> None:
        text = "# foo_bar_baz"

        result = generate_toc(text)

        assert result.headings[0].text == "foo_bar_baz"
        assert result.headings[0].anchor == "foo_bar_baz"


class TestJapaneseAnchors:
    def test_generate_toc_hiragana_heading_preserves_anchor(self) -> None:
        result = generate_toc("# はじめに")

        assert result.headings[0].anchor == "はじめに"

    def test_generate_toc_katakana_heading_preserves_anchor(self) -> None:
        result = generate_toc("# インストール")

        assert result.headings[0].anchor == "インストール"

    def test_generate_toc_kanji_heading_preserves_anchor(self) -> None:
        result = generate_toc("# 導入方法")

        assert result.headings[0].anchor == "導入方法"


class TestRelativeIndent:
    def test_generate_toc_h2_and_h4_only_has_depth_gap_of_two(self) -> None:
        text = "## Section\n\n#### Deep"

        result = generate_toc(text, max_level=6)

        assert len(result.headings) == 2
        expected_markdown = "- [Section](#section)\n    - [Deep](#deep)"
        assert result.markdown == expected_markdown


class TestAtxClosing:
    def test_generate_toc_atx_trailing_hashes_removed(self) -> None:
        text = "## Heading ##"

        result = generate_toc(text)

        assert result.headings[0].text == "Heading"
        assert result.headings[0].anchor == "heading"
        assert result.markdown == "- [Heading](#heading)"
