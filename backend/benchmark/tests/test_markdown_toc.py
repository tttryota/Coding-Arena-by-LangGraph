"""markdown_toc モジュールのテスト."""

from __future__ import annotations

from benchmark.markdown_toc import generate_toc


class TestGenerateToc:
    """generate_toc 関数のテスト."""

    def test_generate_toc_empty_string_returns_empty(self) -> None:
        """検証: 空文字列を渡した場合.

        期待: headings が空、markdown が空文字列で返る
        """
        result = generate_toc("")

        assert len(result.headings) == 0
        assert result.markdown == ""

    def test_generate_toc_no_headings_body_returns_empty(self) -> None:
        """検証: 見出しのない本文のみを渡した場合.

        期待: headings が空、markdown が空文字列で返る
        """
        result = generate_toc("本文テキストのみ\n改行もある")

        assert len(result.headings) == 0
        assert result.markdown == ""

    def test_generate_toc_single_h1_returns_correct_fields(self) -> None:
        """検証: H1 が1つだけの場合.

        期待: text="はじめに", level=1, anchor="はじめに", markdown="- [はじめに](#はじめに)"
        """
        result = generate_toc("# はじめに")

        assert len(result.headings) == 1
        h = result.headings[0]
        assert h.text == "はじめに"
        assert h.level == 1
        assert h.anchor == "はじめに"
        assert result.markdown == "- [はじめに](#はじめに)"

    def test_generate_toc_mixed_h1_h2_h3_returns_correct_hierarchy(self) -> None:
        """検証: H1, H2, H3 が混在する場合.

        期待: 4件の headings が返り、インデントが H1=0, H2=2, H3=4 スペースで正しい
        """
        text = "# Title\n## Section\n### Sub\n## Section2"

        result = generate_toc(text)

        assert len(result.headings) == 4
        expected = (
            "- [Title](#title)\n"
            "  - [Section](#section)\n"
            "    - [Sub](#sub)\n"
            "  - [Section2](#section2)"
        )
        assert result.markdown == expected

    def test_generate_toc_backtick_code_block_skips_headings(self) -> None:
        """検証: バッククォートコードブロック内に見出し行がある場合.

        期待: コードブロック内の # 行は無視され、前後の見出しのみ抽出される
        """
        text = "# Real\n```\n# Fake\n```\n# Also Real"

        result = generate_toc(text)

        assert len(result.headings) == 2
        assert result.headings[0].text == "Real"
        assert result.headings[1].text == "Also Real"

    def test_generate_toc_tilde_block_skips_and_no_cross_close(self) -> None:
        """検証: チルダコードブロック内はスキップし、バッククォートでは閉じない場合.

        期待: チルダブロック内の見出しは無視され、ブロック外の見出しのみ抽出される
        """
        text = "# Before\n~~~\n# InTilde\n```\n# StillInTilde\n~~~\n# After"

        result = generate_toc(text)

        assert len(result.headings) == 2
        assert result.headings[0].text == "Before"
        assert result.headings[1].text == "After"

    def test_generate_toc_duplicate_headings_appends_anchor_suffix(self) -> None:
        """検証: 同名見出しが3つある場合.

        期待: anchor が section, section-1, section-2 で、markdown も対応する付番リンク
        """
        text = "# Section\n# Section\n# Section"

        result = generate_toc(text)

        assert result.headings[0].anchor == "section"
        assert result.headings[1].anchor == "section-1"
        assert result.headings[2].anchor == "section-2"
        expected = (
            "- [Section](#section)\n- [Section](#section-1)\n- [Section](#section-2)"
        )
        assert result.markdown == expected

    def test_generate_toc_min_max_level_filters_h2_h3_only(self) -> None:
        """検証: min_level=2, max_level=3 を指定した場合.

        期待: H2, H3 のみ抽出され、H2 が深さ0 のインデントで出力される
        """
        text = "# H1\n## H2\n### H3\n# H1b"

        result = generate_toc(text, min_level=2, max_level=3)

        assert len(result.headings) == 2
        assert result.headings[0].level == 2
        assert result.headings[1].level == 3
        expected = "- [H2](#h2)\n  - [H3](#h3)"
        assert result.markdown == expected

    def test_generate_toc_bold_code_link_in_heading_strips_decorations(
        self,
    ) -> None:
        """検証: **bold**, `code`, [link](url) を含む見出しの場合.

        期待: text="bold and code and link", anchor="bold-and-code-and-link"
        """
        text = "# **bold** and `code` and [link](http://example.com)"

        result = generate_toc(text)

        assert result.headings[0].text == "bold and code and link"
        assert result.headings[0].anchor == "bold-and-code-and-link"
        assert result.markdown == "- [bold and code and link](#bold-and-code-and-link)"

    def test_generate_toc_word_internal_underscore_preserved(self) -> None:
        """検証: foo_bar_baz のように単語内にアンダースコアがある場合.

        期待: text="foo_bar_baz", anchor="foo_bar_baz" でアンダースコアが保持される
        """
        result = generate_toc("# foo_bar_baz")

        assert result.headings[0].text == "foo_bar_baz"
        assert result.headings[0].anchor == "foo_bar_baz"

    def test_generate_toc_hiragana_anchor_preserved(self) -> None:
        """検証: ひらがなの見出しの場合.

        期待: anchor="はじめに" でひらがながそのまま保持される
        """
        result = generate_toc("# はじめに")

        assert result.headings[0].anchor == "はじめに"

    def test_generate_toc_katakana_anchor_preserved(self) -> None:
        """検証: カタカナの見出しの場合.

        期待: anchor="インストール" でカタカナがそのまま保持される
        """
        result = generate_toc("# インストール")

        assert result.headings[0].anchor == "インストール"

    def test_generate_toc_kanji_anchor_preserved(self) -> None:
        """検証: 漢字の見出しの場合.

        期待: anchor="設定方法" で漢字がそのまま保持される
        """
        result = generate_toc("# 設定方法")

        assert result.headings[0].anchor == "設定方法"

    def test_generate_toc_h2_h4_only_relative_indent_correct(self) -> None:
        """検証: H2 と H4 のみで見出しレベルが飛んでいる場合.

        期待: H2 が深さ0、H4 が深さ2 (4スペースインデント) で出力される
        """
        text = "## Section\n#### Detail"

        result = generate_toc(text, max_level=4)

        expected = "- [Section](#section)\n    - [Detail](#detail)"
        assert result.markdown == expected

    def test_generate_toc_atx_closing_hashes_removed(self) -> None:
        """検証: ATX 末尾クロージング (## Heading ##) がある場合.

        期待: text="Heading", anchor="heading" で末尾の # が除去される
        """
        result = generate_toc("## Heading ##")

        assert result.headings[0].text == "Heading"
        assert result.headings[0].anchor == "heading"
        assert result.markdown == "- [Heading](#heading)"

    def test_generate_toc_japanese_duplicate_appends_anchor_suffix(self) -> None:
        """検証: 日本語の重複見出しがある場合.

        期待: 2つ目の "はじめに" の anchor が "はじめに-1" で、markdown も対応
        """
        text = "# はじめに\n## 概要\n# はじめに"

        result = generate_toc(text)

        assert result.headings[0].anchor == "はじめに"
        assert result.headings[2].anchor == "はじめに-1"
        expected = (
            "- [はじめに](#はじめに)\n  - [概要](#概要)\n- [はじめに](#はじめに-1)"
        )
        assert result.markdown == expected
