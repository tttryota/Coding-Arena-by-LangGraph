---
feature: markdown-toc
spec: docs/spec/benchmark/markdown-toc.md
status: approved
---

## テストケース（実装順）

### Phase 1: 最小骨格（基本動作 — 全フィールド検証）

1. 空文字列を渡すと、headings が空リストで、markdown が空文字列で返る
2. 見出しのない本文（例: `"本文のみ\n改行あり"`）を渡すと、headings が空リストで、markdown が空文字列で返る
3. `"# Hello World"` を渡すと、headings が1件で text="Hello World", level=1, anchor="hello-world"、markdown が `"- [Hello World](#hello-world)"` で返る

### Phase 2: コアロジック

4. （出力形式）`"# Title\n## Section\n### Sub\n## Another"` を渡すと、headings が4件で各 level が正しく、markdown のインデントが `""`, `"  "`, `"    "`, `"  "` の順になる
5. （フィルタ）バッククォート3つで囲まれたコードブロック内の `# comment` 行が headings に含まれない。コードブロック外の見出しのみ抽出される
6. （フィルタ）チルダ3つで囲まれたコードブロック内の行が headings に含まれない。チルダフェンスとバッククォートフェンスは互いに閉じない
7. （変換ロジック）`"# Section\n# Section\n# Section"` を渡すと、3件の headings の anchor がそれぞれ "section", "section-1", "section-2" となり、markdown の各行のリンクも対応するアンカーを持つ
8. （フィルタ）`"# H1\n## H2\n### H3\n#### H4"` に min_level=2, max_level=3 を指定すると、headings が2件（H2, H3のみ）で、markdown のインデントが H2=深さ0、H3=深さ1 になる

### Phase 3: エッジケース

9. （変換ロジック）`"# **Bold** and \`code\` and [link](http://example.com)"` を渡すと、headings の text が "Bold and code and link"、anchor が "bold-and-code-and-link"
10. （変換ロジック）`"# foo_bar_baz"` を渡すと、headings の text が "foo_bar_baz"（アンダースコア保持）、anchor が "foo_bar_baz"
11. （変換ロジック）ひらがなの見出し `"# はじめに"` を渡すと anchor が "はじめに"
12. （変換ロジック）カタカナの見出し `"# セットアップ"` を渡すと anchor が "セットアップ"
13. （変換ロジック）漢字の見出し `"# 設定方法"` を渡すと anchor が "設定方法"
14. （出力形式）`"## Overview\n#### Detail"` に max_level=6 を指定すると、headings が2件で、markdown のインデントが Overview=深さ0、Detail=深さ2（レベル差4-2=2）
15. （変換ロジック）`"## Heading ##"` を渡すと、headings の text が "Heading"（末尾 ## 除去）、anchor が "heading"、markdown が `"- [Heading](#heading)"`
16. （変換ロジック）`"# はじめに\n## 概要\n# はじめに"` を渡すと、3件目の anchor が "はじめに-1" で、markdown の3行目のリンクが `"[はじめに](#はじめに-1)"` を含む
17. （境界条件）未閉鎖コードフェンス ``"# Before\n```\n# Ignored"`` を渡すと、headings は "Before" の1件だけで、フェンス開始以降の見出しは無視される
18. （境界条件）`min_level=4, max_level=3` を指定すると、headings が空で markdown が空文字列になる
19. （境界条件）`" # Not Heading\n# Actual"` を渡すと、先頭スペース付き行は無視され、"Actual" だけが headings に入る
20. （境界条件）`"####### Too Many\n# Valid"` を渡すと、`####### Too Many` は見出しとして認識されず、"Valid" だけが headings に入る
21. （境界条件）`"## !!!"` を渡すと、headings の text が "!!!"、anchor が空文字列で、markdown が `"- [!!!](#)"` になる
22. （既知制限）`"# [text](https://example.com/foo_(bar))"` を渡すと、最初の `)` でリンクが閉じた扱いになり、text が `"text)"`、anchor が `"text"` になる

### Phase 4: ハッピーパス（統合 — 全フィールド検証）

23. （統合）仕様書の具体例全文を渡すと、headings が6件で各 text/level/anchor が仕様どおり、markdown も spec 記載の出力と一致する
