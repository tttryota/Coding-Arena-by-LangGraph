from __future__ import annotations

from backend.benchmark.markdown_toc import generate_toc


class TestEmptyInput:
    def test_generate_toc_empty_string_returns_empty_headings_and_markdown(
        self,
    ) -> None:
        result = generate_toc("")
        assert result.headings == []
        assert result.markdown == ""


class TestNoHeadings:
    def test_generate_toc_plain_text_returns_empty_headings_and_markdown(
        self,
    ) -> None:
        result = generate_toc("This is just plain text.\nNo headings here.")
        assert result.headings == []
        assert result.markdown == ""


class TestSingleHeading:
    def test_generate_toc_single_h1_returns_correct_text_level_anchor_markdown(
        self,
    ) -> None:
        result = generate_toc("# Hello World")
        assert len(result.headings) == 1
        heading = result.headings[0]
        assert heading.text == "Hello World"
        assert heading.level == 1
        assert heading.anchor == "hello-world"
        assert result.markdown == "- [Hello World](#hello-world)"


class TestMixedLevels:
    def test_generate_toc_h1_h2_h3_mixed_returns_4_headings_with_correct_indent(
        self,
    ) -> None:
        text = "# Title\n## Section A\n### Subsection\n## Section B"
        result = generate_toc(text)
        assert len(result.headings) == 4
        assert result.headings[0].level == 1
        assert result.headings[1].level == 2
        assert result.headings[2].level == 3
        assert result.headings[3].level == 2
        expected_md = (
            "- [Title](#title)\n"
            "  - [Section A](#section-a)\n"
            "    - [Subsection](#subsection)\n"
            "  - [Section B](#section-b)"
        )
        assert result.markdown == expected_md


class TestCodeBlockSkip:
    def test_generate_toc_backtick_code_block_skips_headings_inside(
        self,
    ) -> None:
        text = "# Real Heading\n```\n# Not a heading\n```\n## Another Real"
        result = generate_toc(text)
        assert len(result.headings) == 2
        assert result.headings[0].text == "Real Heading"
        assert result.headings[1].text == "Another Real"

    def test_generate_toc_tilde_code_block_skips_headings_and_backtick_does_not_close_tilde(
        self,
    ) -> None:
        text = (
            "# Before\n"
            "~~~\n"
            "# Inside tilde block\n"
            "```\n"
            "# Still inside tilde block\n"
            "~~~\n"
            "## After"
        )
        result = generate_toc(text)
        assert len(result.headings) == 2
        assert result.headings[0].text == "Before"
        assert result.headings[1].text == "After"


class TestDuplicateAnchors:
    def test_generate_toc_three_same_headings_returns_numbered_anchors_and_markdown(
        self,
    ) -> None:
        text = "# Section\n# Section\n# Section"
        result = generate_toc(text)
        assert len(result.headings) == 3
        assert result.headings[0].anchor == "section"
        assert result.headings[1].anchor == "section-1"
        assert result.headings[2].anchor == "section-2"
        expected_md = (
            "- [Section](#section)\n- [Section](#section-1)\n- [Section](#section-2)"
        )
        assert result.markdown == expected_md


class TestMinMaxLevel:
    def test_generate_toc_min2_max3_extracts_only_h2_h3_with_correct_indent(
        self,
    ) -> None:
        text = "# H1 Title\n## H2 Section\n### H3 Sub\n#### H4 Deep"
        result = generate_toc(text, min_level=2, max_level=3)
        assert len(result.headings) == 2
        assert result.headings[0].text == "H2 Section"
        assert result.headings[0].level == 2
        assert result.headings[1].text == "H3 Sub"
        assert result.headings[1].level == 3
        expected_md = "- [H2 Section](#h2-section)\n  - [H3 Sub](#h3-sub)"
        assert result.markdown == expected_md


class TestDecorationRemoval:
    def test_generate_toc_bold_code_link_removed_returns_clean_text_anchor_markdown(
        self,
    ) -> None:
        text = "## **bold** and `code` and [link](https://example.com)"
        result = generate_toc(text, min_level=1, max_level=6)
        assert len(result.headings) == 1
        heading = result.headings[0]
        assert heading.text == "bold and code and link"
        assert heading.anchor == "bold-and-code-and-link"
        assert result.markdown == "- [bold and code and link](#bold-and-code-and-link)"


class TestUnderscorePreservation:
    def test_generate_toc_foo_bar_baz_preserves_underscores_in_text_and_anchor(
        self,
    ) -> None:
        text = "# foo_bar_baz"
        result = generate_toc(text)
        heading = result.headings[0]
        assert heading.text == "foo_bar_baz"
        assert heading.anchor == "foo_bar_baz"


class TestJapaneseAnchors:
    def test_generate_toc_hiragana_heading_preserves_anchor(self) -> None:
        text = "# はじめに"
        result = generate_toc(text)
        assert result.headings[0].anchor == "はじめに"

    def test_generate_toc_katakana_heading_preserves_anchor(self) -> None:
        text = "# カタカナ"
        result = generate_toc(text)
        assert result.headings[0].anchor == "カタカナ"

    def test_generate_toc_kanji_heading_preserves_anchor(self) -> None:
        text = "# 漢字見出し"
        result = generate_toc(text)
        assert result.headings[0].anchor == "漢字見出し"


class TestSkippedLevels:
    def test_generate_toc_h2_and_h4_only_returns_relative_indent_with_depth_gap(
        self,
    ) -> None:
        text = "## Intro\n#### Detail"
        result = generate_toc(text, min_level=1, max_level=6)
        assert len(result.headings) == 2
        expected_md = "- [Intro](#intro)\n    - [Detail](#detail)"
        assert result.markdown == expected_md


class TestAtxClosing:
    def test_generate_toc_atx_trailing_hashes_removed_in_text_anchor_markdown(
        self,
    ) -> None:
        text = "## Heading ##"
        result = generate_toc(text, min_level=1, max_level=6)
        heading = result.headings[0]
        assert heading.text == "Heading"
        assert heading.anchor == "heading"
        assert result.markdown == "- [Heading](#heading)"


class TestJapaneseDuplicateAnchors:
    def test_generate_toc_japanese_duplicate_headings_returns_numbered_anchors_and_markdown(
        self,
    ) -> None:
        text = "# はじめに\n## インストール\n# はじめに"
        result = generate_toc(text)
        assert result.headings[0].anchor == "はじめに"
        assert result.headings[2].anchor == "はじめに-1"
        expected_md = (
            "- [はじめに](#はじめに)\n"
            "  - [インストール](#インストール)\n"
            "- [はじめに](#はじめに-1)"
        )
        assert result.markdown == expected_md
