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
- `codex` CLI が PATH に存在（デフォルトの主フローで使用）
- `claude` CLI が PATH に存在（外部レビューを使う場合）
- プロジェクトに応じた lint/test ツール（Python: ruff + mypy + pytest、TypeScript: eslint + tsc + vitest）

セットアップガイドを表示:
```bash
tdd-harness init
```

## 設定

設定ファイルは `.harness/harness.yml` を推奨（後方互換で `.harness.yml` も読み込み可）:

### プロファイル

```yaml
profiles:
  backend:
    lint: [ruff, mypy]
    test: pytest
    toolRoot: backend
    criteriaPreset: backend
    context:
      defaultContextBundles: [backend-core]
      stepOverrides:
        test_generate:
          contextBundles: [backend-test-generate]
        impl_generate:
          contextBundles: [backend-impl, backend-failure-modes]
        impl_self_criteria:
          contextBundles: [backend-review-criteria]
        impl_self_quality:
          contextBundles: [backend-review-quality]
    stepProviders:
      defaultProvider: codex
      stepOverrides:
        test_external_review: claude_opus
        impl_external_review: claude_opus
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
      sourceDir: "frontend/src/{{category}}/{{name}}"
      testDir: "frontend/src/{{category}}/{{name}}/__tests__"
      scopePattern: "frontend/src/{{category}}/{{name}}/*"
      additionalAllowedPrefixes: ["docs/reviews/", "frontend/src/mocks/handlers/"]
    storybook:
      renderCommand: ["pnpm", "storybook", "build", "--test", "--docs", "--output-dir", ".storybook-static-{{target}}"]
      smokeCommand: ["pnpm", "storybook", "test", "--stories-json", "{{storyFile}}"]
```

### プロバイダ・ステップ割り当て

```yaml
providers:
  codex:
    type: codex
    sandbox: workspace-write
    heartbeatMs: 15000
    stallTimeoutMs: 180000
    capabilities: [session_resume]
    capabilityPolicy:
      session_resume: native
      system_prompt: degrade_to_prompt
      allowed_tools: degrade_to_prompt
      agent: reject
      mcp_config: reject
  claude:
    type: claude
    capabilities: [session_resume, system_prompt, allowed_tools, agent, mcp_config]
    capabilityPolicy:
      session_resume: native
      system_prompt: native
      allowed_tools: native
      agent: native
      mcp_config: native
  claude_opus:
    type: claude
    model: opus
    capabilities: [session_resume, system_prompt, allowed_tools, agent, mcp_config]
    capabilityPolicy:
      session_resume: native
      system_prompt: native
      allowed_tools: native
      agent: native
      mcp_config: native
  copilot:
    type: generic
    command: gh
    args: ["copilot"]
    promptFlag: "--prompt"
    capabilities: []
    capabilityPolicy:
      session_resume: reject
      system_prompt: degrade_to_prompt
      allowed_tools: degrade_to_prompt
      agent: reject
      mcp_config: reject

context:
  contextBundles:
    backend-core: [harness-backend-core]
    backend-test-generate: [harness-backend-test]
    backend-impl: [harness-backend-impl]
    backend-review-criteria: [harness-backend-review-criteria]
    backend-review-quality: [harness-backend-review-quality]
    backend-failure-modes: [harness-backend-failure-modes]

flow: full          # full | light

steps:
  test_generate: codex
  test_self_quality: codex
  test_external_review: claude_opus
  impl_generate: codex
  impl_self_criteria: codex
  impl_self_quality: copilot     # ステップごとに差し替え可能
  impl_external_review: claude_opus
  lint_fix: codex
  apply_fixes: codex
  judgment_summary: codex
  judge_minor: codex
```

`.harness/harness.yml`（または `.harness.yml`）に `profiles` が定義されていない場合はエラーになる。`tdd-harness init` でセットアップガイドを表示できる。

## 使い方

### Design Flow（仕様書・テストケース生成）

```bash
tdd-harness design ingestion/chunk-splitter "Markdownをチャンク分割する機能"
tdd-harness design ingestion/chunk-splitter "Markdownをチャンク分割する機能" --profile backend
```

1. 仕様書を生成（`docs/spec/{category}/{name}.md`）
2. 人間が確認し、必要なら修正後に再実行して `status: ready` にする
3. 再実行するとテストケースを生成
4. 人間が確認し、必要なら修正後に再実行して `status: ready` にする

### Impl Flow（TDD 実装）

```bash
tdd-harness impl plan/current-task.md
```

実行前に対話的にステップごとのプロバイダ割り当てを確認・変更できる。通常運用では profile を切り替えるだけで provider 構成ごと切り替えられる:

```
フロー: full
ステップ割り当て:
  1. test_generate: codex
  2. test_self_quality: codex
  3. test_external_review: claude_opus
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

# profile 切り替え
tdd-harness impl plan/task.md --profile backend_codex_only
tdd-harness impl plan/task.md --profile backend_claude_review

# 対話プロンプトをスキップ
tdd-harness impl plan/task.md --no-interactive

# チェックポイントから再開
tdd-harness impl plan/task.md --resume
```

```bash
tdd-harness component plan/components-task.md
tdd-harness page plan/page-task.md
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
- lint / typecheck / configured Storybook render + smoke / セルフレビューを実行
- target ごとに最大 2 回修正
- 終了時に `未収束 target: N` を標準出力へ表示
- Storybook コマンドは `profile.storybook.renderCommand` / `smokeCommand` で指定する
- 利用可能な変数: `{{target}}`, `{{storyFile}}`, `{{toolRoot}}`

## 計画ファイルのフォーマット

```markdown
---
profile: backend
benchmark: generation
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

`benchmark:` は任意で、`harness` または `generation` を指定できる。`generation` は `ALREADY_GREEN` を失格扱いにする。

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
  ├── config（.harness/harness.yml 優先で読み込み + プロファイル解決）
  ├── runner-registry（ステップ → ランナー解決）
  │   ├── claude-runner（claude -p ラッパー）
  │   ├── codex-runner（Codex SDK ラッパー）
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
- `benchmark-summary` — 生成済みログディレクトリから review/token/cost 指標を集計
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
- **sandbox**: Codex ランナーのデフォルトは `workspace-write`。必要に応じて `read-only` や `danger-full-access` に変更可能

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
