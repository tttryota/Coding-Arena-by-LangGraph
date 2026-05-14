# タスクレポート: benchmark/markdown-toc

**実行日**: 2026-05-02T02-50-32
**スコープ**: benchmark/markdown-toc
**結果**: 完了
**レビューサイクル数**: 14回
**修正件数**: 23件

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

### test_self_quality

#### 指摘: テストケース #17（Phase 4 統合テスト）が欠落している。仕様書の具体例を入力として6件の headings と markdown 出力を全フィールド検証するテストが実装されていない。（critical）
- **ファイル**: backend/benchmark/tests/test_markdown_toc.py
- **判断**: 修正
- **理由**: テスト仕様書とテストコードの入力値・期待値に不整合があり、仕様で意図した変換ルール（スペース→ハイフン、max_levelフィルタ、重複アンカー付番等）が実際には検証されていなかった。仕様書の具体例に忠実に合わせることで、各テストケースが本来検証すべきロジックを正しくカバーするよう修正した。また欠落していたPhase 4統合テストを追加し、仕様との完全な対応を確保した。
- **修正内容**:
```diff
diff --git a/backend/benchmark/tests/test_markdown_toc.py b/backend/benchmark/tests/test_markdown_toc.py
index 9045fa4..7fb0ae9 100644
--- a/backend/benchmark/tests/test_markdown_toc.py
+++ b/backend/benchmark/tests/test_markdown_toc.py
@@ -31,17 +31,17 @@ class TestGenerateToc:
     def test_generate_toc_single_h1_correct_fields(self) -> None:
         """検証: H1 が1つだけの場合.
 
-        期待: text="Hello", level=1, anchor="hello",
-              markdown="- [Hello](#hello)" が返る.
+        期待: text="Hello World", level=1, anchor="hello-world",
+              markdown="- [Hello World](#hello-world)" が返る.
         """
-        result = generate_toc("# Hello")
+        result = generate_toc("# Hello World")
 
         assert len(result.headings) == 1
         heading = result.headings[0]
-        assert heading.text == "Hello"
+        assert heading.text == "Hello World"
         assert heading.level == 1
-        assert heading.anchor == "hello"
-        assert result.markdown == "- [Hello](#hello)"
+        assert heading.anchor == "hello-world"
+        assert result.markdown == "- [Hello World](#hello-world)"
 
     def test_generate_toc_mixed_levels_four_headings_with_indent(self) -> None:
         """検証: H1, H2, H3 が混在し計4件の場合.
@@ -152,42 +152,37 @@ class TestGenerateToc:
     def test_generate_toc_min_max_level_filter_h2_h3_only(self) -> None:
```

#### 指摘: テストケース #3 との不整合。テストケース文書では入力が `"# Hello World"` で anchor="hello-world" を期待しているが、テストは `"# Hello"` を使用しており anchor="hello" となっている。Phase 1 の全フィールド検証でスペース→ハイフン変換のアンカー生成ルールが検証されない。（major）
- **ファイル**: backend/benchmark/tests/test_markdown_toc.py:37
- **判断**: 修正
- **理由**: テスト仕様書とテストコードの入力値・期待値に不整合があり、仕様で意図した変換ルール（スペース→ハイフン、max_levelフィルタ、重複アンカー付番等）が実際には検証されていなかった。仕様書の具体例に忠実に合わせることで、各テストケースが本来検証すべきロジックを正しくカバーするよう修正した。また欠落していたPhase 4統合テストを追加し、仕様との完全な対応を確保した。
- **修正内容**:
```diff
diff --git a/backend/benchmark/tests/test_markdown_toc.py b/backend/benchmark/tests/test_markdown_toc.py
index 9045fa4..7fb0ae9 100644
--- a/backend/benchmark/tests/test_markdown_toc.py
+++ b/backend/benchmark/tests/test_markdown_toc.py
@@ -31,17 +31,17 @@ class TestGenerateToc:
     def test_generate_toc_single_h1_correct_fields(self) -> None:
         """検証: H1 が1つだけの場合.
 
-        期待: text="Hello", level=1, anchor="hello",
-              markdown="- [Hello](#hello)" が返る.
+        期待: text="Hello World", level=1, anchor="hello-world",
+              markdown="- [Hello World](#hello-world)" が返る.
         """
-        result = generate_toc("# Hello")
+        result = generate_toc("# Hello World")
 
         assert len(result.headings) == 1
         heading = result.headings[0]
-        assert heading.text == "Hello"
+        assert heading.text == "Hello World"
         assert heading.level == 1
-        assert heading.anchor == "hello"
-        assert result.markdown == "- [Hello](#hello)"
+        assert heading.anchor == "hello-world"
+        assert result.markdown == "- [Hello World](#hello-world)"
 
     def test_generate_toc_mixed_levels_four_headings_with_indent(self) -> None:
         """検証: H1, H2, H3 が混在し計4件の場合.
@@ -152,42 +152,37 @@ class TestGenerateToc:
     def test_generate_toc_min_max_level_filter_h2_h3_only(self) -> None:
```

#### 指摘: テストケース #8 との不整合。テストケース文書では入力が `"# H1\n## H2\n### H3\n#### H4"` で H4 が max_level=3 により除外されることを検証するが、テストの入力に H4 が含まれていないため max_level の上限フィルタが検証されていない。また期待 headings 数がテストケース文書の2件に対しテストは3件。（major）
- **ファイル**: backend/benchmark/tests/test_markdown_toc.py:157
- **判断**: 修正
- **理由**: テスト仕様書とテストコードの入力値・期待値に不整合があり、仕様で意図した変換ルール（スペース→ハイフン、max_levelフィルタ、重複アンカー付番等）が実際には検証されていなかった。仕様書の具体例に忠実に合わせることで、各テストケースが本来検証すべきロジックを正しくカバーするよう修正した。また欠落していたPhase 4統合テストを追加し、仕様との完全な対応を確保した。
- **修正内容**:
```diff
diff --git a/backend/benchmark/tests/test_markdown_toc.py b/backend/benchmark/tests/test_markdown_toc.py
index 9045fa4..7fb0ae9 100644
--- a/backend/benchmark/tests/test_markdown_toc.py
+++ b/backend/benchmark/tests/test_markdown_toc.py
@@ -31,17 +31,17 @@ class TestGenerateToc:
     def test_generate_toc_single_h1_correct_fields(self) -> None:
         """検証: H1 が1つだけの場合.
 
-        期待: text="Hello", level=1, anchor="hello",
-              markdown="- [Hello](#hello)" が返る.
+        期待: text="Hello World", level=1, anchor="hello-world",
+              markdown="- [Hello World](#hello-world)" が返る.
         """
-        result = generate_toc("# Hello")
+        result = generate_toc("# Hello World")
 
         assert len(result.headings) == 1
         heading = result.headings[0]
-        assert heading.text == "Hello"
+        assert heading.text == "Hello World"
         assert heading.level == 1
-        assert heading.anchor == "hello"
-        assert result.markdown == "- [Hello](#hello)"
+        assert heading.anchor == "hello-world"
+        assert result.markdown == "- [Hello World](#hello-world)"
 
     def test_generate_toc_mixed_levels_four_headings_with_indent(self) -> None:
         """検証: H1, H2, H3 が混在し計4件の場合.
@@ -152,42 +152,37 @@ class TestGenerateToc:
     def test_generate_toc_min_max_level_filter_h2_h3_only(self) -> None:
```

