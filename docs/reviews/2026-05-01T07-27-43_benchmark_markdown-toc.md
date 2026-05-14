# タスクレポート: benchmark/markdown-toc

**実行日**: 2026-05-01T07-27-43
**スコープ**: benchmark/markdown-toc
**結果**: 完了
**レビューサイクル数**: 5回
**修正件数**: 5件

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
- 実装生成: 1回目で GREEN（最大3回）

---

## レビュー詳細

### self_criteria

#### 指摘: 命名規則違反: 変数名の省略。ジェネレータ式の変数 `h` は `heading` の省略形。`min(heading.level for heading in headings)` とすべき。（minor）
- **ファイル**: backend/benchmark/markdown_toc.py:157
- **判断**: 修正
- **理由**: 1. **変数名 `h` → `heading`**: ジェネレータ式・内包表記でも省略名を避けるという命名規則に従い、意味が即座に伝わる完全名に統一した。
2. **マジックストリング定数化**: `` "`" `` と `"~"` が複数関数に散在しており、意味の不明瞭さと変更時の修正漏れリスクがあるため、`FENCE_CHAR_BACKTICK` / `FENCE_CHAR_TILDE` としてモジュール定数に切り出した。
3. いずれも minor 指摘だが、コードベース全体の命名・定数管理の一貫性を保つために対応した。
- **修正内容**:
```diff
diff --git a/backend/benchmark/markdown_toc.py b/backend/benchmark/markdown_toc.py
index 3358d22..cba871c 100644
--- a/backend/benchmark/markdown_toc.py
+++ b/backend/benchmark/markdown_toc.py
@@ -25,6 +25,9 @@ SLUG_DISALLOWED_PATTERN = re.compile(
 )
 CONSECUTIVE_HYPHENS_PATTERN = re.compile(r"-{2,}")
 
+FENCE_CHAR_BACKTICK = "`"
+FENCE_CHAR_TILDE = "~"
+
 INDENT_UNIT = 2
 
 
@@ -86,7 +89,9 @@ def _check_fence_close(
 ) -> tuple[bool, str | None, int]:
     """コードブロックの閉じフェンスを判定する."""
     pattern = (
-        BACKTICK_FENCE_CLOSE_PATTERN if fence_char == "`" else TILDE_FENCE_CLOSE_PATTERN
+        BACKTICK_FENCE_CLOSE_PATTERN
+        if fence_char == FENCE_CHAR_BACKTICK
+        else TILDE_FENCE_CLOSE_PATTERN
     )
     close_match = pattern.match(line)
     if close_match and len(close_match.group(1)) >= fence_length:
@@ -98,11 +103,11 @@ def _check_fence_open(line: str) -> tuple[bool, str | None, int]:
     """コードブロックの開きフェンスを判定する."""
     backtick_match = BACKTICK_FENCE_OPEN_PATTERN.match(line)
     if backtick_match:
-        return True, "`", len(backtick_match.group(1))
```

#### 指摘: 命名規則違反: 変数名の省略。リスト内包表記の変数 `h` は `heading` の省略形。`[heading for heading in all_headings if ...]` とすべき。（minor）
- **ファイル**: backend/benchmark/markdown_toc.py:178
- **判断**: 修正
- **理由**: 1. **変数名 `h` → `heading`**: ジェネレータ式・内包表記でも省略名を避けるという命名規則に従い、意味が即座に伝わる完全名に統一した。
2. **マジックストリング定数化**: `` "`" `` と `"~"` が複数関数に散在しており、意味の不明瞭さと変更時の修正漏れリスクがあるため、`FENCE_CHAR_BACKTICK` / `FENCE_CHAR_TILDE` としてモジュール定数に切り出した。
3. いずれも minor 指摘だが、コードベース全体の命名・定数管理の一貫性を保つために対応した。
- **修正内容**:
```diff
diff --git a/backend/benchmark/markdown_toc.py b/backend/benchmark/markdown_toc.py
index 3358d22..cba871c 100644
--- a/backend/benchmark/markdown_toc.py
+++ b/backend/benchmark/markdown_toc.py
@@ -25,6 +25,9 @@ SLUG_DISALLOWED_PATTERN = re.compile(
 )
 CONSECUTIVE_HYPHENS_PATTERN = re.compile(r"-{2,}")
 
+FENCE_CHAR_BACKTICK = "`"
+FENCE_CHAR_TILDE = "~"
+
 INDENT_UNIT = 2
 
 
@@ -86,7 +89,9 @@ def _check_fence_close(
 ) -> tuple[bool, str | None, int]:
     """コードブロックの閉じフェンスを判定する."""
     pattern = (
-        BACKTICK_FENCE_CLOSE_PATTERN if fence_char == "`" else TILDE_FENCE_CLOSE_PATTERN
+        BACKTICK_FENCE_CLOSE_PATTERN
+        if fence_char == FENCE_CHAR_BACKTICK
+        else TILDE_FENCE_CLOSE_PATTERN
     )
     close_match = pattern.match(line)
     if close_match and len(close_match.group(1)) >= fence_length:
