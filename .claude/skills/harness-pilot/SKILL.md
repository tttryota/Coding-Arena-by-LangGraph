---
description: 'TDD ハーネスのワークフローを自律実行する。使用場面: (1) ハーネスで機能実装、(2) ハーネスで仕様策定、(3) ハーネスの使い方の質問。トリガー: "/harness-pilot", "ハーネスで", "ハーネスの"'
name: harness-pilot
---
# TDD ハーネス — Pilot リファレンス

このプロジェクトの TDD ハーネスを正しく操作するための知識ベース。
ユーザーの意図に応じて、適切なコマンドを判断・実行する。

## コマンドリファレンス

| コマンド | 用途 | 引数 |
|---|---|---|
| `tdd-harness design <category/name> "<要件>"` | BE 仕様策定 | scope 形式の名前 + 要件テキスト |
| `tdd-harness design-fe <feature> "<要件>" --figma <url>` | FE 仕様策定（Figma 連携） | feature 名 + 要件 + Figma URL |
| `tdd-harness impl <plan-file> [--resume] [--flow full\|light]` | TDD 実装（BE + FE Logic） | plan ファイルパス |
| `tdd-harness component <plan-file>` | コンポーネント + Story 生成 | plan ファイルパス |
| `tdd-harness page <plan-file>` | ページ組み立て + 3観点レビュー | plan ファイルパス |
| `/harness-plan-fe <spec-path>` | FE plan 群を対話的に生成 | 仕様書パス（Claude Code skill） |

## ワークフロー

### バックエンド
1. `tdd-harness design <category/name> "<要件>"` → 仕様書 + テストケース生成
2. 人間が plan.md を作成（frontmatter: type, profile, scope, spec, test_cases）
3. `tdd-harness impl <plan-file>` → テスト生成 → RED → 実装 → GREEN → レビュー

### フロントエンド
1. `tdd-harness design-fe <feature> "<要件>" --figma <url>` → 仕様書 + コンポーネント定義書生成
2. `/harness-plan-fe <spec-path>` → plan 群を対話的に生成
3. `tdd-harness component <plan>` → コンポーネント + Story 生成
4. `tdd-harness impl <plan>` → Logic（hooks/atoms/API）を TDD で実装
5. `tdd-harness page <plan>` → ページ組み立て + 3観点レビュー + ブラウザ検証

## ステータス管理

| status | 意味 | 次のアクション |
|---|---|---|
| `needs_input` | [要確認] タグあり、人間の追記が必要 | 人間が追記して再実行 → LLM が検証 + 清書 |
| `ready` | 次工程へ進行可能 | 自動で次ステップへ。人間は異議があれば修正して再実行で差し戻せる |

ハーネスが [要確認] タグの有無で status を自動設定する。人間が手動で status を変更する必要はない。

## plan の構造

### frontmatter 必須フィールド
- 共通: `type`, `profile`, `scope`, `spec`
- Component: `component_spec`, `figma_cache`
- Logic: `test_cases`, `msw`
- Page: `component_spec`, `figma_cache`, `test_cases`, `msw`

### body セクション
`今回やること`, `Targets`, `Dependencies`, `Figma Slice`, `対象テストケース`, `やらないこと`, `完了条件`, `設計判断`

### Dependencies 形式
```yaml
- name: QuizCard
  import: "@/components/quiz/QuizCard"
```

### msw フラグ
API 呼び出しがある Logic/Page plan でのみ `msw: true`。Component plan では MSW 使用禁止。

## フロー間の責務境界

| フロー | 許可 | 禁止 |
|---|---|---|
| Component | Props → 描画、表示分岐、局所 UI state、Story | API、atom/global state、ビジネスロジック |
| Logic | hooks / atoms / API クライアント（.ts のみ） | JSX、コンポーネント定義 |
| Page | Component + Logic の接続、レイアウト | ロジック直接実装、新コンポーネント定義 |

## profile と設定

`.harness/harness.yml` を優先し、後方互換で `.harness.yml` も読み込む。そこに `backend` / `frontend` profile が定義されている。

| profile | lint | test | toolRoot | sourceLayout |
|---|---|---|---|---|
| backend | ruff, mypy | pytest | backend | `backend/{{category}}` |
| frontend | eslint, tsc | vitest | frontend | `frontend/src/{{category}}/{{name}}` |

## ログと成果物

### logs/ ディレクトリ
フロー実行ごとに `{timestamp}_{flowType}_{scope}/` が作られる:
- `harness.jsonl` — イベントログ（JSONL 形式）
- `claude-code.log` — Claude CLI の入出力ログ
- `codex-review.log` — Codex CLI の入出力ログ（使用時のみ）
- `review-data.json` — レビュー記録の構造化データ（全 cycle の findings, decision, diff）
- `checkpoint.json` — 中断再開用チェックポイント

### docs/reviews/ ディレクトリ
impl フロー完了時にレビューレポート（Markdown）が自動生成される:
- ファイル名: `{timestamp}_{scope}.md`
- 内容: テストケース一覧、TDD サイクル結果、レビュー指摘と修正内容、設計判断記録

### チェックポイントと再開
`tdd-harness impl <plan> --resume` で中断箇所から再開可能。
`logs/checkpoint_{taskName}.json` からステップと状態を復元する。

## 関連 skill

| skill | 呼び出し方 | 用途 |
|---|---|---|
| `/harness-plan-fe` | Skill ツールで呼び出す | FE 仕様書から plan 群を生成 |

FE ワークフローで仕様書が ready になった後、plan 生成が必要なタイミングで `/harness-plan-fe <spec-path>` を Skill ツールで呼び出す。

## 典型的なエラーと対処

| エラー | 対処 |
|---|---|
| レビュー発散（収束しない） | 各レビューステップのスコープ制約を確認 |
| Figma 取得失敗 | レート制限確認（200/日, 15/分） |
| RED で想定外エラー | MSW ハンドラの有無（msw フラグ）を確認 |
| frontend scope でエラー | plan に `profile: frontend` が指定されているか確認 |
| フロー中断 | `--resume` フラグで再開 |
