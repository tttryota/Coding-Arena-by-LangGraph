# tdd-harness セットアップガイド

## インストール

```bash
npm install @tsuryoryo/tdd-harness
# or
pnpm add @tsuryoryo/tdd-harness
```

前提:
- Node.js 22.18+
- `codex` CLI が PATH に存在（デフォルトの主フローで使用）
- `claude` CLI が PATH に存在（外部レビューを使う場合）
- プロジェクトに応じた lint/test ツール

## 設定ファイル

設定ファイルは `.harness/harness.json` を推奨（後方互換で `.harness.json` も読み込み可）。

### 例1: Python バックエンド

```json
{
  "profiles": {
    "backend": {
      "lint": ["ruff", "mypy"],
      "test": "pytest",
      "toolRoot": "backend",
      "criteriaPreset": "backend",
      "context": {
        "defaultContextBundles": ["backend-core"],
        "stepOverrides": {
          "test_generate": { "contextBundles": ["backend-test-generate"] },
          "impl_generate": { "contextBundles": ["backend-impl", "backend-failure-modes"] },
          "impl_self_criteria": { "contextBundles": ["backend-review-criteria"] },
          "impl_self_quality": { "contextBundles": ["backend-review-quality"] }
        }
      },
      "stepProviders": {
        "defaultProvider": "codex",
        "stepOverrides": {
          "test_external_review": "claude_opus",
          "impl_external_review": "claude_opus"
        }
      },
      "sourceLayout": {
        "sourceDir": "backend/{{category}}",
        "testDir": "backend/{{category}}/tests",
        "scopePattern": "backend/{{category}}/*"
      }
    }
  }
}
```

### 例2: TypeScript プロジェクト

```json
{
  "profiles": {
    "app": {
      "lint": ["eslint", "tsc"],
      "test": "vitest",
      "toolRoot": ".",
      "criteriaPreset": "frontend",
      "sourceLayout": {
        "sourceDir": "src/{{category}}/{{name}}",
        "testDir": "src/{{category}}/{{name}}/__tests__",
        "scopePattern": "src/{{category}}/{{name}}/*"
      }
    }
  }
}
```

### 例3: 複数プロファイル

```json
{
  "profiles": {
    "backend": {
      "lint": ["ruff", "mypy"],
      "test": "pytest",
      "toolRoot": "backend",
      "criteriaPreset": "backend",
      "sourceLayout": {
        "sourceDir": "backend/{{category}}",
        "testDir": "backend/{{category}}/tests"
      }
    },
    "frontend": {
      "lint": ["eslint", "tsc"],
      "test": "vitest",
      "toolRoot": "frontend",
      "criteriaPreset": "frontend",
      "sourceLayout": {
        "sourceDir": "frontend/src/{{category}}/{{name}}",
        "testDir": "frontend/src/{{category}}/{{name}}/__tests__",
        "scopePattern": "frontend/src/{{category}}/{{name}}/*"
      }
    }
  },
  "providers": {
    "codex": { "type": "codex", "sandbox": "workspace-write" },
    "claude_opus": { "type": "claude", "model": "opus" }
  },
  "context": {
    "contextBundles": {
      "backend-core": ["harness-backend-core"],
      "backend-test-generate": ["harness-backend-test"],
      "backend-impl": ["harness-backend-impl"]
    }
  }
}
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

## プロバイダ

| type | 説明 |
|---|---|
| claude | Claude Code CLI (`claude -p`) |
| codex | OpenAI Codex SDK（内部でローカル `codex` CLI を利用） |
| generic | 任意の CLI コマンド |

### generic provider の設定

| フィールド | 必須 | 説明 |
|---|---|---|
| command | o | 実行する CLI コマンド |
| args | o | コマンドの固定引数（配列） |
| promptFlag | - | プロンプトを渡すフラグ（例: `-p`）。未指定時は stdin にプロンプトを流す |
| timeoutMs | - | タイムアウト（ミリ秒） |

```yaml
providers:
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
```

non-interactive 実行にはツール側の権限設定が必要な場合があります（例: Copilot CLI の `--allow-all-tools`）。

## 計画ファイルの書き方

```markdown
---
profile: backend
benchmark: generation
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
`benchmark:` は任意で、`harness` または `generation` を指定できる。`generation` は開始時点で GREEN なら失格になる。

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
tdd-harness impl plan/task.md --profile backend_codex_only
tdd-harness impl plan/task.md --profile backend_claude_review
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
| stepProviders | object | profile 単位の provider 切り替え設定 |

### sourceLayout

| フィールド | 説明 | 例 |
|---|---|---|
| sourceDir | ソースディレクトリ | `backend/{{category}}` |
| testDir | テストディレクトリ | `backend/{{category}}/tests` |
| scopePattern | スコープパターン | `backend/{{category}}/*` |
| additionalAllowedPrefixes | 追加の許可パス | `["docs/reviews/"]` |

`{{category}}` と `{{name}}` がスコープの値で置換される。
