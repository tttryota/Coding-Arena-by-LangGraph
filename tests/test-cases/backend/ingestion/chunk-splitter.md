---
status: ready
---

# テストケース一覧

# 検証焦点

| テストの種類 | 検証焦点 |
|---|---|
| Phase 1（最小骨格） | `content` / `heading_path` / `token_count` の基本返却形 |
| Phase 2（コアロジック） | 一次分割、二次分割、コードブロック保護、テキスト保存 |
| Phase 3（エッジケース） | 空入力、フロントマター境界、不可分単位超過、未閉鎖ブロック |
| Phase 4（外部連携） | 依存インターフェース検証、例外送出、可観測性 |

## Phase 1: 最小骨格

| ID | 観点 | 前提 | 入力 | 期待結果 | 備考 |
|---|---|---|---|---|---|
| TC-01 | H1 配下の最小チャンクを 1 件返す | `token_counter.count("# Docker\n\n概要") = 12` | `markdown_text = "# Docker\n\n概要"` | `[{content: "# Docker\n\n概要", heading_path: ["Docker"], token_count: 12}]` を出現順で返す | 全フィールドの最小正常系 |
| TC-02 | H1/H2 が存在しない本文は全体を 1 チャンクにする | `token_counter.count("本文のみ\n\n[[リンク先]]") = 18` | `markdown_text = "本文のみ\n\n[[リンク先]]"` | `[{content: "本文のみ\n\n[[リンク先]]", heading_path: [], token_count: 18}]` を返す | `heading_path` 空配列の基本確認 |
| TC-03 | 空ファイルは空リストを返す | なし | `markdown_text = ""` | `[]` を返す | 最小境界 |

## Phase 2: コアロジック