#### 指摘: テストケース #16 との不整合。テストケース文書では `"# はじめに\n## 概要\n# はじめに"` の3件入力で、重複しない見出し「概要」が間に挟まっても付番が正しく動作することを検証するが、テストは `"# はじめに\n## はじめに"` の2件のみで、間に非重複見出しが存在するケースが検証されていない。（major）
- **ファイル**: backend/benchmark/tests/test_markdown_toc.py:272
- **判断**: 修正
- **理由**: テスト仕様書とテストコードの入力値・期待値に不整合があり、仕様で意図した変換ルール（スペース→ハイフン、max_levelフィルタ、重複アンカー付番等）が実際には検証されていなかった。仕様書の具体例に忠実に合わせることで、各テストケースが本来検証すべきロジックを正しくカバーするよう修正した。また欠落していたPhase 4統合テストを追加し、仕様との完全な対応を確保した。
- **修正内容**:
```diff
diff --git a/backend/benchmark/tests/test_markdown_toc.py b/backend/benchmark/tests/test_markdown_toc.py
index 9045fa4..7fb0ae9 100644
--- a/backend/benchmark/tests/test_markdown_toc.py
+++ b/backend/benchmark/tests/test_markdown_toc.py
@@ -31,17 +31,17 @@ class TestGenerateToc:
     def test_generate_toc_single_h1_correct_fields(self) -> None:
         """検証: H1 が1つだけの場合.
 
-        期待: text="Hello", level=1, anchor="hello",
-              markdown="- [Hello](#hello)" が返る.
+        期待: text="Hello World", level=1, anchor="hello-world",
+              markdown="- [Hello World](#hello-world)" が返る.
         """
-        result = generate_toc("# Hello")
+        result = generate_toc("# Hello World")
 
         assert len(result.headings) == 1
         heading = result.headings[0]
-        assert heading.text == "Hello"
+        assert heading.text == "Hello World"
         assert heading.level == 1
-        assert heading.anchor == "hello"
-        assert result.markdown == "- [Hello](#hello)"
+        assert heading.anchor == "hello-world"
+        assert result.markdown == "- [Hello World](#hello-world)"
 
     def test_generate_toc_mixed_levels_four_headings_with_indent(self) -> None:
         """検証: H1, H2, H3 が混在し計4件の場合.
@@ -152,42 +152,37 @@ class TestGenerateToc:
     def test_generate_toc_min_max_level_filter_h2_h3_only(self) -> None:
```

#### 指摘: テストケース #9 との値の不整合。テストケース文書では H1 レベル・"Bold"（大文字）・"[link](url)" を使用するが、テストは H2 レベル（max_level=6 追加）・"bold"（小文字）・"[link text](url)" を使用しており、入力・期待値ともに文書と異なる。（minor）
- **ファイル**: backend/benchmark/tests/test_markdown_toc.py:181
- **判断**: 修正
- **理由**: テスト仕様書とテストコードの入力値・期待値に不整合があり、仕様で意図した変換ルール（スペース→ハイフン、max_levelフィルタ、重複アンカー付番等）が実際には検証されていなかった。仕様書の具体例に忠実に合わせることで、各テストケースが本来検証すべきロジックを正しくカバーするよう修正した。また欠落していたPhase 4統合テストを追加し、仕様との完全な対応を確保した。
- **修正内容**:
```diff
diff --git a/backend/benchmark/tests/test_markdown_toc.py b/backend/benchmark/tests/test_markdown_toc.py
index 9045fa4..7fb0ae9 100644
--- a/backend/benchmark/tests/test_markdown_toc.py
+++ b/backend/benchmark/tests/test_markdown_toc.py
@@ -31,17 +31,17 @@ class TestGenerateToc:
     def test_generate_toc_single_h1_correct_fields(self) -> None:
         """検証: H1 が1つだけの場合.
 
-        期待: text="Hello", level=1, anchor="hello",
-              markdown="- [Hello](#hello)" が返る.
+        期待: text="Hello World", level=1, anchor="hello-world",
+              markdown="- [Hello World](#hello-world)" が返る.
         """
-        result = generate_toc("# Hello")
+        result = generate_toc("# Hello World")
 
         assert len(result.headings) == 1
         heading = result.headings[0]
-        assert heading.text == "Hello"
+        assert heading.text == "Hello World"
         assert heading.level == 1
-        assert heading.anchor == "hello"
-        assert result.markdown == "- [Hello](#hello)"
+        assert heading.anchor == "hello-world"
+        assert result.markdown == "- [Hello World](#hello-world)"
 
     def test_generate_toc_mixed_levels_four_headings_with_indent(self) -> None:
         """検証: H1, H2, H3 が混在し計4件の場合.
@@ -152,42 +152,37 @@ class TestGenerateToc:
     def test_generate_toc_min_max_level_filter_h2_h3_only(self) -> None:
```

#### 指摘: テストケース #12 との値の不整合。テストケース文書では見出しテキストが「セットアップ」だが、テストでは「カタカナ」を使用している。（minor）
- **ファイル**: backend/benchmark/tests/test_markdown_toc.py:221
- **判断**: 修正
- **理由**: テスト仕様書とテストコードの入力値・期待値に不整合があり、仕様で意図した変換ルール（スペース→ハイフン、max_levelフィルタ、重複アンカー付番等）が実際には検証されていなかった。仕様書の具体例に忠実に合わせることで、各テストケースが本来検証すべきロジックを正しくカバーするよう修正した。また欠落していたPhase 4統合テストを追加し、仕様との完全な対応を確保した。
- **修正内容**:
```diff
diff --git a/backend/benchmark/tests/test_markdown_toc.py b/backend/benchmark/tests/test_markdown_toc.py
index 9045fa4..7fb0ae9 100644
--- a/backend/benchmark/tests/test_markdown_toc.py
+++ b/backend/benchmark/tests/test_markdown_toc.py
@@ -31,17 +31,17 @@ class TestGenerateToc:
     def test_generate_toc_single_h1_correct_fields(self) -> None:
         """検証: H1 が1つだけの場合.
 
-        期待: text="Hello", level=1, anchor="hello",
-              markdown="- [Hello](#hello)" が返る.
+        期待: text="Hello World", level=1, anchor="hello-world",
+              markdown="- [Hello World](#hello-world)" が返る.
         """
-        result = generate_toc("# Hello")
+        result = generate_toc("# Hello World")
 
         assert len(result.headings) == 1
         heading = result.headings[0]
-        assert heading.text == "Hello"
+        assert heading.text == "Hello World"
         assert heading.level == 1
-        assert heading.anchor == "hello"
-        assert result.markdown == "- [Hello](#hello)"
+        assert heading.anchor == "hello-world"
+        assert result.markdown == "- [Hello World](#hello-world)"
 
     def test_generate_toc_mixed_levels_four_headings_with_indent(self) -> None:
         """検証: H1, H2, H3 が混在し計4件の場合.
@@ -152,42 +152,37 @@ class TestGenerateToc:
     def test_generate_toc_min_max_level_filter_h2_h3_only(self) -> None:
```

