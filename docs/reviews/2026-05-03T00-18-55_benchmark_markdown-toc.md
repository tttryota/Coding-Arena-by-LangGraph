# タスクレポート: benchmark/markdown-toc

**実行日**: 2026-05-03T00-18-55
**スコープ**: benchmark/markdown-toc
**結果**: 完了
**レビューサイクル数**: 8回
**修正件数**: 4件

## 対象テストケース
1. 空文字列 → headings空リスト、markdown空文字列
2. 見出しなし本文 → headings空リスト、markdown空文字列
3. H1が1つ → text/level/anchor/markdownが正しい
4. H1,H2,H3混在 → 4件のheadingsとインデント階層が正しい
5. バッククォートコードブロック内はスキップ
6. チルダコードブロック内はスキップ、バッククォートとチルダは互いに閉じない
7. 同名見出し3つ → anchor付番 section, section-1, section-2、markdownも対応
8. min_level=2,max_level=3 → H2,H3のみ抽出、インデント正しい
9. **bold**,`code`,[link](url)除去 → text/anchor/markdownが正しい
10. foo_bar_baz → アンダースコア保持、text/anchor正しい
11. ひらがな見出し → anchor保持
12. カタカナ見出し → anchor保持
13. 漢字見出し → anchor保持
14. H2とH4のみ → 相対インデント（深さ差2）が正しい
15. ATX末尾クロージング除去 → text/anchor/markdown正しい
16. 日本語重複見出し → anchor付番 はじめに-1、markdownも対応

## TDD サイクル
- テスト生成後、既に GREEN（実装生成スキップ）

---

## レビュー詳細

### test_self_quality

- [minor] backend/benchmark/tests/test_markdown_toc.py:100 — test_generate_table_of_contents_min_level_exceeds_max_level_returns_empty はテストケース文書の17件のいずれにも対応しない独自追加テスト。min_level > max_level の境界条件は仕様書に記載があるが、テストケース文書には含まれていない。テストケースの追加はdesignフェーズの責務であり、テストコード側で独自に追加すべきではない。このテストを削除し、必要であればテストケース文書に追加した上で再実装する。

**判断**: テストケース文書に定義されていない独自テスト(`min_level > max_level`)をテストコード側で勝手に追加していたため、designフェーズとimplフェーズの責務分離の原則に従い削除した。境界条件のテストが必要なら、まずテストケース文書に追加してからテストコードに反映すべきという判断。併せてフォーマット修正（行長・未使用import削除）も適用された。

<details><summary>修正 diff</summary>

```diff
diff --git a/backend/benchmark/tests/test_markdown_toc.py b/backend/benchmark/tests/test_markdown_toc.py
index 5d44b34..d02962b 100644
--- a/backend/benchmark/tests/test_markdown_toc.py
+++ b/backend/benchmark/tests/test_markdown_toc.py
@@ -1,6 +1,5 @@
 """markdown_toc モジュールのテスト."""
 
-import pytest
 from textwrap import dedent
 
 from backend.benchmark.markdown_toc import (
@@ -47,7 +46,9 @@ class TestGenerateTableOfContents:
         assert heading.anchor == "hello-world"
         assert result.markdown == "- [Hello World](#hello-world)"
 
-    def test_generate_table_of_contents_mixed_levels_four_headings_with_indent(self) -> None:
+    def test_generate_table_of_contents_mixed_levels_four_headings_with_indent(
+        self,
+    ) -> None:
         """検証: H1, H2, H3 が混在し計4件の場合.
 
         期待: 4件の headings とレベルに応じたインデント階層の markdown が返る.
@@ -61,7 +62,11 @@ class TestGenerateTableOfContents:
         result = generate_table_of_contents(text)
 
         assert len(result.headings) == 4
-        assert result.headings[0] == TableOfContentsHeading(text="Title", level=1, anchor="title")
+        assert result.headings[0] == TableOfContentsHeading(
+            text="Title",
+            level=1,
```
</details>

指摘なし（2回目で通過）

### test_external

指摘なし（1回目で通過）

### self_criteria

指摘なし（1回目で通過）

### self_quality

指摘なし（1回目で通過）

### impl_external

