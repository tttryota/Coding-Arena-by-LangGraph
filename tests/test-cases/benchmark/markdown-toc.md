---
feature: markdown-toc
spec: docs/spec/benchmark/markdown-toc.md
status: approved
---

## テストケース（実装順）

各テストは generate_toc() の戻り値 TocResult の headings（見出し一覧）と markdown（目次テキスト）の両方を検証すること。

### Phase 1: 最小骨格

1. 空文字列を渡すと、headings が空リストで、markdown が空文字列で返る
2. 見出しのない本文（例: `"本文のみ\n改行あり"`）を渡すと、headings が空リストで、markdown が空文字列で返る
3. `"# Hello World"` を渡すと、headings が1件で text="Hello World", level=1, anchor="hello-world"、markdown が `"- [Hello World](#hello-world)"` で返る

### Phase 2: コアロジック

4. `"# Title\n## Section\n### Sub\n## Another"` を渡すと、headings が4件で各 level が正しく、markdown のインデントが `""`, `"  "`, `"    "`, `"  "` の順になる
5. バッククォート3つで囲まれたコードブロック内の `# comment` 行が headings に含まれない。コードブロック外の見出しのみ抽出される
6. チルダ3つで囲まれたコードブロック内の行が headings に含まれない。チルダフェンスとバッククォートフェンスは互いに閉じない
7. `"# Section\n# Section\n# Section"` を渡すと、3件の headings の anchor がそれぞれ "section", "section-1", "section-2" となり、markdown の各行のリンクも対応するアンカーを持つ
8. `"# H1\n## H2\n### H3\n#### H4"` に min_level=2, max_level=3 を指定すると、headings が2件（H2, H3のみ）で、markdown のインデントが H2=深さ0、H3=深さ1 になる

### Phase 3: エッジケース

9. `"# **Bold** and \`code\` and [link](http://example.com)"` を渡すと、headings の text が "Bold and code and link"、anchor が "bold-and-code-and-link"、markdown のリンクテキストも装飾なしになる
10. `"# foo_bar_baz"` を渡すと、headings の text が "foo_bar_baz"（アンダースコア保持）、anchor が "foo_bar_baz" で返る
11. ひらがなの見出し `"# はじめに"` を渡すと anchor が "はじめに" で返る
12. カタカナの見出し `"# セットアップ"` を渡すと anchor が "セットアップ" で返る
13. 漢字の見出し `"# 設定方法"` を渡すと anchor が "設定方法" で返る
14. `"## Overview\n#### Detail"` に max_level=6 を指定すると、headings が2件で、markdown のインデントが Overview=深さ0、Detail=深さ2（レベル差4-2=2）になる
15. `"## Heading ##"` を渡すと、headings の text が "Heading"（末尾 ## 除去）、anchor が "heading"、markdown が `"- [Heading](#heading)"` で返る
16. `"# はじめに\n## 概要\n# はじめに"` を渡すと、3件目の anchor が "はじめに-1" になり、markdown の3行目のリンクが `"[はじめに](#はじめに-1)"` を含む
