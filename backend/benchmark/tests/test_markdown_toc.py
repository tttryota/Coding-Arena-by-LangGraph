"""markdown_toc モジュールのテスト."""

from textwrap import dedent

from backend.benchmark.markdown_toc import (
    TableOfContentsHeading,
    generate_table_of_contents,
)


class TestGenerateTableOfContents:
    """generate_table_of_contents 関数の振る舞いを検証する."""

    def test_generate_table_of_contents_empty_string_empty_result(self) -> None:
        """検証: 空文字列を渡した場合.

        期待: headings が空、markdown が空文字列で返る.
        """
        result = generate_table_of_contents("")

        assert len(result.headings) == 0
        assert result.markdown == ""

    def test_generate_table_of_contents_no_headings_empty_result(self) -> None:
        """検証: 見出しを含まない本文のみの場合.

        期待: headings が空、markdown が空文字列で返る.
        """
        result = generate_table_of_contents("本文テキストのみ。見出しなし。\n次の行。")

        assert len(result.headings) == 0
        assert result.markdown == ""

    def test_generate_table_of_contents_single_h1_correct_fields(self) -> None:
        """検証: H1 が1つだけの場合.

        期待: text="Hello World", level=1, anchor="hello-world",
              markdown="- [Hello World](#hello-world)" が返る.
        """
        result = generate_table_of_contents("# Hello World")

        assert len(result.headings) == 1
        heading = result.headings[0]
        assert heading.text == "Hello World"
        assert heading.level == 1
        assert heading.anchor == "hello-world"
        assert result.markdown == "- [Hello World](#hello-world)"

    def test_generate_table_of_contents_mixed_levels_four_headings_with_indent(
        self,
    ) -> None:
        """検証: H1, H2, H3 が混在し計4件の場合.

        期待: 4件の headings とレベルに応じたインデント階層の markdown が返る.
        """
        text = dedent("""\
            # Title
            ## Section
            ### Sub
            ## Another
        """)
        result = generate_table_of_contents(text)

        assert len(result.headings) == 4
        assert result.headings[0] == TableOfContentsHeading(
            text="Title",
            level=1,
            anchor="title",
        )
        assert result.headings[1] == TableOfContentsHeading(
            text="Section",
            level=2,
            anchor="section",
        )
        assert result.headings[2] == TableOfContentsHeading(
            text="Sub",
            level=3,
            anchor="sub",
        )
        assert result.headings[3] == TableOfContentsHeading(
            text="Another",
            level=2,
            anchor="another",
        )
        expected_md = dedent("""\
            - [Title](#title)
              - [Section](#section)
                - [Sub](#sub)
              - [Another](#another)""")
        assert result.markdown == expected_md

    def test_generate_table_of_contents_backtick_code_block_skipped(self) -> None:
        """検証: バッククォートコードブロック内に # 行がある場合.

        期待: コードブロック内の行は見出しとして認識されない.
        """
        text = dedent("""\
            # Before

            ```
            # Inside Code Block
            ```

            # After
        """)
        result = generate_table_of_contents(text)

        assert len(result.headings) == 2
        assert result.headings[0].text == "Before"
        assert result.headings[1].text == "After"
        expected_md = "- [Before](#before)\n- [After](#after)"
        assert result.markdown == expected_md

    def test_generate_table_of_contents_tilde_code_block_skipped_not_closed_by_backtick(
        self,
    ) -> None:
        """検証: チルダコードブロック内はスキップされ、バッククォートでは閉じない場合.

        期待: チルダフェンス内の行は見出しとして認識されず、
              バッククォートフェンスがチルダフェンスを閉じない.
        """
        text = dedent("""\
            # Before

            ~~~
            # Inside Tilde
            ```
            # Still Inside
            ~~~

            # After
        """)
        result = generate_table_of_contents(text)

        assert len(result.headings) == 2
        assert result.headings[0].text == "Before"
        assert result.headings[1].text == "After"
        expected_md = "- [Before](#before)\n- [After](#after)"
        assert result.markdown == expected_md

    def test_generate_table_of_contents_duplicate_names_numbered_anchors(self) -> None:
        """検証: 同名見出しが3つある場合.

        期待: anchor が section, section-1, section-2 と付番され、
              markdown のリンク先も対応する.
        """
        text = dedent("""\
            # Section
            # Section
            # Section
        """)
        result = generate_table_of_contents(text)

        assert len(result.headings) == 3
        assert result.headings[0].anchor == "section"
        assert result.headings[1].anchor == "section-1"
        assert result.headings[2].anchor == "section-2"
        expected_md = dedent("""\
            - [Section](#section)
            - [Section](#section-1)
            - [Section](#section-2)""")
        assert result.markdown == expected_md

    def test_generate_table_of_contents_min_max_level_filter_h2_h3_only(self) -> None:
        """検証: min_level=2, max_level=3 を指定した場合.

        期待: H2, H3 のみ抽出され、H4 は max_level=3 により除外される.
        """
        text = dedent("""\
            # H1
            ## H2
            ### H3
            #### H4
        """)
        result = generate_table_of_contents(text, min_level=2, max_level=3)

        assert len(result.headings) == 2
        assert result.headings[0].text == "H2"
        assert result.headings[1].text == "H3"
        expected_md = dedent("""\
            - [H2](#h2)
              - [H3](#h3)""")
        assert result.markdown == expected_md

    def test_generate_table_of_contents_bold_code_link_stripped(self) -> None:
        """検証: 見出しに **Bold**, `code`, [link](url) が含まれる場合.

        期待: 装飾が除去され text="Bold and code and link",
              anchor="bold-and-code-and-link" が返る.
        """
        text = "# **Bold** and `code` and [link](http://example.com)"
        result = generate_table_of_contents(text)

        heading = result.headings[0]
        assert heading.text == "Bold and code and link"
        assert heading.anchor == "bold-and-code-and-link"
        assert result.markdown == "- [Bold and code and link](#bold-and-code-and-link)"

    def test_generate_table_of_contents_word_internal_underscore_preserved(
        self,
    ) -> None:
        """検証: foo_bar_baz のように単語内にアンダースコアがある場合.

        期待: アンダースコアがイタリック除去されず保持され、
              text="foo_bar_baz", anchor="foo_bar_baz" が返る.
        """
        text = "# foo_bar_baz"
        result = generate_table_of_contents(text)

        heading = result.headings[0]
        assert heading.text == "foo_bar_baz"
        assert heading.anchor == "foo_bar_baz"

    def test_generate_table_of_contents_hiragana_anchor_preserved(self) -> None:
        """検証: ひらがなのみの見出しの場合.

        期待: anchor にひらがながそのまま保持される.
        """
        result = generate_table_of_contents("# はじめに")

        heading = result.headings[0]
        assert heading.text == "はじめに"
        assert heading.anchor == "はじめに"

    def test_generate_table_of_contents_katakana_anchor_preserved(self) -> None:
        """検証: カタカナのみの見出しの場合.

        期待: anchor にカタカナがそのまま保持される.
        """
        result = generate_table_of_contents("# セットアップ")

        heading = result.headings[0]
        assert heading.text == "セットアップ"
        assert heading.anchor == "セットアップ"

    def test_generate_table_of_contents_kanji_anchor_preserved(self) -> None:
        """検証: 漢字のみの見出しの場合.

        期待: anchor に漢字がそのまま保持される.
        """
        result = generate_table_of_contents("# 設定方法")

        heading = result.headings[0]
        assert heading.text == "設定方法"
        assert heading.anchor == "設定方法"

    def test_generate_table_of_contents_h2_h4_only_relative_indent(self) -> None:
        """検証: H2 と H4 のみでレベルが飛んでいる場合.

        期待: H2 が深さ0、H4 が深さ2(スペース4つ)の相対インデントで出力される.
        """
        text = dedent("""\
            ## Overview
            #### Detail
        """)
        result = generate_table_of_contents(text, max_level=6)

        assert len(result.headings) == 2
        expected_md = "- [Overview](#overview)\n    - [Detail](#detail)"
        assert result.markdown == expected_md

    def test_generate_table_of_contents_atx_closing_removed(self) -> None:
        """検証: ATX 末尾クロージング ## Heading ## がある場合.

        期待: 末尾の # が除去され text="Heading", anchor="heading" が返る.
        """
        text = "## Heading ##"
        result = generate_table_of_contents(text)

        heading = result.headings[0]
        assert heading.text == "Heading"
        assert heading.anchor == "heading"
        assert result.markdown == "- [Heading](#heading)"

    def test_generate_table_of_contents_japanese_duplicates_numbered_anchors(
        self,
    ) -> None:
        """検証: 日本語の重複見出しがある場合.

        期待: 重複しない見出しが間に挟まっても付番が正しく動作し、
              3件目の anchor が はじめに-1 となる.
        """
        text = dedent("""\
            # はじめに
            ## 概要
            # はじめに
        """)
        result = generate_table_of_contents(text)

        assert len(result.headings) == 3
        assert result.headings[0].anchor == "はじめに"
        assert result.headings[1].anchor == "概要"
        assert result.headings[2].anchor == "はじめに-1"
        expected_md = dedent("""\
            - [はじめに](#はじめに)
              - [概要](#概要)
            - [はじめに](#はじめに-1)""")
        assert result.markdown == expected_md

    def test_generate_table_of_contents_spec_example_full_integration(self) -> None:
        """検証: 仕様書の具体例を入力とした統合テスト.

        期待: headings が6件で各 text/level/anchor が正しく、
              markdown が仕様書記載の出力と一致する.
        """
        text = dedent("""\
            # はじめに

            本文テキスト

            ## インストール

            手順の説明

            ## 使い方

            ### 基本的な使い方

            ### 応用例

            ## はじめに""")
        result = generate_table_of_contents(text, min_level=1, max_level=3)

        assert len(result.headings) == 6
        assert result.headings[0] == TableOfContentsHeading(
            text="はじめに",
            level=1,
            anchor="はじめに",
        )
        assert result.headings[1] == TableOfContentsHeading(
            text="インストール",
            level=2,
            anchor="インストール",
        )
        assert result.headings[2] == TableOfContentsHeading(
            text="使い方",
            level=2,
            anchor="使い方",
        )
        assert result.headings[3] == TableOfContentsHeading(
            text="基本的な使い方",
            level=3,
            anchor="基本的な使い方",
        )
        assert result.headings[4] == TableOfContentsHeading(
            text="応用例",
            level=3,
            anchor="応用例",
        )
        assert result.headings[5] == TableOfContentsHeading(
            text="はじめに",
            level=2,
            anchor="はじめに-1",
        )
        expected_md = dedent("""\
            - [はじめに](#はじめに)
              - [インストール](#インストール)
              - [使い方](#使い方)
                - [基本的な使い方](#基本的な使い方)
                - [応用例](#応用例)
              - [はじめに](#はじめに-1)""")
        assert result.markdown == expected_md
