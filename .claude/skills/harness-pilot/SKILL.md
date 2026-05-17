---
description: 'TDD ハーネスのワークフローを自律実行する。使用場面: (1) ハーネスで機能実装、(2) ハーネスで仕様策定、(3) ハーネスの使い方の質問。トリガー: "/harness-pilot", "ハーネスで", "ハーネスの"'
name: harness-pilot
---
# TDD ハーネス — Pilot リファレンス

このプロジェクトの TDD ハーネスを正しく操作するための知識ベース。
ユーザーの意図に応じて、適切なコマンドを判断・実行する。

## まず押さえること

- この repo では `./.harness/harness` が実行入口
- `profile` は lint / test / sourceLayout を選ぶ設定であり、LLM サービス選択には使わない
- どの LLM をどのステップで使うかは `.harness/harness.yml` または `.harness.yml` の `runners` と `steps` で切り替える
- `type: codex` は現在 `codex app-server` バックエンド
- フロントエンドフローは `component` / `impl` / `page` と `/harness-plan-fe` が現役

## コマンドリファレンス

| コマンド | 用途 | 引数 |
|---|---|---|
| `./.harness/harness design <category/name> "<要件>"` | 仕様書 / テストケース生成 | scope 形式の名前 + 要件テキスト |
| `./.harness/harness impl <plan-file> [--resume] [--flow full\|light] [--no-interactive]` | TDD 実装（BE + FE Logic） | plan ファイルパス |
| `./.harness/harness component <plan-file> [--flow full\|light] [--no-interactive]` | コンポーネント + Story 生成 | plan ファイルパス |
| `./.harness/harness page <plan-file> [--flow full\|light] [--no-interactive]` | ページ組み立て + 3観点レビュー | plan ファイルパス |
| `./.harness/harness benchmark-summary <log-dir> [<log-dir>]` | ベンチマーク比較サマリ生成 | 1つまたは2つのログディレクトリ |
| `/harness-plan-fe <spec-path>` | FE plan 群を対話的に生成 | 仕様書パス（Claude Code skill） |

## ワークフロー

### バックエンド
1. `./.harness/harness design <category/name> "<要件>"` → 仕様書 + テストケース生成
2. 人間が plan.md を作成（frontmatter: type, profile, scope, spec, test_cases）
3. `./.harness/harness impl <plan-file>` → テスト生成 → RED → 実装 → GREEN → レビュー

### フロントエンド
1. ready の仕様書 / コンポーネント定義書 / Figma キャッシュ / 必要ならテストケースを用意する
2. `/harness-plan-fe <spec-path>` → plan 群を対話的に生成
3. `./.harness/harness component <plan>` → コンポーネント + Story 生成
4. `./.harness/harness impl <plan>` → Logic（hooks/atoms/API）を TDD で実装
5. `./.harness/harness page <plan>` → ページ組み立て + 3観点レビュー + ブラウザ検証

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

- `profile` は runtime 別の lint / test / sourceLayout を選ぶ
- reviewer の LLM サービスは `steps.test_external_review` / `steps.impl_external_review` などで選ぶ
- `runners.<name>.type: claude|codex|generic` を複数定義して、step ごとに差し替える
- Claude reviewer をモデル違いで分けたい場合は `runners` 側で別名 runner を作る

| profile | lint | test | toolRoot | sourceLayout |
|---|---|---|---|---|
| backend | ruff, mypy | pytest | backend | `backend/{{category}}` |
| frontend | eslint, tsc | vitest | frontend | `frontend/src/{{category}}/{{name}}` |

### reviewer 切り替え例

```yaml
runners:
  claude:
    type: claude
  claude-opus-review:
    type: claude
    model: opus
  codex:
    type: codex
    sandbox: read-only

steps:
  test_generate: claude
  test_external_review: codex
  impl_generate: claude
  impl_external_review: claude-opus-review
```

## ログと成果物

### logs/ ディレクトリ
フロー実行ごとに `{timestamp}_{flowType}_{scope}/` が作られる:
- `harness.jsonl` — イベントログ（JSONL 形式）
- `claude-code.log` — Claude CLI の入出力ログ
- `codex-app-server.log` — Codex App Server の transcript（使用時のみ）
- `review-data.json` — レビュー記録の構造化データ（全 cycle の findings, decision, diff）
- `checkpoint.json` — 中断再開用チェックポイント

### docs/reviews/ ディレクトリ
impl フロー完了時にレビューレポート（Markdown）が自動生成される:
- ファイル名: `{timestamp}_{scope}.md`
- 内容: テストケース一覧、TDD サイクル結果、レビュー指摘と修正内容、設計判断記録

### チェックポイントと再開
`./.harness/harness impl <plan> --resume` で中断箇所から再開可能。
resume は `logs/checkpoint_{taskName}.json` を参照し、ログディレクトリ内にも `checkpoint.json` を保存する。

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
| Codex reviewer が動かない | `codex app-server` が起動可能か、`sandbox` 設定が妥当か確認 |
