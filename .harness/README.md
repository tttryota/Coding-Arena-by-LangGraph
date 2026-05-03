# @tsuryoryo/tdd-harness

LLM CLI を使った TDD 自動化オーケストレーター。
Claude Code / Codex / GitHub Copilot CLI など任意の LLM CLI をプラガブルに差し替え可能。

## セットアップ

```bash
npm install @tsuryoryo/tdd-harness
# or
pnpm add @tsuryoryo/tdd-harness
```

前提条件:
- Node.js 22.18+
- `claude` CLI が PATH に存在（デフォルトの全ステップで使用。他の CLI のみ使う場合は `.harness.yml` で `runners` と `steps` を明示設定）
- プロジェクトに応じた lint/test ツール（Python: ruff + mypy + pytest、TypeScript: eslint + tsc + vitest）

セットアップガイドを表示:
```bash
tdd-harness init
```

## 設定

プロジェクトルートに `.harness.yml` を配置:

### プロファイル

```yaml
profiles:
  backend:
    lint: [ruff, mypy]
    test: pytest
    toolRoot: backend
    criteriaPreset: backend
    sourceLayout:
      sourceDir: "backend/{{category}}"
      testDir: "backend/{{category}}/tests"
      scopePattern: "backend/{{category}}/*"
  frontend:
    lint: [eslint, tsc]
    test: vitest
    toolRoot: frontend
    criteriaPreset: frontend
    sourceLayout:
      sourceDir: "frontend/src/{{category}}"
      testDir: "frontend/src/{{category}}/__tests__"
      scopePattern: "frontend/src/{{category}}/*"
```

### ランナー・ステップ割り当て

```yaml
runners:
  claude:
    type: claude
  codex:
    type: codex
    sandbox: read-only
  copilot:
    type: generic
    command: gh
    args: ["copilot"]
    promptFlag: "--prompt"

flow: full          # full | light
fallbackRunner: claude

steps:
  test_generate: claude
  test_self_quality: claude
  test_external_review: codex
  impl_generate: claude
  impl_self_criteria: claude
  impl_self_quality: copilot     # ステップごとに差し替え可能
  impl_external_review: codex
  lint_fix: claude
  apply_fixes: claude
  judgment_summary: claude
  judge_minor: claude
```

`.harness.yml` に `profiles` が定義されていない場合はエラーになる。`tdd-harness init` でセットアップガイドを表示できる。

## 使い方

### Design Flow（仕様書・テストケース生成）

```bash
tdd-harness design ingestion/chunk-splitter "Markdownをチャンク分割する機能"
```

1. 仕様書を生成（`docs/spec/{category}/{name}.md`）
2. 人間が確認し、必要なら修正後に再実行して `status: ready` にする
3. 再実行するとテストケースを生成
4. 人間が確認し、必要なら修正後に再実行して `status: ready` にする

### Impl Flow（TDD 実装）

```bash
tdd-harness impl plan/current-task.md
tdd-harness component plan/components-task.md
tdd-harness page plan/page-task.md
```

実行前に対話的にステップごとのランナー割り当てを確認・変更できる:

```
フロー: full
ステップ割り当て:
  1. test_generate: claude
  2. test_self_quality: claude
  3. test_external_review: codex
  ...

変更するステップ番号を入力 (Enter でそのまま実行):
```

#### フロー

| ステップ | full | light |
|---|---|---|
| テスト生成 | o | o |
| テストセルフレビュー | o | o |
| テスト外部レビュー | o | 省略 |
| RED 確認 | o | o |
| 実装生成 | o | o |
| GREEN 確認 | o | o |
| 実装セルフレビュー(criteria) | o | o |
| 実装セルフレビュー(quality) | o | o |
| 実装外部レビュー | o | 省略 |

```bash
# light フロー
tdd-harness impl plan/task.md --flow light

# 対話プロンプトをスキップ
tdd-harness impl plan/task.md --no-interactive

# チェックポイントから再開
tdd-harness impl plan/task.md --resume
```

### Page Flow（Page UI 実装）

```bash
tdd-harness page plan/page-task.md
```

- page 実装を生成
- lint / typecheck / page テストを実行
- 3観点レビュー（design / behavior / code quality）を最大5サイクル実行
- Browser Verification を最後に1回実行
- fail した場合は修正後にレビューへ戻る

### Component Flow（Component + Story 実装）

```bash
tdd-harness component plan/components-task.md
```