- [major] /Users/tsuryoryo/Desktop/repo/obsidian/backend/benchmark/markdown_toc.py:156 — _render_markdown が heading.text を Markdown リンクラベルにそのまま埋め込んでおり、`[` や `]` を含む有効な見出しで出力 Markdown が壊れる。たとえば `# a]b` は `- [a]b](#ab)` になり、仕様が要求する `- [見出しテキスト](#アンカー)` 形式の1件のリンクとして解釈されない。結果として、構造化データ `headings` は正しくても、利用側が使う `markdown` が壊れて目次リンクとして機能しない。リンクラベルへ埋め込む直前に Markdown の特殊文字をエスケープし、少なくとも `\`、`[`、`]` を安全に出力するよう修正すべき。
- [minor] /Users/tsuryoryo/Desktop/repo/obsidian/backend/benchmark/markdown_toc.py:8 — 見出し判定と ATX 末尾クロージング除去に `\s` を使っているため、仕様が要求する「スペース」をタブなど他の空白文字まで許容してしまう。実際に `#\tTabbed` は見出しとして抽出され、`## Heading\t##` も末尾クロージングとして処理されるが、仕様では `#` の直後やクロージング前に必要なのはスペースであり、タブ許容は定義されていない。これにより、ベンチマークの挙動が承認済み仕様とずれる。`_HEADING_PATTERN` と `_ATX_CLOSING_PATTERN` の空白条件を literal space ベースに変更し、仕様どおり半角スペースのみを受け付けるべき。

**判断**: **major指摘（リンクラベル破損）:** 見出しテキストに `[` や `]` が含まれるとMarkdownリンク構文が壊れるため、埋め込み前に `\[` `\]` `\\` へエスケープする関数を追加した。

**minor指摘（空白文字の許容範囲）:** 仕様では `#` の後に必要なのは半角スペースのみだが、`\s` だとタブ等も許容してしまうため、正規表現をリテラルスペース（` +`）に変更して仕様準拠とした。

<details><summary>修正 diff</summary>

```diff
diff --git a/backend/benchmark/markdown_toc.py b/backend/benchmark/markdown_toc.py
index d3e3fea..7fc151f 100644
--- a/backend/benchmark/markdown_toc.py
+++ b/backend/benchmark/markdown_toc.py
@@ -5,9 +5,9 @@ from __future__ import annotations
 import re
 from dataclasses import dataclass
 
-_HEADING_PATTERN = re.compile(r"^(#{1,6})\s+(.*)$")
+_HEADING_PATTERN = re.compile(r"^(#{1,6}) +(.*)$")
 _FENCE_PATTERN = re.compile(r"^(`{3,}|~{3,})")
-_ATX_CLOSING_PATTERN = re.compile(r"\s+#+\s*$")
+_ATX_CLOSING_PATTERN = re.compile(r" +#+ *$")
 
 _LINK_PATTERN = re.compile(r"\[([^\]]*?)\]\([^)]*?\)")
 _CODE_PATTERN = re.compile(r"`([^`]*?)`")