@@ -98,11 +103,11 @@ def _check_fence_open(line: str) -> tuple[bool, str | None, int]:
     """コードブロックの開きフェンスを判定する."""
     backtick_match = BACKTICK_FENCE_OPEN_PATTERN.match(line)
     if backtick_match:
-        return True, "`", len(backtick_match.group(1))
```

#### 指摘: マジックストリング禁止違反: 文字列リテラル `"`"` が line 89（_check_fence_close）と line 101（_check_fence_open）の2関数で繰り返し使用されている。`FENCE_CHAR_BACKTICK = "`"` のようにモジュール定数に切り出すべき。（minor）
- **ファイル**: backend/benchmark/markdown_toc.py:89
- **判断**: 修正
- **理由**: 1. **変数名 `h` → `heading`**: ジェネレータ式・内包表記でも省略名を避けるという命名規則に従い、意味が即座に伝わる完全名に統一した。
2. **マジックストリング定数化**: `` "`" `` と `"~"` が複数関数に散在しており、意味の不明瞭さと変更時の修正漏れリスクがあるため、`FENCE_CHAR_BACKTICK` / `FENCE_CHAR_TILDE` としてモジュール定数に切り出した。
3. いずれも minor 指摘だが、コードベース全体の命名・定数管理の一貫性を保つために対応した。
- **修正内容**:
```diff
diff --git a/backend/benchmark/markdown_toc.py b/backend/benchmark/markdown_toc.py
index 3358d22..cba871c 100644
--- a/backend/benchmark/markdown_toc.py
+++ b/backend/benchmark/markdown_toc.py
@@ -25,6 +25,9 @@ SLUG_DISALLOWED_PATTERN = re.compile(
 )
 CONSECUTIVE_HYPHENS_PATTERN = re.compile(r"-{2,}")
 
+FENCE_CHAR_BACKTICK = "`"
+FENCE_CHAR_TILDE = "~"
+
 INDENT_UNIT = 2
 
 
@@ -86,7 +89,9 @@ def _check_fence_close(
 ) -> tuple[bool, str | None, int]:
     """コードブロックの閉じフェンスを判定する."""
     pattern = (
-        BACKTICK_FENCE_CLOSE_PATTERN if fence_char == "`" else TILDE_FENCE_CLOSE_PATTERN
+        BACKTICK_FENCE_CLOSE_PATTERN
+        if fence_char == FENCE_CHAR_BACKTICK
+        else TILDE_FENCE_CLOSE_PATTERN
     )
     close_match = pattern.match(line)
     if close_match and len(close_match.group(1)) >= fence_length:
@@ -98,11 +103,11 @@ def _check_fence_open(line: str) -> tuple[bool, str | None, int]:
     """コードブロックの開きフェンスを判定する."""
     backtick_match = BACKTICK_FENCE_OPEN_PATTERN.match(line)
     if backtick_match:
-        return True, "`", len(backtick_match.group(1))
```

### self_quality

#### 指摘: ATX_CLOSING_PATTERN の正規表現 r" +#+\s*$" は、`#+`（1個以上の#）の後にさらに `#+`（1個以上の#）を要求するため、末尾の # が2個以上ある場合にしかマッチしない。仕様書は「末尾の連続 # とその前のスペースを取り除く」と定めており、単一の #（例: `## Heading #` → `Heading`）も除去対象である。正しくは r" #+\s*$" とすべき。現在のテストは `## Heading ##`（# が2個）のため偶然通過している。（major）
- **ファイル**: backend/benchmark/markdown_toc.py:10
- **判断**: 修正
- **理由**: `r" +#+\s*$"` は `#` が2個以上連続する場合しかマッチしないため、`## Heading #` のような末尾 `#` 1個のケースを除去できないバグがあった。仕様は「末尾の連続 `#` とその前のスペース」を全て除去対象としており、`#` 1個も含まれる。`+#+` → `#+` に修正し、`#` 1個以上で正しくマッチするようにした。
- **修正内容**:
```diff
diff --git a/backend/benchmark/markdown_toc.py b/backend/benchmark/markdown_toc.py
index 3358d22..f58494b 100644
--- a/backend/benchmark/markdown_toc.py
+++ b/backend/benchmark/markdown_toc.py
@@ -6,7 +6,7 @@ import re
 from dataclasses import dataclass
 
 HEADING_PATTERN = re.compile(r"^(#{1,6}) +(.*)$")
-ATX_CLOSING_PATTERN = re.compile(r" +#+\s*$")
+ATX_CLOSING_PATTERN = re.compile(r" #+\s*$")
 
 BACKTICK_FENCE_OPEN_PATTERN = re.compile(r"^(`{3,})")
 TILDE_FENCE_OPEN_PATTERN = re.compile(r"^(~{3,})")