#### 指摘: テストケース #13 との値の不整合。テストケース文書では見出しテキストが「設定方法」だが、テストでは「漢字」を使用している。（minor）
- **ファイル**: backend/benchmark/tests/test_markdown_toc.py:232
- **判断**: 修正
- **理由**: テスト仕様書とテストコードの入力値・期待値に不整合があり、仕様で意図した変換ルール（スペース→ハイフン、max_levelフィルタ、重複アンカー付番等）が実際には検証されていなかった。仕様書の具体例に忠実に合わせることで、各テストケースが本来検証すべきロジックを正しくカバーするよう修正した。また欠落していたPhase 4統合テストを追加し、仕様との完全な対応を確保した。
- **修正内容**:
```diff
diff --git a/backend/benchmark/tests/test_markdown_toc.py b/backend/benchmark/tests/test_markdown_toc.py
index 9045fa4..7fb0ae9 100644
--- a/backend/benchmark/tests/test_markdown_toc.py
+++ b/backend/benchmark/tests/test_markdown_toc.py
@@ -31,17 +31,17 @@ class TestGenerateToc:
     def test_generate_toc_single_h1_correct_fields(self) -> None:
         """検証: H1 が1つだけの場合.
 
-        期待: text="Hello", level=1, anchor="hello",
-              markdown="- [Hello](#hello)" が返る.
+        期待: text="Hello World", level=1, anchor="hello-world",
+              markdown="- [Hello World](#hello-world)" が返る.
         """
-        result = generate_toc("# Hello")
+        result = generate_toc("# Hello World")
 
         assert len(result.headings) == 1
         heading = result.headings[0]
-        assert heading.text == "Hello"
+        assert heading.text == "Hello World"
         assert heading.level == 1
-        assert heading.anchor == "hello"
-        assert result.markdown == "- [Hello](#hello)"
+        assert heading.anchor == "hello-world"
+        assert result.markdown == "- [Hello World](#hello-world)"
 
     def test_generate_toc_mixed_levels_four_headings_with_indent(self) -> None:
         """検証: H1, H2, H3 が混在し計4件の場合.
@@ -152,42 +152,37 @@ class TestGenerateToc:
     def test_generate_toc_min_max_level_filter_h2_h3_only(self) -> None:
```

#### 指摘: テストケース文書との入力不整合。テストケース4は入力を `"# Title\n## Section\n### Sub\n## Another"` と指定しているが、テストでは "Some text" 行が追加され、見出しテキストが "Sub" → "Subsection" に変更されている。（major）
- **ファイル**: backend/benchmark/tests/test_markdown_toc.py:51
- **判断**: 修正
- **理由**: テスト仕様書で定義された入力文字列・見出しテキスト・パラメータと、実装されたテストコードの間に不整合があった。
修正では、仕様書の記載に忠実になるよう入力を元に戻し（"Subsection"→"Sub"、H2→H1など）、仕様にない `max_level=6` の追加を削除した。
テストコードは仕様書の単一情報源（Single Source of Truth）であるべきという判断に基づく対応。
- **修正内容**:
```diff
diff --git a/backend/benchmark/tests/test_markdown_toc.py b/backend/benchmark/tests/test_markdown_toc.py
index 9045fa4..8837af4 100644
--- a/backend/benchmark/tests/test_markdown_toc.py
+++ b/backend/benchmark/tests/test_markdown_toc.py
@@ -31,17 +31,17 @@ class TestGenerateToc:
     def test_generate_toc_single_h1_correct_fields(self) -> None:
         """検証: H1 が1つだけの場合.
 
-        期待: text="Hello", level=1, anchor="hello",
-              markdown="- [Hello](#hello)" が返る.
+        期待: text="Hello World", level=1, anchor="hello-world",
+              markdown="- [Hello World](#hello-world)" が返る.
         """
-        result = generate_toc("# Hello")
+        result = generate_toc("# Hello World")
 
         assert len(result.headings) == 1
         heading = result.headings[0]
-        assert heading.text == "Hello"
+        assert heading.text == "Hello World"
         assert heading.level == 1
-        assert heading.anchor == "hello"
-        assert result.markdown == "- [Hello](#hello)"
+        assert heading.anchor == "hello-world"
+        assert result.markdown == "- [Hello World](#hello-world)"
 
     def test_generate_toc_mixed_levels_four_headings_with_indent(self) -> None:
         """検証: H1, H2, H3 が混在し計4件の場合.
@@ -50,9 +50,8 @@ class TestGenerateToc:
         """
```

#### 指摘: テストケース文書との入力不整合。テストケース7は `"# Section\n# Section\n# Section"` (H1) をデフォルトパラメータで渡すと指定しているが、テストでは `## Section` (H2) に変更し、テストケース文書にない `max_level=6` を追加している。（major）
- **ファイル**: backend/benchmark/tests/test_markdown_toc.py:136
- **判断**: 修正
- **理由**: テスト仕様書で定義された入力文字列・見出しテキスト・パラメータと、実装されたテストコードの間に不整合があった。
修正では、仕様書の記載に忠実になるよう入力を元に戻し（"Subsection"→"Sub"、H2→H1など）、仕様にない `max_level=6` の追加を削除した。
テストコードは仕様書の単一情報源（Single Source of Truth）であるべきという判断に基づく対応。
- **修正内容**:
```diff
diff --git a/backend/benchmark/tests/test_markdown_toc.py b/backend/benchmark/tests/test_markdown_toc.py
index 9045fa4..8837af4 100644
--- a/backend/benchmark/tests/test_markdown_toc.py
+++ b/backend/benchmark/tests/test_markdown_toc.py
@@ -31,17 +31,17 @@ class TestGenerateToc:
     def test_generate_toc_single_h1_correct_fields(self) -> None:
         """検証: H1 が1つだけの場合.
 
-        期待: text="Hello", level=1, anchor="hello",
-              markdown="- [Hello](#hello)" が返る.
+        期待: text="Hello World", level=1, anchor="hello-world",
+              markdown="- [Hello World](#hello-world)" が返る.
         """
-        result = generate_toc("# Hello")
+        result = generate_toc("# Hello World")
 
         assert len(result.headings) == 1
         heading = result.headings[0]
-        assert heading.text == "Hello"
+        assert heading.text == "Hello World"
         assert heading.level == 1
-        assert heading.anchor == "hello"
-        assert result.markdown == "- [Hello](#hello)"
+        assert heading.anchor == "hello-world"
+        assert result.markdown == "- [Hello World](#hello-world)"
 
     def test_generate_toc_mixed_levels_four_headings_with_indent(self) -> None:
         """検証: H1, H2, H3 が混在し計4件の場合.
@@ -50,9 +50,8 @@ class TestGenerateToc:
         """
```