| ID | 観点 | 前提 | 入力 | 期待結果 | 備考 |
|---|---|---|---|---|---|
| TC-10 | 先頭 YAML フロントマターを除外し、H1/H2 で一次分割し、H3 は親チャンクに保持する | `token_counter.count("# TypeScript\nIntro\n\n### Generics\nT extends U") = 120`、`token_counter.count("## Utility Types\nPick と Omit") = 65` | `markdown_text = "---\ntitle: TS Notes\ntags:\n  - study\n---\n\n# TypeScript\nIntro\n\n### Generics\nT extends U\n\n## Utility Types\nPick と Omit"` | 1件目 `{content: "# TypeScript\nIntro\n\n### Generics\nT extends U", heading_path: ["TypeScript"], token_count: 120}`、2件目 `{content: "## Utility Types\nPick と Omit", heading_path: ["TypeScript", "Utility Types"], token_count: 65}` をこの順で返す | 仕様書 例1 に対応 |
| TC-11 | 一次チャンクが 512 トークン超過時に段落単位で二次分割し、各サブチャンク先頭へ親見出しを再付与する | `token_counter.count("# Docker\n\n段落A\n\n段落B") = 430`、`token_counter.count("# Docker\n\n段落A\n\n段落B\n\n段落C") = 620`、`token_counter.count("# Docker\n\n段落C") = 210` | `markdown_text = "# Docker\n\n段落A\n\n段落B\n\n段落C"` | 1件目 `{content: "# Docker\n\n段落A\n\n段落B", heading_path: ["Docker"], token_count: 430}`、2件目 `{content: "# Docker\n\n段落C", heading_path: ["Docker"], token_count: 210}` を返す | 仕様書 例2 に対応 |
| TC-12 | コードブロック内の見出し様テキストを境界にせず、本文中の `---` を保持し、512 超の単一コードブロックは分割しない | `token_counter.count("# Python\n\n```python\n# this is not a heading\nprint(\"a\")\nprint(\"b\")\n```") = 540`、`token_counter.count("# Python\n\n---\n\n本文") = 40` | `markdown_text = "# Python\n\n```python\n# this is not a heading\nprint(\"a\")\nprint(\"b\")\n```\n\n---\n\n本文"` | 1件目 `{content: "# Python\n\n```python\n# this is not a heading\nprint(\"a\")\nprint(\"b\")\n```", heading_path: ["Python"], token_count: 540}`、2件目 `{content: "# Python\n\n---\n\n本文", heading_path: ["Python"], token_count: 40}` を返す | 仕様書 例3 に対応 |
| TC-13 | 親 H1 を持たない H2 は `heading_path = [H2]` とする | `token_counter.count("## Utility Types\nPick と Omit") = 65` | `markdown_text = "## Utility Types\nPick と Omit"` | `[{content: "## Utility Types\nPick と Omit", heading_path: ["Utility Types"], token_count: 65}]` を返す | 入出力契約の H2 単独ケース |
| TC-14 | 二次分割時も見出し行を直後のコードブロックから分離しない | `token_counter.count("# Python\n\n```python\nprint(\"a\")\n```\n\n説明段落") = 620`、`token_counter.count("# Python\n\n```python\nprint(\"a\")\n```") = 350`、`token_counter.count("# Python\n\n説明段落") = 120` | `markdown_text = "# Python\n\n```python\nprint(\"a\")\n```\n\n説明段落"` | 1件目 `{content: "# Python\n\n```python\nprint(\"a\")\n```", heading_path: ["Python"], token_count: 350}`、2件目 `{content: "# Python\n\n説明段落", heading_path: ["Python"], token_count: 120}` を返す | 二次分割ルールの「見出し行は直後の本文またはコードブロックと分離しない」を単独確認 |
| TC-15 | Obsidian 内部リンクは解決・変換せず本文文字列として保持する | `token_counter.count("# References\n\n[[リンク先]] と [[別ノート|表示名]] を見る") = 55` | `markdown_text = "# References\n\n[[リンク先]] と [[別ノート|表示名]] を見る"` | `[{content: "# References\n\n[[リンク先]] と [[別ノート|表示名]] を見る", heading_path: ["References"], token_count: 55}]` を返す | テキスト保存ルール専用 |

## Phase 3: エッジケース

| ID | 観点 | 前提 | 入力 | 期待結果 | 備考 |
|---|---|---|---|---|---|
| TC-20 | 空白文字のみのファイルは空リストを返す | なし | `markdown_text = " \n\t\n"` | `[]` を返す | 空ファイルとは別境界 |
| TC-21 | フロントマター除外後に本文が空なら空リストを返す | なし | `markdown_text = "---\ntitle: only-meta\n---\n"` | `[]` を返す | フロントマターのみファイル |
| TC-22 | H3/H4/H5/H6 のみで H1/H2 がない本文は全体を 1 チャンクにする | `token_counter.count("### Generics\nT extends U\n\n#### Constraint\nextends を使う") = 90` | `markdown_text = "### Generics\nT extends U\n\n#### Constraint\nextends を使う"` | `[{content: "### Generics\nT extends U\n\n#### Constraint\nextends を使う", heading_path: [], token_count: 90}]` を返す | H3 以下は境界を作らない |
| TC-23 | 先頭 `---` に閉じ行がない場合はフロントマターとして除外しない | `token_counter.count("---\ntitle: draft\n本文") = 30` | `markdown_text = "---\ntitle: draft\n本文"` | `[{content: "---\ntitle: draft\n本文", heading_path: [], token_count: 30}]` を返す | フロントマター閉じ忘れ |
| TC-24 | 一次チャンクが 512 トークンを超えても段落境界がなければそのまま 1 件返す | `token_counter.count("# Docker\n\n段落A 段落B 段落C") = 620` | `markdown_text = "# Docker\n\n段落A 段落B 段落C"` | `[{content: "# Docker\n\n段落A 段落B 段落C", heading_path: ["Docker"], token_count: 620}]` を返す | 単一段落由来の best-effort 超過も兼ねる |
| TC-25 | 開始フェンスのみで閉じフェンスがない場合はファイル末尾までコードブロックとして扱う | `token_counter.count("# Before\n\n```python\n## これは見出しではない\nprint(\"x\")") = 160` | `markdown_text = "# Before\n\n```python\n## これは見出しではない\nprint(\"x\")"` | `[{content: "# Before\n\n```python\n## これは見出しではない\nprint(\"x\")", heading_path: ["Before"], token_count: 160}]` を返す | 未閉鎖コードブロック |

## Phase 4: 外部連携

| ID | 観点 | 前提 | 入力 | 期待結果 | 備考 |
|---|---|---|---|---|---|
| TC-30 | `markdown_text` が文字列以外なら `ChunkSplitInputError` を送出する | `token_counter` は正常な `count(text: str) -> int` を提供する | `markdown_text = 123` | `ChunkSplitInputError` を送出し、結果リストを返さない | 入力型エラー |
| TC-31 | `token_counter` が `count(text: str) -> int` 契約を満たさない場合は `ChunkSplitInputError` を送出する | `token_counter` に `count` メソッドが存在しない、または呼び出し不能 | `markdown_text = "# Docker\n\n概要"` | `ChunkSplitInputError` を送出し、結果リストを返さない | 依存インターフェース検証 |
| TC-32 | `token_counter.count()` が例外を送出した場合は `TokenCountError` を送出する | `token_counter.count()` が最初の候補チャンク計測時に例外を送出する | `markdown_text = "# Docker\n\n概要"` | `TokenCountError` を送出し、部分的な結果リストを返さない | 計測失敗 |
| TC-33 | `token_counter.count()` が負数を返した場合は `TokenCountError` を送出する | `token_counter.count("# Docker\n\n概要") = -1` | `markdown_text = "# Docker\n\n概要"` | `TokenCountError` を送出し、結果リストを返さない | 契約違反値 |
| TC-34 | `token_counter.count()` が非整数を返した場合は `TokenCountError` を送出する | `token_counter.count("# Docker\n\n概要") = "12"` | `markdown_text = "# Docker\n\n概要"` | `TokenCountError` を送出し、結果リストを返さない | 契約違反型 |
| TC-35 | 呼び出し元が総チャンク数と 512 トークン超過チャンク数を観測できる | ログまたはメトリクス収集を有効化し、`token_counter` の計測結果は TC-12 と同じ | `markdown_text = "# Python\n\n```python\n# this is not a heading\nprint(\"a\")\nprint(\"b\")\n```\n\n---\n\n本文"` | 非エラーで 2 チャンクを返し、かつ呼び出し元から `総チャンク数 = 2` と `512 トークン超過チャンク数 = 1` を観測できる | 可観測性の非機能要件 |

# 網羅性チェック

仕様書の受け入れ基準の各項目に対応するテストケース ID を記載する。
全項目が少なくとも1つのテストケースでカバーされていることを確認する。

| 受け入れ基準 | 対応テストケース |
|---|---|
| ファイル先頭の YAML フロントマターのみが除外され、本文中の `---` は本文として残る | TC-10, TC-12, TC-21, TC-23 |
| H1 / H2 でチャンクが分割され、H3 / H4 / H5 / H6 では新規チャンクが作られない | TC-10, TC-22 |
| コードブロック内の見出し様テキストは境界として扱われない | TC-12, TC-25 |
| 空ファイルと空白のみファイルは空リストになる | TC-03, TC-20 |
| H1 / H2 が存在しない本文は1チャンクで返る | TC-02, TC-22, TC-23 |
| 一次チャンクが 512 トークンを超えた場合、段落単位で順序を保って再分割される | TC-11, TC-14 |
| 再分割後の各サブチャンクは理解に必要な親見出しを先頭に含む | TC-11, TC-14 |
| 単一コードブロックが 512 トークンを超える場合でも、そのコードブロックは分割されない | TC-12 |
| `[[リンク先]]` は本文テキストとして変換されずに残る | TC-02, TC-15 |
| 各返却チャンクの `token_count` は `multilingual-e5-large` トークナイザの計測値と一致する | TC-01, TC-10, TC-11, TC-12, TC-13, TC-14, TC-15, TC-22, TC-23, TC-24, TC-25 |

# 記述ルール

- 仕様書に明記された振る舞いだけを前提にする
- 仕様未記載の振る舞いを期待結果に置く場合は `[要仕様追記]` タグを付ける
- 正常系・境界系・異常系が重複なく網羅されていることを確認する
- 仕様書の受け入れ基準の各項目に対応するテストケースが最低1つあることを確認する