@@ -25,6 +25,9 @@ SLUG_DISALLOWED_PATTERN = re.compile(
 )
 CONSECUTIVE_HYPHENS_PATTERN = re.compile(r"-{2,}")
 
+FENCE_CHAR_BACKTICK = "`"
+FENCE_CHAR_TILDE = "~"
+
 INDENT_UNIT = 2
 
 
@@ -86,7 +89,9 @@ def _check_fence_close(
 ) -> tuple[bool, str | None, int]:
     """コードブロックの閉じフェンスを判定する."""
     pattern = (
-        BACKTICK_FENCE_CLOSE_PATTERN if fence_char == "`" else TILDE_FENCE_CLOSE_PATTERN
+        BACKTICK_FENCE_CLOSE_PATTERN
+        if fence_char == FENCE_CHAR_BACKTICK
```

指摘なし（2回目で通過）

### codex

#### 指摘: `TocResult` は `frozen=True` ですが `headings` が `list[TocHeading]` のため、呼び出し側が `result.headings.append(...)` などで内容を変更できます。仕様書の『戻り値のデータ構造は frozen（不変）とする』に反しており、意図しない状態変更を防ぐという技術判断を満たしていません。`tuple[TocHeading, ...]` などの不変コンテナにする必要があります。（major）
- **ファイル**: /Users/tsuryoryo/Desktop/repo/obsidian/backend/benchmark/markdown_toc.py:47
- **判断**: 修正
- **理由**: `TocResult`は`frozen=True`で属性の再代入は防げるが、`list`は中身の変更（append等）が可能なため、仕様書の「不変」要件を満たしていなかった。`tuple[TocHeading, ...]`に変更することで、コンテナ自体が不変となり、呼び出し側からの意図しない状態変更を構造的に防止できるようになった。
- **修正内容**:
```diff
diff --git a/backend/benchmark/markdown_toc.py b/backend/benchmark/markdown_toc.py
index 3358d22..a485947 100644
--- a/backend/benchmark/markdown_toc.py
+++ b/backend/benchmark/markdown_toc.py
@@ -6,7 +6,7 @@ import re
 from dataclasses import dataclass
 
 HEADING_PATTERN = re.compile(r"^(#{1,6}) +(.*)$")
-ATX_CLOSING_PATTERN = re.compile(r" +#+\s*$")
+ATX_CLOSING_PATTERN = re.compile(r" #+\s*$")
 
 BACKTICK_FENCE_OPEN_PATTERN = re.compile(r"^(`{3,})")
 TILDE_FENCE_OPEN_PATTERN = re.compile(r"^(~{3,})")
@@ -25,6 +25,9 @@ SLUG_DISALLOWED_PATTERN = re.compile(
 )
 CONSECUTIVE_HYPHENS_PATTERN = re.compile(r"-{2,}")
 
+FENCE_CHAR_BACKTICK = "`"
+FENCE_CHAR_TILDE = "~"
+
 INDENT_UNIT = 2
 
 
@@ -41,7 +44,7 @@ class TocHeading:
 class TocResult:
     """目次の生成結果."""
 
-    headings: list[TocHeading]
+    headings: tuple[TocHeading, ...]
     markdown: str
```

指摘なし（2回目で通過）

---

## 事前定義の設計判断

- ベンチマーク用ダミー機能のため、他モジュールへの依存は持たない
- 標準ライブラリのみ使用（外部パッケージ不使用）
- Markdown 装飾除去は正規表現の最短マッチで実装し、完全なパーサーは作らない

---

## レビュー中に許容した指摘

#### マジックストリング: 文字列リテラル "-" が _generate_slug (63, 65, 66行目) と _assign_anchors (150行目) で計4回繰り返し使用されているが定数化されていない。スラッグ区切り文字として SLUG_SEPARATOR = "-" 等に切り出すべき（minor）
- **ファイル**: backend/benchmark/markdown_toc.py:63
- **判断**: 許容
- **理由**: （第三者判断の生成に失敗。許容として扱う）

#### モジュール設計: ファイルが211行で200行目安を超過している。テストクラス単位での分割を検討すべき（minor）
- **ファイル**: backend/benchmark/tests/test_markdown_toc.py:1
- **判断**: 許容
- **理由**: （第三者判断の生成に失敗。許容として扱う）

---

## サマリー

| 指標 | 値 |
|---|---|
| レビューステップ数 | 3 |
| レビューサイクル総数 | 5回（修正による再実行を含む） |
| 修正した指摘数 | 5件 |
| 通過ステップ数 | 2件 |
| 事前定義の設計判断 | 3件 |
| レビュー中に許容 | 2件 |
