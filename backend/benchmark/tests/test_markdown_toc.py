from backend.benchmark.markdown_toc import Heading, generate_toc


class TestGenerateToc_EmptyInput:
    def test_generate_toc_empty_string_returns_empty_headings_and_markdown(
        self,
    ) -> None:
        result = generate_toc("")

        assert result.headings == []
        assert result.markdown == ""

    def test_generate_toc_no_headings_returns_empty_headings_and_markdown(
        self,
    ) -> None:
        result = generate_toc("本文のみ\n改行あり")

        assert result.headings == []
        assert result.markdown == ""


class TestGenerateToc_SingleHeading:
    def test_generate_toc_single_h1_returns_correct_text_level_anchor_markdown(
        self,
    ) -> None:
        result = generate_toc("# Hello World")

        assert result.headings == [
            Heading(text="Hello World", level=1, anchor="hello-world"),
        ]
        assert result.markdown == "- [Hello World](#hello-world)"


class TestGenerateToc_MultiLevel:
    def test_generate_toc_h1_h2_h3_mixed_returns_4_headings_with_correct_indent(
        self,
    ) -> None:
        result = generate_toc("# Title\n## Section\n### Sub\n## Another")

        assert len(result.headings) == 4
        assert result.headings[0].level == 1
        assert result.headings[1].level == 2
        assert result.headings[2].level == 3
        assert result.headings[3].level == 2

        lines = result.markdown.split("\n")
        assert lines[0].startswith("- ")
        assert lines[1].startswith("  - ")
        assert lines[2].startswith("    - ")
        assert lines[3].startswith("  - ")


class TestGenerateToc_CodeBlock:
    def test_generate_toc_backtick_code_block_skips_headings_inside(
        self,
    ) -> None:
        text = (
            "# Real Heading\n"
            "```\n"
            "# comment inside code\n"
            "```\n"
            "## Another Real"
        )
        result = generate_toc(text)

        assert len(result.headings) == 2
        assert result.headings[0].text == "Real Heading"
        assert result.headings[1].text == "Another Real"

    def test_generate_toc_tilde_code_block_skips_headings_and_fences_dont_cross(
        self,
    ) -> None:
        text = (
            "# Before\n"
            "~~~\n"
            "# inside tilde\n"
            "```\n"
            "# still inside tilde\n"
            "~~~\n"
            "# After"
        )
        result = generate_toc(text)

        assert len(result.headings) == 2
        assert result.headings[0].text == "Before"
        assert result.headings[1].text == "After"


class TestGenerateToc_DuplicateAnchor:
    def test_generate_toc_three_same_headings_anchors_numbered_sequentially(
        self,
    ) -> None:
        result = generate_toc("# Section\n# Section\n# Section")

        assert len(result.headings) == 3
        assert result.headings[0].anchor == "section"
        assert result.headings[1].anchor == "section-1"
        assert result.headings[2].anchor == "section-2"

        lines = result.markdown.split("\n")
        assert "(#section)" in lines[0]
        assert "(#section-1)" in lines[1]
        assert "(#section-2)" in lines[2]


class TestGenerateToc_LevelFilter:
    def test_generate_toc_min2_max3_extracts_only_h2_h3_with_correct_indent(
        self,
    ) -> None:
        text = "# H1\n## H2\n### H3\n#### H4"
        result = generate_toc(text, min_level=2, max_level=3)

        assert len(result.headings) == 2
        assert result.headings[0].text == "H2"
        assert result.headings[1].text == "H3"

        lines = result.markdown.split("\n")
        # H2 is min level → depth 0
        assert lines[0].startswith("- ")
        # H3 is depth 1
        assert lines[1].startswith("  - ")


class TestGenerateToc_DecorationRemoval:
    def test_generate_toc_bold_code_link_removed_in_text_anchor_markdown(
        self,
    ) -> None:
        text = "# **Bold** and `code` and [link](http://example.com)"
        result = generate_toc(text)

        assert result.headings[0].text == "Bold and code and link"
        assert result.headings[0].anchor == "bold-and-code-and-link"
        assert result.markdown == "- [Bold and code and link](#bold-and-code-and-link)"


class TestGenerateToc_Underscore:
    def test_generate_toc_foo_bar_baz_preserves_underscores_in_text_and_anchor(
        self,
    ) -> None:
        result = generate_toc("# foo_bar_baz")

        assert result.headings[0].text == "foo_bar_baz"
        assert result.headings[0].anchor == "foo_bar_baz"


class TestGenerateToc_JapaneseAnchor:
    def test_generate_toc_hiragana_heading_preserves_anchor(self) -> None:
        result = generate_toc("# はじめに")

        assert result.headings[0].anchor == "はじめに"

    def test_generate_toc_katakana_heading_preserves_anchor(self) -> None:
        result = generate_toc("# セットアップ")

        assert result.headings[0].anchor == "セットアップ"

    def test_generate_toc_kanji_heading_preserves_anchor(self) -> None:
        result = generate_toc("# 設定方法")

        assert result.headings[0].anchor == "設定方法"


class TestGenerateToc_SkippedLevel:
    def test_generate_toc_h2_and_h4_only_relative_indent_reflects_level_gap(
        self,
    ) -> None:
        result = generate_toc("## Overview\n#### Detail", max_level=6)

        assert len(result.headings) == 2

        lines = result.markdown.split("\n")
        # H2 is min level → depth 0
        assert lines[0].startswith("- ")
        # H4 is depth 2 (level diff 4-2=2) → 4 spaces
        assert lines[1].startswith("    - ")


class TestGenerateToc_AtxClosing:
    def test_generate_toc_trailing_hashes_removed_in_text_anchor_markdown(
        self,
    ) -> None:
        result = generate_toc("## Heading ##")

        assert result.headings[0].text == "Heading"
        assert result.headings[0].anchor == "heading"
        assert result.markdown == "- [Heading](#heading)"


class TestGenerateToc_JapaneseDuplicateAnchor:
    def test_generate_toc_japanese_duplicate_headings_anchor_numbered_correctly(
        self,
    ) -> None:
        text = "# はじめに\n## 概要\n# はじめに"
        result = generate_toc(text)

        assert result.headings[2].anchor == "はじめに-1"

        lines = result.markdown.split("\n")
        assert "[はじめに](#はじめに-1)" in lines[2]


class TestTocResult_Frozen:
    def test_toc_result_is_immutable(self) -> None:
        result = generate_toc("# Test")

        import pytest

        with pytest.raises(AttributeError):
            result.markdown = "modified"  # type: ignore[misc]

    def test_heading_is_immutable(self) -> None:
        result = generate_toc("# Test")

        import pytest

        with pytest.raises(AttributeError):
            result.headings[0].text = "modified"  # type: ignore[misc]