#### 指摘: テストケース文書との入力不整合。テストケース10は `"# foo_bar_baz"` (H1) と指定しているが、テストでは `## foo_bar_baz` (H2) に変更し、テストケース文書にない `max_level=6` を追加している。（major）
- **ファイル**: backend/benchmark/tests/test_markdown_toc.py:193
- **判断**: 修正
- **理由**: テスト仕様書で定義された入力文字列・見出しテキスト・パラメータと、実装されたテストコードの間に不整合があった。
修正では、仕様書の記載に忠実になるよう入力を元に戻し（"Subsection"→"Sub"、H2→H1など）、仕様にない `max_level=6` の追加を削除した。
テストコードは仕様書の単一情報源（Single Source of Truth）であるべきという判断に基づく対応。
- **修正内容**:
```diff
diff --git a/backend/benchmark/tests/test_markdown_toc.py b/backend/benchmark/tests/test_markdown_toc.py
index 9045fa4..8837af4 100644
--- a/backend/benchmark/tests/test_markdown_toc.py
+++ b/backend/benchmark/tests/test_markdown_toc.py
@@ -31,17 +31,17 @@ class TestGenerateToc:
     def test_generate_toc_single_h1_correct_fields(self) -> None:
         """検証: H1 が1つだけの場合.
 
-        期待: text="Hello", level=1, anchor="hello",
-              markdown="- [Hello](#hello)" が返る.
+        期待: text="Hello World", level=1, anchor="hello-world",
+              markdown="- [Hello World](#hello-world)" が返る.
         """
-        result = generate_toc("# Hello")
+        result = generate_toc("# Hello World")
 
         assert len(result.headings) == 1
         heading = result.headings[0]
-        assert heading.text == "Hello"
+        assert heading.text == "Hello World"
         assert heading.level == 1
-        assert heading.anchor == "hello"
-        assert result.markdown == "- [Hello](#hello)"
+        assert heading.anchor == "hello-world"
+        assert result.markdown == "- [Hello World](#hello-world)"
 
     def test_generate_toc_mixed_levels_four_headings_with_indent(self) -> None:
         """検証: H1, H2, H3 が混在し計4件の場合.
@@ -50,9 +50,8 @@ class TestGenerateToc:
         """
```

#### 指摘: テストケース文書との入力不整合。テストケース14は見出しテキストを "Overview" / "Detail" と指定しているが、テストでは "Level Two" / "Level Four" に変更されている。（major）
- **ファイル**: backend/benchmark/tests/test_markdown_toc.py:239
- **判断**: 修正
- **理由**: テスト仕様書で定義された入力文字列・見出しテキスト・パラメータと、実装されたテストコードの間に不整合があった。
修正では、仕様書の記載に忠実になるよう入力を元に戻し（"Subsection"→"Sub"、H2→H1など）、仕様にない `max_level=6` の追加を削除した。
テストコードは仕様書の単一情報源（Single Source of Truth）であるべきという判断に基づく対応。
- **修正内容**:
```diff
diff --git a/backend/benchmark/tests/test_markdown_toc.py b/backend/benchmark/tests/test_markdown_toc.py
index 9045fa4..8837af4 100644
--- a/backend/benchmark/tests/test_markdown_toc.py
+++ b/backend/benchmark/tests/test_markdown_toc.py
@@ -31,17 +31,17 @@ class TestGenerateToc:
     def test_generate_toc_single_h1_correct_fields(self) -> None:
         """検証: H1 が1つだけの場合.
 
-        期待: text="Hello", level=1, anchor="hello",
-              markdown="- [Hello](#hello)" が返る.
+        期待: text="Hello World", level=1, anchor="hello-world",
+              markdown="- [Hello World](#hello-world)" が返る.
         """
-        result = generate_toc("# Hello")
+        result = generate_toc("# Hello World")
 
         assert len(result.headings) == 1
         heading = result.headings[0]
-        assert heading.text == "Hello"
+        assert heading.text == "Hello World"
         assert heading.level == 1
-        assert heading.anchor == "hello"
-        assert result.markdown == "- [Hello](#hello)"
+        assert heading.anchor == "hello-world"
+        assert result.markdown == "- [Hello World](#hello-world)"
 
     def test_generate_toc_mixed_levels_four_headings_with_indent(self) -> None:
         """検証: H1, H2, H3 が混在し計4件の場合.
@@ -50,9 +50,8 @@ class TestGenerateToc:
         """
```

#### 指摘: テストケース文書とのパラメータ不整合。テストケース15は `max_level` を指定していない（デフォルト使用）が、テストでは `max_level=6` が追加されている。H2 はデフォルトの max_level=3 の範囲内であり不要。（major）
- **ファイル**: backend/benchmark/tests/test_markdown_toc.py:254
- **判断**: 修正
- **理由**: テスト仕様書で定義された入力文字列・見出しテキスト・パラメータと、実装されたテストコードの間に不整合があった。
修正では、仕様書の記載に忠実になるよう入力を元に戻し（"Subsection"→"Sub"、H2→H1など）、仕様にない `max_level=6` の追加を削除した。
テストコードは仕様書の単一情報源（Single Source of Truth）であるべきという判断に基づく対応。
- **修正内容**:
```diff
diff --git a/backend/benchmark/tests/test_markdown_toc.py b/backend/benchmark/tests/test_markdown_toc.py
index 9045fa4..8837af4 100644
--- a/backend/benchmark/tests/test_markdown_toc.py
+++ b/backend/benchmark/tests/test_markdown_toc.py
@@ -31,17 +31,17 @@ class TestGenerateToc:
     def test_generate_toc_single_h1_correct_fields(self) -> None:
         """検証: H1 が1つだけの場合.
 
-        期待: text="Hello", level=1, anchor="hello",
-              markdown="- [Hello](#hello)" が返る.
+        期待: text="Hello World", level=1, anchor="hello-world",
+              markdown="- [Hello World](#hello-world)" が返る.
         """
-        result = generate_toc("# Hello")
+        result = generate_toc("# Hello World")
 
         assert len(result.headings) == 1
         heading = result.headings[0]
-        assert heading.text == "Hello"
+        assert heading.text == "Hello World"
         assert heading.level == 1
-        assert heading.anchor == "hello"
-        assert result.markdown == "- [Hello](#hello)"
+        assert heading.anchor == "hello-world"
+        assert result.markdown == "- [Hello World](#hello-world)"
 
     def test_generate_toc_mixed_levels_four_headings_with_indent(self) -> None:
         """検証: H1, H2, H3 が混在し計4件の場合.
@@ -50,9 +50,8 @@ class TestGenerateToc:
         """
```