- `Targets` を 1 件ずつ順に処理
- component と Story を同時生成
- lint / typecheck / story smoke / セルフレビューを実行
- target ごとに最大 2 回修正
- 終了時に `未収束 target: N` を標準出力へ表示

## 計画ファイルのフォーマット

```markdown
---
profile: backend
scope: ingestion/chunk-splitter
spec: docs/spec/ingestion/chunk-splitter.md
test_cases: tests/test-cases/ingestion/chunk-splitter.md
---

## 今回やること
chunk-splitter の Phase 1 を実装する

## 対象テストケース
1. 空ファイルを渡すと空リストが返る
2. 見出しなしファイルは1チャンクになる

## やらないこと
- Phase 2以降

## 完了条件
- 上記テストが GREEN
- lint パス

## 設計判断
- カテゴリ単位のlint拡大は import 解決のため許容
```

profile が 1 つだけの場合は frontmatter の `profile:` を省略可能。

## scope の命名規則

`カテゴリ/名前` 形式（例: `ingestion/chunk-splitter`）。
英数字とハイフンのみ使用可能。

## 利用可能なツール

### lint adapter

| 名前 | runtime | filePass | 説明 |
|---|---|---|---|
| ruff | python | files | Python linter/formatter |
| mypy | python | files | Python 型チェッカー |
| eslint | node | files | JavaScript/TypeScript linter |
| tsc | node | project | TypeScript 型チェッカー |

### test adapter

| 名前 | runtime | 説明 |
|---|---|---|
| pytest | python | Python テストフレームワーク |
| vitest | node | JavaScript/TypeScript テストフレームワーク |

## アーキテクチャ

```
harness（CLI エントリポイント）
  ├── config（.harness.yml 読み込み + プロファイル解決）
  ├── runner-registry（ステップ → ランナー解決）
  │   ├── claude-runner（claude -p ラッパー）
  │   ├── codex-runner（codex exec ラッパー）
  │   └── generic-runner（任意 CLI ラッパー）
  ├── interactive（対話的ランナー割り当て）
  ├── boundary（パス検証・スコープ解決・ガード）
  ├── design-flow（仕様書・テストケース生成）
  ├── impl-flow（TDD 実装サイクル + リトライ）
  ├── page-flow（Page UI 実装 + ブラウザ検証）
  │   ├── lint-guard（lint adapter ゼロ違反強制）
  │   ├── drift-guard（迷走検知 + エスカレーション）
  │   └── review-orchestrator（レビューサイクル管理）
  ├── templates（プロンプトテンプレート）
  ├── logger（JSONL 構造化ログ + redact）
  └── types（共有型定義）
```

## レビュー観点のカスタマイズ

レビュープロンプトはテンプレートファイルとして外部化されています。
プロジェクトの `.harness/templates/` に同名ファイルを配置すると上書きできます。

テンプレート内では `{{変数名}}` でプレースホルダ置換が行われます。

同梱テンプレート:
- `review-response-format.md` — レビュー回答形式の共通指示
- `review-test-quality.md` — テストセルフレビュー
- `review-impl-quality.md` — 実装品質レビュー
- `review-impl-criteria.md` — レビュー観点チェック
- `review-codex-test.md` — テスト外部レビュー
- `review-codex-impl.md` — 実装外部レビュー
- `review-dual-fallback.md` — フォールバックレビュー
- `test-generate.md` — テスト生成プロンプト
- `impl-generate.md` — 実装生成プロンプト
- `impl-retry.md` — 実装リトライプロンプト

## 安全機構

- **パス検証**: symlink 解決 + プロジェクトルート境界チェック
- **スコープ制限**: ランナーの capabilities に応じた権限制御
- **変更検証**: `git diff` でスコープ外変更を検出
- **fail-closed**: パース失敗・コマンド失敗は全てエラーとして停止
- **迷走検知**: テストリトライ上限、同一エラー連続検出、タイムアウト、diff 肥大化
- **ログ redact**: API キー・トークンパターンを自動除去
- **sandbox**: Codex ランナーのデフォルトは `read-only`

## レビューレポート

impl フロー完了時に `docs/reviews/{date}_{scope}.md` を自動生成。

レポート内容:
- TDD サイクルの結果
- 各レビューステップの指摘と対応（修正 / 許容 / エスカレーション）
- 判断理由の要約
- 設計判断の記録

## ログ

`logs/{timestamp}_{task_name}/` に出力:

- `harness.jsonl` — イベントログ
- `claude-code.log` — Claude CLI の入出力
- `review-data.json` — レビュー構造化データ
- `checkpoint.json` — 再開用チェックポイント

## ライセンス

MIT
