"""markdown_toc モジュールのテスト."""

from backend.benchmark.markdown_toc import generate_toc


class TestGenerateTocEmptyAndNoHeadings:
    """空入力・見出しなし入力."""

    def test_generate_toc_empty_string_returns_empty_headings_and_markdown(
        self,
    ) -> None:
        result = generate_toc("")

        assert result.headings == []
        assert result.markdown == ""

    def test_generate_toc_body_only_returns_empty_headings_and_markdown(
        self,
    ) -> None:
        result = generate_toc("本文テキストのみ\n改行もある\nさらに続く")

        assert result.headings == []
        assert result.markdown == ""


class TestGenerateTocSingleHeading:
    """単一見出しの抽出."""

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


class TestGenerateTocMultipleLevels:
    """複数レベル見出しの階層."""

    def test_generate_toc_h1_h2_h3_mixed_returns_four_headings_with_correct_indent(
        self,
    ) -> None:
        text = "# Title\n## Section A\n## Section B\n### Subsection"

        result = generate_toc(text)

        assert len(result.headings) == 4
        expected_markdown = (
            "- [Title](#title)\n"
            "  - [Section A](#section-a)\n"
            "  - [Section B](#section-b)\n"
            "    - [Subsection](#subsection)"
        )
        assert result.markdown == expected_markdown


class TestGenerateTocCodeBlock:
    """コードブロック内の見出しスキップ."""

    def test_generate_toc_backtick_fence_skips_heading_inside(self) -> None:
        text = "# Real\n```\n# Fake\n```\n# Also Real"

        result = generate_toc(text)

        assert len(result.headings) == 2
        assert result.headings[0].text == "Real"
        assert result.headings[1].text == "Also Real"

    def test_generate_toc_tilde_fence_skips_and_backtick_does_not_close_tilde(
        self,
    ) -> None:
        text = "# Before\n~~~\n# Inside Tilde\n```\n# Still Inside\n~~~\n# After"

        result = generate_toc(text)

        assert len(result.headings) == 2
        assert result.headings[0].text == "Before"
        assert result.headings[1].text == "After"


class TestGenerateTocDuplicateAnchors:
    """重複アンカーの付番."""

    def test_generate_toc_three_same_headings_returns_numbered_anchors_and_markdown(
        self,
    ) -> None:
        text = "# Section\n# Section\n# Section"

        result = generate_toc(text)

        assert result.headings[0].anchor == "section"
        assert result.headings[1].anchor == "section-1"
        assert result.headings[2].anchor == "section-2"
        expected_markdown = (
            "- [Section](#section)\n- [Section](#section-1)\n- [Section](#section-2)"
        )
        assert result.markdown == expected_markdown


class TestGenerateTocLevelFilter:
    """min_level / max_level フィルタ."""

    def test_generate_toc_min2_max3_extracts_h2_h3_with_correct_indent(
        self,
    ) -> None:
        text = "# H1\n## H2\n### H3\n#### H4"

        result = generate_toc(text, min_level=2, max_level=3)

        assert len(result.headings) == 2
        assert result.headings[0].text == "H2"
        assert result.headings[0].level == 2
        assert result.headings[1].text == "H3"
        assert result.headings[1].level == 3
        expected_markdown = "- [H2](#h2)\n  - [H3](#h3)"
        assert result.markdown == expected_markdown


class TestGenerateTocDecorationRemoval:
    """Markdown 装飾の除去."""

    def test_generate_toc_bold_code_link_removed_in_text_anchor_markdown(
        self,
    ) -> None:
        text = "# **bold** and `code` and [link](http://example.com)"

        result = generate_toc(text)

        heading = result.headings[0]
        assert heading.text == "bold and code and link"
        assert heading.anchor == "bold-and-code-and-link"
        assert result.markdown == "- [bold and code and link](#bold-and-code-and-link)"

    def test_generate_toc_word_internal_underscore_preserved_in_text_and_anchor(
        self,
    ) -> None:
        text = "# foo_bar_baz"

        result = generate_toc(text)

        heading = result.headings[0]
        assert heading.text == "foo_bar_baz"
        assert heading.anchor == "foo_bar_baz"


class TestGenerateTocJapaneseSlug:
    """日本語見出しのスラッグ生成."""

    def test_generate_toc_hiragana_heading_anchor_preserved(self) -> None:
        result = generate_toc("# はじめに")

        assert result.headings[0].anchor == "はじめに"

    def test_generate_toc_katakana_heading_anchor_preserved(self) -> None:
        result = generate_toc("# カタカナ")

        assert result.headings[0].anchor == "カタカナ"

    def test_generate_toc_kanji_heading_anchor_preserved(self) -> None:
        result = generate_toc("# 漢字")

        assert result.headings[0].anchor == "漢字"


class TestGenerateTocRelativeIndent:
    """見出しレベルが飛んでいる場合の相対インデント."""

    def test_generate_toc_h2_h4_only_returns_depth_difference_of_two(self) -> None:
        text = "## Level2\n#### Level4"

        result = generate_toc(text, min_level=1, max_level=6)

        expected_markdown = "- [Level2](#level2)\n    - [Level4](#level4)"
        assert result.markdown == expected_markdown


class TestGenerateTocAtxClosing:
    """ATX 末尾クロージングの除去."""

    def test_generate_toc_trailing_hashes_removed_in_text_anchor_markdown(
        self,
    ) -> None:
        text = "## Heading ##"

        result = generate_toc(text)

        heading = result.headings[0]
        assert heading.text == "Heading"
        assert heading.anchor == "heading"
        assert result.markdown == "- [Heading](#heading)"


class TestGenerateTocJapaneseDuplicate:
    """日本語重複見出しの付番."""

    def test_generate_toc_japanese_duplicate_returns_numbered_anchor_and_markdown(
        self,
    ) -> None:
        text = "# はじめに\n# はじめに"

        result = generate_toc(text)

        assert result.headings[0].anchor == "はじめに"
        assert result.headings[1].anchor == "はじめに-1"
        expected_markdown = "- [はじめに](#はじめに)\n- [はじめに](#はじめに-1)"
        assert result.markdown == expected_markdown