指摘なし（3回目で通過）

### test_codex

#### 指摘: 空結果の検証で `result.headings == ()` を固定しており、テストケース文書の「headings が空リスト」と一致していません。仕様書も要求しているのは不変性であって具体的なコレクション型までは規定していないため、ここは API を必要以上に `tuple` に拘束しています。同種の問題が 28 行目にもあります。（major）
- **ファイル**: /Users/tsuryoryo/Desktop/repo/obsidian/backend/benchmark/tests/test_markdown_toc.py:18
- **判断**: 修正
- **理由**: 1. **[major]** `result.headings == ()` を `len(result.headings) == 0` に変更し、APIの戻り値型をtupleに縛らず、仕様書が求める「空であること」だけを検証するようにした。
2. **[minor]** コードブロック除外テストに `result.markdown` の検証を追加し、抽出された見出しだけでなく生成される目次文字列にもコードブロック内の見出しが含まれないことを担保した。
3. いずれも「仕様書が要求する範囲を過不足なくテストする」という原則に従い、過剰な型制約の除去と検証カバレッジの補完を行った。
- **修正内容**:
```diff
diff --git a/backend/benchmark/tests/test_markdown_toc.py b/backend/benchmark/tests/test_markdown_toc.py
index 9045fa4..643c854 100644
--- a/backend/benchmark/tests/test_markdown_toc.py
+++ b/backend/benchmark/tests/test_markdown_toc.py
@@ -15,7 +15,7 @@ class TestGenerateToc:
         """
         result = generate_toc("")
 
-        assert result.headings == ()
+        assert len(result.headings) == 0
         assert result.markdown == ""
 
     def test_generate_toc_no_headings_empty_result(self) -> None:
@@ -25,23 +25,23 @@ class TestGenerateToc:
         """
         result = generate_toc("本文テキストのみ。見出しなし。\n次の行。")
 
-        assert result.headings == ()
+        assert len(result.headings) == 0
         assert result.markdown == ""
 
     def test_generate_toc_single_h1_correct_fields(self) -> None:
         """検証: H1 が1つだけの場合.
 
-        期待: text="Hello", level=1, anchor="hello",
-              markdown="- [Hello](#hello)" が返る.
+        期待: text="Hello World", level=1, anchor="hello-world",
+              markdown="- [Hello World](#hello-world)" が返る.
         """
-        result = generate_toc("# Hello")
```

#### 指摘: コードブロック除外の2テストは `headings` の件数とテキストだけを見ており、返却される `markdown` がコードブロック内の見出しを含まないことを検証していません。仕様書とテストケース文書はいずれも目次生成結果全体の正しさを対象にしているため、抽出結果とレンダリング結果の不整合を見逃します。同じ問題が 124-126 行目のチルダフェンスのテストにもあります。（minor）
- **ファイル**: /Users/tsuryoryo/Desktop/repo/obsidian/backend/benchmark/tests/test_markdown_toc.py:99
- **判断**: 修正
- **理由**: 1. **[major]** `result.headings == ()` を `len(result.headings) == 0` に変更し、APIの戻り値型をtupleに縛らず、仕様書が求める「空であること」だけを検証するようにした。
2. **[minor]** コードブロック除外テストに `result.markdown` の検証を追加し、抽出された見出しだけでなく生成される目次文字列にもコードブロック内の見出しが含まれないことを担保した。
3. いずれも「仕様書が要求する範囲を過不足なくテストする」という原則に従い、過剰な型制約の除去と検証カバレッジの補完を行った。
- **修正内容**:
```diff
diff --git a/backend/benchmark/tests/test_markdown_toc.py b/backend/benchmark/tests/test_markdown_toc.py
index 9045fa4..643c854 100644
--- a/backend/benchmark/tests/test_markdown_toc.py
+++ b/backend/benchmark/tests/test_markdown_toc.py
@@ -15,7 +15,7 @@ class TestGenerateToc:
         """
         result = generate_toc("")
 
-        assert result.headings == ()
+        assert len(result.headings) == 0
         assert result.markdown == ""
 
     def test_generate_toc_no_headings_empty_result(self) -> None:
@@ -25,23 +25,23 @@ class TestGenerateToc:
         """
         result = generate_toc("本文テキストのみ。見出しなし。\n次の行。")
 
-        assert result.headings == ()
+        assert len(result.headings) == 0
         assert result.markdown == ""
 
     def test_generate_toc_single_h1_correct_fields(self) -> None:
         """検証: H1 が1つだけの場合.
 
-        期待: text="Hello", level=1, anchor="hello",
-              markdown="- [Hello](#hello)" が返る.
+        期待: text="Hello World", level=1, anchor="hello-world",
+              markdown="- [Hello World](#hello-world)" が返る.
         """
-        result = generate_toc("# Hello")
```

指摘なし（2回目で通過）

### self_criteria

#### 指摘: _is_closing_fence が閉じフェンス行の後続文字を検証していない。_parse_fence は行頭のフェンス文字のみをチェックするため、コードブロック内の「python」のような info string 付き行が閉じフェンスと誤判定される。結果としてコードブロックが早期に閉じられ、ブロック内の # 行が見出しとして誤抽出される。CommonMark 仕様では閉じフェンスに info string は許容されないため、行がフェンス文字と末尾空白のみで構成されていることを検証すべき。（major）
- **ファイル**: backend/benchmark/markdown_toc.py:87
- **判断**: 修正
- **理由**: `_is_closing_fence` が閉じフェンス文字の個数だけで判定しており、後続に info string（例: `python`）がある行も閉じフェンスと誤認していた。CommonMark 仕様では閉じフェンスに info string は許容されないため、フェンス文字以降が空白のみであることを検証する条件（`rest.strip() == ""`）を追加し、コードブロック内の `#` 行が見出しとして誤抽出されるバグを防止した。
- **修正内容**:
```diff
diff --git a/backend/benchmark/markdown_toc.py b/backend/benchmark/markdown_toc.py
index 53ca68d..c3afbf1 100644
--- a/backend/benchmark/markdown_toc.py
+++ b/backend/benchmark/markdown_toc.py
@@ -20,6 +20,7 @@ _SLUG_KEEP_PATTERN = re.compile(
     r"[^a-z0-9\-_\u3040-\u309f\u30a0-\u30ff\u4e00-\u9fff]",
 )
 _CONSECUTIVE_HYPHENS_PATTERN = re.compile(r"-+")
+_SLUG_SEPARATOR = "-"
 
 _DEFAULT_MIN_LEVEL = 1
 _DEFAULT_MAX_LEVEL = 3
@@ -56,10 +57,10 @@ def _strip_decorations(text: str) -> str:
 def _generate_slug(text: str) -> str:
     """GitHub 互換の簡易アンカースラッグを生成する."""
     slug = text.lower()
-    slug = slug.replace(" ", "-")
+    slug = slug.replace(" ", _SLUG_SEPARATOR)
     slug = _SLUG_KEEP_PATTERN.sub("", slug)
-    slug = _CONSECUTIVE_HYPHENS_PATTERN.sub("-", slug)
-    slug = slug.strip("-")
+    slug = _CONSECUTIVE_HYPHENS_PATTERN.sub(_SLUG_SEPARATOR, slug)
+    slug = slug.strip(_SLUG_SEPARATOR)
     return slug
 
 
@@ -93,25 +94,28 @@ def _is_closing_fence(
     if fence is None:
         return False
     closing_char, closing_count = fence
```