@@ -16,6 +16,8 @@ _BOLD_UNDERSCORE_PATTERN = re.compile(r"(?<![A-Za-z0-9_])__(.+?)__(?![A-Za-z0-9_
 _ITALIC_ASTERISK_PATTERN = re.compile(r"\*(.+?)\*")
 _ITALIC_UNDERSCORE_PATTERN = re.compile(r"(?<![A-Za-z0-9_])_(.+?)_(?![A-Za-z0-9_])")
 
+_LINK_LABEL_ESCAPE_PATTERN = re.compile(r"([\\[\]])")
+
 _SLUG_KEEP_PATTERN = re.compile(
     r"[^a-z0-9\-_\u3040-\u309f\u30a0-\u30ff\u4e00-\u9fff]",
 )
@@ -143,6 +145,11 @@ def _assign_anchors(
     return result
 
 
+def _escape_link_label(text: str) -> str:
```
</details>

- [major] /Users/tsuryoryo/Desktop/repo/obsidian/backend/benchmark/markdown_toc.py:15 — `_BOLD_UNDERSCORE_PATTERN` と `_ITALIC_UNDERSCORE_PATTERN` が単語境界の判定を ASCII の `[A-Za-z0-9_]` に限定しているため、日本語など非 ASCII 文字に挟まれた `__` / `_` を単語内記法として扱えない。仕様では `foo_bar_baz` のような『単語内アンダースコアは装飾として扱わない』ことを求めており、日本語見出しも対象にしているので、`# 日本語_見出し_例` や `# 日本語__見出し__例` が誤って `日本語見出し例` に変換される。結果として目次表示テキストとアンカースラッグの両方が仕様とずれ、生成されたリンクが期待と一致しない。修正方針として、アンダースコア装飾の前後判定を ASCII 固定ではなく Unicode の単語文字を考慮する実装に変更し、少なくとも日本語文字に隣接する `_` / `__` は単語内として保持する必要がある。

**判断**: `_BOLD_UNDERSCORE_PATTERN` と `_ITALIC_UNDERSCORE_PATTERN` の前後判定を `[A-Za-z0-9_]` から `\w` に変更した。Pythonの `\w` はデフォルトでUnicode対応のため、日本語文字も「単語文字」として認識され、`日本語_見出し_例` のようなケースでアンダースコアが装飾ではなく単語内文字として正しく保持される。これにより目次テキストとアンカースラッグの両方が仕様通りに生成される。

<details><summary>修正 diff</summary>

```diff
diff --git a/backend/benchmark/markdown_toc.py b/backend/benchmark/markdown_toc.py
index d3e3fea..9a09bf2 100644
--- a/backend/benchmark/markdown_toc.py
+++ b/backend/benchmark/markdown_toc.py
@@ -5,16 +5,18 @@ from __future__ import annotations
 import re
 from dataclasses import dataclass
 
-_HEADING_PATTERN = re.compile(r"^(#{1,6})\s+(.*)$")
+_HEADING_PATTERN = re.compile(r"^(#{1,6}) +(.*)$")
 _FENCE_PATTERN = re.compile(r"^(`{3,}|~{3,})")
-_ATX_CLOSING_PATTERN = re.compile(r"\s+#+\s*$")
+_ATX_CLOSING_PATTERN = re.compile(r" +#+ *$")
 
 _LINK_PATTERN = re.compile(r"\[([^\]]*?)\]\([^)]*?\)")
 _CODE_PATTERN = re.compile(r"`([^`]*?)`")
 _BOLD_ASTERISK_PATTERN = re.compile(r"\*\*(.+?)\*\*")
-_BOLD_UNDERSCORE_PATTERN = re.compile(r"(?<![A-Za-z0-9_])__(.+?)__(?![A-Za-z0-9_])")
+_BOLD_UNDERSCORE_PATTERN = re.compile(r"(?<!\w)__(.+?)__(?!\w)")
 _ITALIC_ASTERISK_PATTERN = re.compile(r"\*(.+?)\*")
-_ITALIC_UNDERSCORE_PATTERN = re.compile(r"(?<![A-Za-z0-9_])_(.+?)_(?![A-Za-z0-9_])")
+_ITALIC_UNDERSCORE_PATTERN = re.compile(r"(?<!\w)_(.+?)_(?!\w)")
+
+_LINK_LABEL_ESCAPE_PATTERN = re.compile(r"([\\[\]])")
 
 _SLUG_KEEP_PATTERN = re.compile(
     r"[^a-z0-9\-_\u3040-\u309f\u30a0-\u30ff\u4e00-\u9fff]",
@@ -143,6 +145,11 @@ def _assign_anchors(
     return result
 
```
</details>

指摘なし（3回目で通過）

---

## 事前定義の設計判断

- ベンチマーク用ダミー機能のため、他モジュールへの依存は持たない
- 標準ライブラリのみ使用（外部パッケージ不使用）
- Markdown 装飾除去は正規表現の最短マッチで実装し、完全なパーサーは作らない

---

## サマリー

| 指標 | 値 |
|---|---|
| レビューステップ数 | 5 |
| レビューサイクル総数 | 8回（修正による再実行を含む） |
| 修正した指摘数 | 4件 |
| 通過ステップ数 | 5件 |
| 事前定義の設計判断 | 3件 |
| レビュー中に許容 | 0件 |
