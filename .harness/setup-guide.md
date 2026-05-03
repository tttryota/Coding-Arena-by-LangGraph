# tdd-harness セットアップガイド

## インストール

```bash
npm install @tsuryoryo/tdd-harness
# or
pnpm add @tsuryoryo/tdd-harness
```

前提:
- Node.js 22.18+
- `claude` CLI が PATH に存在（デフォルトの全ステップで使用。他の CLI のみ使う場合は `.harness.yml` で `runners` と `steps` を明示設定）
- プロジェクトに応じた lint/test ツール

## 設定ファイル

プロジェクトルートに `.harness.yml` を作成。

### 例1: Python バックエンド

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
```

### 例2: TypeScript プロジェクト

```yaml
profiles:
  app:
    lint: [eslint, tsc]
    test: vitest
    toolRoot: .
    criteriaPreset: frontend
    sourceLayout:
      sourceDir: "src/{{category}}"
      testDir: "src/{{category}}/__tests__"
      scopePattern: "src/{{category}}/*"
```

### 例3: 複数プロファイル

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
  frontend:
    lint: [eslint, tsc]
    test: vitest
    toolRoot: frontend
    criteriaPreset: frontend
    sourceLayout:
      sourceDir: "frontend/src/{{category}}"
      testDir: "frontend/src/{{category}}/__tests__"

runners:
  claude:
    type: claude
  codex:
    type: codex
    sandbox: read-only
```

`profiles` は必須。未定義の場合はエラーになる。`tdd-harness init` でこのガイドを表示できる。

## 利用可能なツール

### lint adapter

| ツール | runtime | filePass | 説明 |
|---|---|---|---|
| ruff | python | files | Python linter/formatter |
| mypy | python | files | Python 型チェッカー |
| eslint | node | files | JavaScript/TypeScript linter |
| tsc | node | project | TypeScript 型チェッカー |

### test adapter

| ツール | runtime | 説明 |
|---|---|---|
| pytest | python | Python テストフレームワーク |
| vitest | node | JavaScript/TypeScript テストフレームワーク |

## ランナー

| type | 説明 |
|---|---|
| claude | Claude Code CLI (`claude -p`) |
| codex | OpenAI Codex CLI (`codex exec`) |
| generic | 任意の CLI コマンド |

### generic runner の設定

| フィールド | 必須 | 説明 |
|---|---|---|
| command | o | 実行する CLI コマンド |
| args | o | コマンドの固定引数（配列） |
| promptFlag | - | プロンプトを渡すフラグ（例: `-p`）。未指定時は stdin にプロンプトを流す |
| timeoutMs | - | タイムアウト（ミリ秒） |

```yaml
runners:
  copilot:
    type: generic
    command: gh
    args: ["copilot"]
    promptFlag: "--prompt"
```

non-interactive 実行にはツール側の権限設定が必要な場合があります（例: Copilot CLI の `--allow-all-tools`）。

## 計画ファイルの書き方

```markdown
---
profile: backend
scope: ingestion/chunk-splitter
spec: docs/spec/ingestion/chunk-splitter.md
test_cases: tests/test-cases/ingestion/chunk-splitter.md
---

## 今回やること
（実装内容の説明）

## 対象テストケース
1. テストケース1
2. テストケース2

## やらないこと
- スコープ外の項目

## 完了条件
- テストが GREEN
- lint パス

## 設計判断
- 判断とその理由
```

profile が 1 つだけの場合は frontmatter の `profile:` を省略可能。

## scope の命名規則

`カテゴリ/名前` 形式（例: `ingestion/chunk-splitter`）。
英数字とハイフンのみ使用可能。

## フロー

### Design Flow（仕様書・テストケース生成）

```bash
tdd-harness design ingestion/chunk-splitter "Markdownをチャンク分割する機能"
```

### Impl Flow（TDD 実装）

```bash
tdd-harness impl plan/task.md
tdd-harness impl plan/task.md --flow light    # 外部レビュー省略
tdd-harness impl plan/task.md --resume        # チェックポイントから再開
tdd-harness impl plan/task.md --no-interactive # 対話プロンプトスキップ
```

## プロファイル設定項目

| フィールド | 型 | 説明 |
|---|---|---|
| lint | string[] | lint ツール名の配列 |
| test | string | test ツール名 |
| toolRoot | string | ツール実行時のルートディレクトリ |
| exec | string[] | ツール実行時のプレフィクス（例: `[poetry, run]`） |
| criteriaPreset | "backend" \| "frontend" | レビュー観点のプリセット |
| reviewCriteria | string[] | カスタムレビュー観点ファイルパス |
| sourceLayout | object | ソースコードのディレクトリ構成 |

### sourceLayout

| フィールド | 説明 | 例 |
|---|---|---|
| sourceDir | ソースディレクトリ | `backend/{{category}}` |
| testDir | テストディレクトリ | `backend/{{category}}/tests` |
| scopePattern | スコープパターン | `backend/{{category}}/*` |
| additionalAllowedPrefixes | 追加の許可パス | `["docs/reviews/"]` |

`{{category}}` と `{{name}}` がスコープの値で置換される。