#### 指摘: generate_toc が min_level > max_level という不正な引数を受け取った際に空の TocResult を静かに返しており、握り潰しに該当する。呼び出し側の引数ミスが検知されずバグが潜在化する。ValueError を送出し「min_level({値}) が max_level({値}) を超えています」のように具体的文脈を含むメッセージを返すべき。（major）
- **ファイル**: backend/benchmark/markdown_toc.py:153
- **判断**: 修正
- **理由**: 1. **[major] ValueError送出**: `min_level > max_level` を黙って空結果で返すと呼び出し側のバグが潜在化するため、不正な引数は早期に `ValueError` で弾き、問題の検知を確実にした。
2. **[minor] 省略名の展開**: `Toc` は `TableOfContents` の省略であり命名規約違反のため、`TocHeading` → `TableOfContentsHeading`、`TocResult` → `TableOfContentsResult` にリネームし規約に準拠させた。
3. 両修正とも「不具合の早期検知」と「コードの可読性・規約遵守」という品質基準に基づく対応であり、機能的な振る舞いへの影響は最小限に留めている。
- **修正内容**:
```diff
diff --git a/backend/benchmark/markdown_toc.py b/backend/benchmark/markdown_toc.py
index 53ca68d..efcd1e6 100644
--- a/backend/benchmark/markdown_toc.py
+++ b/backend/benchmark/markdown_toc.py
@@ -20,13 +20,14 @@ _SLUG_KEEP_PATTERN = re.compile(
     r"[^a-z0-9\-_\u3040-\u309f\u30a0-\u30ff\u4e00-\u9fff]",
 )
 _CONSECUTIVE_HYPHENS_PATTERN = re.compile(r"-+")
+_SLUG_SEPARATOR = "-"
 
 _DEFAULT_MIN_LEVEL = 1
 _DEFAULT_MAX_LEVEL = 3
 
 
 @dataclass(frozen=True)
-class TocHeading:
+class TableOfContentsHeading:
     """目次の見出し1件を表す値オブジェクト."""
 
     text: str
@@ -35,10 +36,10 @@ class TocHeading:
 
 
 @dataclass(frozen=True)
-class TocResult:
+class TableOfContentsResult:
     """目次の生成結果を表す値オブジェクト."""
 
-    headings: tuple[TocHeading, ...]
+    headings: tuple[TableOfContentsHeading, ...]
```

#### 指摘: Toc は TableOfContents の省略形であり「変数名は省略しない」規約に違反している。TocHeading → TableOfContentsHeading、TocResult → TableOfContentsResult、generate_toc → generate_table_of_contents に rename すべき。（minor）
- **ファイル**: backend/benchmark/markdown_toc.py:31
- **判断**: 修正
- **理由**: 1. **[major] ValueError送出**: `min_level > max_level` を黙って空結果で返すと呼び出し側のバグが潜在化するため、不正な引数は早期に `ValueError` で弾き、問題の検知を確実にした。
2. **[minor] 省略名の展開**: `Toc` は `TableOfContents` の省略であり命名規約違反のため、`TocHeading` → `TableOfContentsHeading`、`TocResult` → `TableOfContentsResult` にリネームし規約に準拠させた。
3. 両修正とも「不具合の早期検知」と「コードの可読性・規約遵守」という品質基準に基づく対応であり、機能的な振る舞いへの影響は最小限に留めている。
- **修正内容**:
```diff
diff --git a/backend/benchmark/markdown_toc.py b/backend/benchmark/markdown_toc.py
index 53ca68d..efcd1e6 100644
--- a/backend/benchmark/markdown_toc.py
+++ b/backend/benchmark/markdown_toc.py
@@ -20,13 +20,14 @@ _SLUG_KEEP_PATTERN = re.compile(
     r"[^a-z0-9\-_\u3040-\u309f\u30a0-\u30ff\u4e00-\u9fff]",
 )
 _CONSECUTIVE_HYPHENS_PATTERN = re.compile(r"-+")
+_SLUG_SEPARATOR = "-"
 
 _DEFAULT_MIN_LEVEL = 1
 _DEFAULT_MAX_LEVEL = 3
 
 
 @dataclass(frozen=True)
-class TocHeading:
+class TableOfContentsHeading:
     """目次の見出し1件を表す値オブジェクト."""
 
     text: str
@@ -35,10 +36,10 @@ class TocHeading:
 
 
 @dataclass(frozen=True)
-class TocResult:
+class TableOfContentsResult:
     """目次の生成結果を表す値オブジェクト."""
 
-    headings: tuple[TocHeading, ...]
+    headings: tuple[TableOfContentsHeading, ...]
```

#### 指摘: 変数名 `msg` が `message` の省略形。命名規則「変数名は省略しない」に違反。`message` に rename すべき。（minor）
- **ファイル**: backend/benchmark/markdown_toc.py:169
- **判断**: 修正
- **理由**: `msg` → `message`、`fence_char` → `fence_character`、`closing_char` → `closing_character` へのリネームは、プロジェクトの命名規則「変数名は省略しない」に従うための修正。省略形は可読性を下げ、規約違反のまま残すとコードベース全体の一貫性が崩れるため対応した。
- **修正内容**:
```diff
diff --git a/backend/benchmark/markdown_toc.py b/backend/benchmark/markdown_toc.py
index 53ca68d..2a8208f 100644
--- a/backend/benchmark/markdown_toc.py
+++ b/backend/benchmark/markdown_toc.py
@@ -20,13 +20,14 @@ _SLUG_KEEP_PATTERN = re.compile(
     r"[^a-z0-9\-_\u3040-\u309f\u30a0-\u30ff\u4e00-\u9fff]",
 )
 _CONSECUTIVE_HYPHENS_PATTERN = re.compile(r"-+")
+_SLUG_SEPARATOR = "-"
 
 _DEFAULT_MIN_LEVEL = 1
 _DEFAULT_MAX_LEVEL = 3
 
 
 @dataclass(frozen=True)
-class TocHeading:
+class TableOfContentsHeading:
     """目次の見出し1件を表す値オブジェクト."""
 
     text: str
@@ -35,10 +36,10 @@ class TocHeading:
 
 
 @dataclass(frozen=True)
-class TocResult:
+class TableOfContentsResult:
     """目次の生成結果を表す値オブジェクト."""
 
-    headings: tuple[TocHeading, ...]
+    headings: tuple[TableOfContentsHeading, ...]
```

