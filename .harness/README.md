# 開発ハーネス

AI（Claude Code + Codex）を使った TDD 自動化オーケストレーター。

## セットアップ

```bash
cd .harness
pnpm install
```

前提条件:
- Node.js 22.18+
- pnpm
- Claude Code CLI（`claude` コマンドが PATH に存在）
- Python 環境: ruff, mypy, pytest
- （任意）Codex CLI（`codex` コマンド）

## 使い方

### Design Flow（仕様書・テストケース生成）

```bash
./harness design ingestion/chunk-splitter "Markdownをチャンク分割する機能"
```

1. 仕様書を生成（`docs/spec/ingestion/chunk-splitter.md`）
2. 人間が確認し `status: approved` に更新
3. 再実行するとテストケースを生成（`tests/test-cases/ingestion/chunk-splitter.md`）
4. 人間が確認し `status: approved` に更新

### Impl Flow（TDD 実装）

```bash
./harness impl plan/current-task.md
```

1. 計画ファイルを読み込み
2. ガードチェック（仕様書・テストケースの存在と承認）
3. テストコード一括生成 → リント → RED 確認
4. 実装コード生成（最大3回リトライ）→ リント → GREEN 確認
5. スコープ外変更の検証
6. レビュー（セルフレビュー → Codex / 2体並列）

## 計画ファイルのフォーマット

```markdown
---
scope: ingestion/chunk-splitter
spec: docs/spec/ingestion/chunk-splitter.md
test_cases: tests/test-cases/ingestion/chunk-splitter.md
---

## 今回やること
chunk-splitter の Phase 1 を実装する

## 対象テストケース
1. 空ファイルを渡すと空リストが返る
2. 見出しなしファイルは1チャンクになる
3. H1で分割される

## やらないこと
- Phase 2以降

## 完了条件
- 上記3つのテストがGREEN
- ruff / mypy がパス
```

## scope の命名規則

`カテゴリ/名前` 形式（例: `ingestion/chunk-splitter`）。

- `カテゴリ` はディレクトリ名に対応（`backend/{カテゴリ}/`, `tests/backend/{カテゴリ}/`）
- 英数字とハイフンのみ使用可能（`.` `/` `\` `,` `(` `)` `*` は禁止）

## アーキテクチャ

```
harness（CLIエントリポイント）
  ├── boundary（パス検証・スコープ解決・ファイル探索・ガード）
  ├── design-flow（仕様書・テストケース生成）
  ├── impl-flow（TDD実装サイクル + リトライ）
  │   ├── lint-guard（ruff + mypy ゼロ違反強制）
  │   ├── drift-guard（迷走検知 + エスカレーション）
  │   └── review-orchestrator（3ステップ/2ステップレビュー）
  ├── claude-runner（claude -p ラッパー、stdin経由）
  ├── logger（JSONL構造化ログ + redact）
  └── types（共有型定義）
```

## 安全機構

- **パス検証**: symlink 解決 + プロジェクトルート境界チェック + 特殊文字拒否
- **スコープ制限**: Claude の Write/Edit 権限を `allowedTools` でスコープ内に限定
- **変更検証**: 実行後に `git diff` + `git ls-files --others` でスコープ外変更を検出
- **fail-closed**: パース失敗・コマンド失敗・未導入は全てエラーとして停止
- **迷走検知**: テストリトライ上限(3回)、同一エラー連続(3回)、タイムアウト(15分)、diff肥大化
- **ログ redact**: API キー・トークンパターンを自動除去
- **タイムアウト**: Claude 10分、Codex 20分

## レビューレポート

impl フロー完了時に `docs/reviews/{date}_{scope}.md` を自動生成。

レポートに含まれる内容:
- 対象テストケース・TDD サイクルの結果
- 各レビューステップの指摘と対応（修正 / 許容 / エスカレーション）
- **判断理由**: 各指摘に対して「なぜ修正したか」「なぜ許容したか」を claude -p で要約
- **設計判断**: 計画ファイルの `## 設計判断` セクションから自動読み取り

### 計画ファイルに設計判断を記載する例

```markdown
## 設計判断
- カテゴリ単位のlint拡大は import 解決のため許容
- ログのstdout/stderr保存はデバッグ性のため許容
```

## ログ

`logs/{timestamp}_{task_name}/` に以下を出力:

- `harness.jsonl` — イベントログ（JSONL）
- `claude-code.log` — Claude CLI の入出力
- `codex-review.log` — Codex の入出力
- `review-data.json` — レビューレポート生成用の構造化データ