#### 指摘: パラメータ名 `fence_char` および96行目の `closing_char` で `char` が `character` の省略形。命名規則「変数名は省略しない」に違反。`fence_character` / `closing_character` に rename すべき。同変数は107行・119行にも存在する。（minor）
- **ファイル**: backend/benchmark/markdown_toc.py:89
- **判断**: 修正
- **理由**: `msg` → `message`、`fence_char` → `fence_character`、`closing_char` → `closing_character` へのリネームは、プロジェクトの命名規則「変数名は省略しない」に従うための修正。省略形は可読性を下げ、規約違反のまま残すとコードベース全体の一貫性が崩れるため対応した。
- **修正内容**:
```diff
diff --git a/backend/benchmark/markdown_toc.py b/backend/benchmark/markdown_toc.py
index 53ca68d..2a8208f 100644
--- a/backend/benchmark/markdown_toc.py
+++ b/backend/benchmark/markdown_toc.py
@@ -20,13 +20,14 @@ _SLUG_KEEP_PATTERN = re.compile(
     r"[^a-z0-9\-_\u3040-\u309f\u30a0-\u30ff\u4e00-\u9fff]",
 )
 _CONSECUTIVE_HYPHENS_PATTERN = re.compile(r"-+")
+_SLUG_SEPARATOR = "-"
 
 _DEFAULT_MIN_LEVEL = 1
 _DEFAULT_MAX_LEVEL = 3
 
 
 @dataclass(frozen=True)
-class TocHeading:
+class TableOfContentsHeading:
     """目次の見出し1件を表す値オブジェクト."""
 
     text: str
@@ -35,10 +36,10 @@ class TocHeading:
 
 
 @dataclass(frozen=True)
-class TocResult:
+class TableOfContentsResult:
     """目次の生成結果を表す値オブジェクト."""
 
-    headings: tuple[TocHeading, ...]
+    headings: tuple[TableOfContentsHeading, ...]
```

指摘なし（4回目で通過）

### self_quality

#### 指摘: min_level > max_level の場合に ValueError を送出しているが、仕様の境界条件では「空の目次を返す（エラーにしない）。呼び出し側の便宜のため。」と定義されている。呼び出し側が min/max を動的に組み立てる場合に毎回ガードが必要になり、仕様の意図に反する。raise ValueError を削除し、空の TableOfContentsResult を返すように修正すべき。（major）
- **ファイル**: backend/benchmark/markdown_toc.py:147
- **判断**: 修正
- **理由**: 仕様では `min_level > max_level` は「空の目次を返す（エラーにしない）」と定義されている境界条件であり、呼び出し側が動的にレベル範囲を組み立てる際に毎回ガードコードを書かせるのは不便なため、`raise ValueError` を削除して空の `TableOfContentsResult` を返すように変更した。これにより呼び出し側の利便性を保ちつつ仕様の意図に沿った振る舞いとなる。
- **修正内容**:
```diff
diff --git a/backend/benchmark/markdown_toc.py b/backend/benchmark/markdown_toc.py
index 53ca68d..a7ab50f 100644
--- a/backend/benchmark/markdown_toc.py
+++ b/backend/benchmark/markdown_toc.py
@@ -20,13 +20,14 @@ _SLUG_KEEP_PATTERN = re.compile(
     r"[^a-z0-9\-_\u3040-\u309f\u30a0-\u30ff\u4e00-\u9fff]",
 )
 _CONSECUTIVE_HYPHENS_PATTERN = re.compile(r"-+")
+_SLUG_SEPARATOR = "-"
 
 _DEFAULT_MIN_LEVEL = 1
 _DEFAULT_MAX_LEVEL = 3
 
 
 @dataclass(frozen=True)
-class TocHeading:
+class TableOfContentsHeading:
     """目次の見出し1件を表す値オブジェクト."""
 
     text: str
@@ -35,10 +36,10 @@ class TocHeading:
 
 
 @dataclass(frozen=True)
-class TocResult:
+class TableOfContentsResult:
     """目次の生成結果を表す値オブジェクト."""
 
-    headings: tuple[TocHeading, ...]
+    headings: tuple[TableOfContentsHeading, ...]
```

指摘なし（2回目で通過）

### impl_external

#### 指摘: `text.split("\n")` で行分割しているため、CRLF (`\r\n`) 入力では各行末の `\r` が残り、`_parse_heading` がそれを見出しテキストとして保持する。結果として `TableOfContentsHeading.text` と `markdown` に `\r` が混入し、`- [Title\r](#title)` のように目次文字列が壊れる。Markdown テキストは Windows 改行でも受け取られ得るため、環境依存で出力が不正になる点が問題。`splitlines()` を使うか、見出し抽出前に行末の改行文字を正規化して `\r` を除去する方針で修正すべき。（major）
- **ファイル**: /Users/tsuryoryo/Desktop/repo/obsidian/backend/benchmark/markdown_toc.py:171
- **判断**: 修正
- **理由**: 1. `text.split("\n")` は CRLF 改行を正しく分割できず `\r` が見出しテキストに混入して目次出力が壊れるため、改行正規化が必要だった。
2. `_HEADING_PATTERN` の本文部分が `(.+)` だと空テキストの ATX 見出し（`# ` のみの行）を認識できず仕様より狭くなるため、`(.*)` に緩めて空見出しも許容した。
3. いずれも特定環境・特定入力でのみ顕在化するが、Markdown パーサとしての正確性と仕様準拠のために対応が必要と判断した。
- **修正内容**:
```diff
diff --git a/backend/benchmark/markdown_toc.py b/backend/benchmark/markdown_toc.py
index 53ca68d..afc85e4 100644
--- a/backend/benchmark/markdown_toc.py
+++ b/backend/benchmark/markdown_toc.py
@@ -5,7 +5,7 @@ from __future__ import annotations
 import re
 from dataclasses import dataclass
 
-_HEADING_PATTERN = re.compile(r"^(#{1,6})\s+(.+)$")
+_HEADING_PATTERN = re.compile(r"^(#{1,6})\s+(.*)$")
 _FENCE_PATTERN = re.compile(r"^(`{3,}|~{3,})")
 _ATX_CLOSING_PATTERN = re.compile(r"\s+#+\s*$")
 
@@ -20,13 +20,14 @@ _SLUG_KEEP_PATTERN = re.compile(
     r"[^a-z0-9\-_\u3040-\u309f\u30a0-\u30ff\u4e00-\u9fff]",
 )
 _CONSECUTIVE_HYPHENS_PATTERN = re.compile(r"-+")
+_SLUG_SEPARATOR = "-"
 
 _DEFAULT_MIN_LEVEL = 1
 _DEFAULT_MAX_LEVEL = 3
 
 
 @dataclass(frozen=True)
-class TocHeading:
+class TableOfContentsHeading:
     """目次の見出し1件を表す値オブジェクト."""
 
     text: str
@@ -35,10 +36,10 @@ class TocHeading:
```

#### 指摘: `_HEADING_PATTERN` が見出し本文に `(.+)` を要求しているため、`# ` のようにテキストが空の ATX 見出しを認識できない。仕様は「1〜6 個の `#` の直後に 1 つ以上のスペースがある行」を見出しとして扱う定義で、空本文を除外していないため、実装は仕様より狭い。結果として空見出しが `headings` と `markdown` から脱落し、後続の重複アンカー付番も実際の文書構造とずれる。本文部分は空文字を許可する形に緩め、ATX 末尾クロージング除去後に空文字でも見出しとして返すよう修正すべき。（major）
- **ファイル**: /Users/tsuryoryo/Desktop/repo/obsidian/backend/benchmark/markdown_toc.py:8
- **判断**: 修正
- **理由**: 1. `text.split("\n")` は CRLF 改行を正しく分割できず `\r` が見出しテキストに混入して目次出力が壊れるため、改行正規化が必要だった。
2. `_HEADING_PATTERN` の本文部分が `(.+)` だと空テキストの ATX 見出し（`# ` のみの行）を認識できず仕様より狭くなるため、`(.*)` に緩めて空見出しも許容した。
3. いずれも特定環境・特定入力でのみ顕在化するが、Markdown パーサとしての正確性と仕様準拠のために対応が必要と判断した。
- **修正内容**:
```diff
diff --git a/backend/benchmark/markdown_toc.py b/backend/benchmark/markdown_toc.py
index 53ca68d..afc85e4 100644
--- a/backend/benchmark/markdown_toc.py
+++ b/backend/benchmark/markdown_toc.py
@@ -5,7 +5,7 @@ from __future__ import annotations
 import re
 from dataclasses import dataclass
 
-_HEADING_PATTERN = re.compile(r"^(#{1,6})\s+(.+)$")
+_HEADING_PATTERN = re.compile(r"^(#{1,6})\s+(.*)$")
 _FENCE_PATTERN = re.compile(r"^(`{3,}|~{3,})")
 _ATX_CLOSING_PATTERN = re.compile(r"\s+#+\s*$")
 
@@ -20,13 +20,14 @@ _SLUG_KEEP_PATTERN = re.compile(
     r"[^a-z0-9\-_\u3040-\u309f\u30a0-\u30ff\u4e00-\u9fff]",
 )
 _CONSECUTIVE_HYPHENS_PATTERN = re.compile(r"-+")
+_SLUG_SEPARATOR = "-"
 
 _DEFAULT_MIN_LEVEL = 1
 _DEFAULT_MAX_LEVEL = 3
 
 
 @dataclass(frozen=True)
-class TocHeading:
+class TableOfContentsHeading:
     """目次の見出し1件を表す値オブジェクト."""
 
     text: str
@@ -35,10 +36,10 @@ class TocHeading:
```

#### 指摘: `_BOLD_UNDERSCORE_PATTERN` と `_ITALIC_UNDERSCORE_PATTERN` が単語内判定に `\w` を使っているため、Python では日本語も単語文字として扱われる。仕様の例外は `foo__bar__baz` / `foo_bar_baz` のような単語内アンダースコアだけを保持する意図だが、現状は `# 見出し__太字__です` や `# 見出し_強調_です` でも装飾が除去されない。結果として、対応対象である日本語見出しの `text` と `anchor` が仕様どおりに正規化されず、目次表示とリンク先が誤る。修正方針としては、lookaround の判定を Unicode の `\w` ではなく ASCII 英数字と `_` に限定した明示的な文字クラス（例: `[A-Za-z0-9_]`）に変更し、英数字の単語内ケースだけを保持して日本語隣接の `_..._` / `__...__` は除去されるようにするべき。（major）
- **ファイル**: /Users/tsuryoryo/Desktop/repo/obsidian/backend/benchmark/markdown_toc.py:15
- **判断**: 修正
- **理由**: Pythonの`\w`はUnicode対応のため日本語文字も「単語文字」と判定し、`見出し__太字__です`のようなケースでlookaroundが不一致となり装飾が除去されなかった。
`\w`を`[A-Za-z0-9_]`に限定することで、単語内アンダースコア保持の例外をASCII英数字の文脈(`foo__bar__baz`等)だけに制限し、日本語隣接の装飾記法は正しく除去されるようにした。
仕様の意図(英単語内のみ保持)とPythonの正規表現エンジンの挙動のギャップを埋める修正。
- **修正内容**:
```diff
diff --git a/backend/benchmark/markdown_toc.py b/backend/benchmark/markdown_toc.py
index 53ca68d..d3e3fea 100644
--- a/backend/benchmark/markdown_toc.py
+++ b/backend/benchmark/markdown_toc.py
@@ -5,28 +5,29 @@ from __future__ import annotations
 import re
 from dataclasses import dataclass
 
-_HEADING_PATTERN = re.compile(r"^(#{1,6})\s+(.+)$")
+_HEADING_PATTERN = re.compile(r"^(#{1,6})\s+(.*)$")
 _FENCE_PATTERN = re.compile(r"^(`{3,}|~{3,})")
 _ATX_CLOSING_PATTERN = re.compile(r"\s+#+\s*$")
 
 _LINK_PATTERN = re.compile(r"\[([^\]]*?)\]\([^)]*?\)")
 _CODE_PATTERN = re.compile(r"`([^`]*?)`")
 _BOLD_ASTERISK_PATTERN = re.compile(r"\*\*(.+?)\*\*")
-_BOLD_UNDERSCORE_PATTERN = re.compile(r"(?<!\w)__(.+?)__(?!\w)")
+_BOLD_UNDERSCORE_PATTERN = re.compile(r"(?<![A-Za-z0-9_])__(.+?)__(?![A-Za-z0-9_])")
 _ITALIC_ASTERISK_PATTERN = re.compile(r"\*(.+?)\*")
-_ITALIC_UNDERSCORE_PATTERN = re.compile(r"(?<!\w)_(.+?)_(?!\w)")
+_ITALIC_UNDERSCORE_PATTERN = re.compile(r"(?<![A-Za-z0-9_])_(.+?)_(?![A-Za-z0-9_])")
 
 _SLUG_KEEP_PATTERN = re.compile(
     r"[^a-z0-9\-_\u3040-\u309f\u30a0-\u30ff\u4e00-\u9fff]",
 )
 _CONSECUTIVE_HYPHENS_PATTERN = re.compile(r"-+")
+_SLUG_SEPARATOR = "-"
 
 _DEFAULT_MIN_LEVEL = 1
 _DEFAULT_MAX_LEVEL = 3
```

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
| レビューサイクル総数 | 14回（修正による再実行を含む） |
| 修正した指摘数 | 23件 |
| 通過ステップ数 | 5件 |
| 事前定義の設計判断 | 3件 |
| レビュー中に許容 | 0件 |
