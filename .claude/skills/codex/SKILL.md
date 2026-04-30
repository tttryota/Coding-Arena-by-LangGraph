---
description: 'OpenAI Codex CLIを使用したコードレビュー、分析、コードベースへの質問を実行する。使用場面: (1) コードレビュー依頼時、(2) コードベース全体の分析、(3) 実装に関する質問、(4) バグの調査、(5) リファクタリング提案、(6) 解消が難しい問題の調査。トリガー: "codex", "コードレビュー", "レビューして", "分析して", "/codex"'
metadata:
    github-path: skills/codex
    github-ref: refs/heads/develop
    github-repo: https://github.com/tttryota/my-skills
    github-tree-sha: 4043b4d3c438cb02378c29f03c1340cd484fa6c1
name: codex
---
# Codex

Codex CLIを使用してコードレビュー・分析を実行するスキル。

## 実行コマンド

codex exec --full-auto --sandbox read-only --cd <project_directory> "<request>"

## パラメータ

| パラメータ | 説明 |
|-----------|------|
| `--full-auto` | 完全自動モードで実行 |
| `--sandbox read-only` | 読み取り専用サンドボックス（安全な分析用） |
| `--cd <dir>` | 対象プロジェクトのディレクトリ |
| `"<request>"` | 依頼内容（日本語可） |

## 使用例

### コードレビュー
codex exec --full-auto --sandbox read-only --cd /path/to/project "{実装計画のファイルのパス} 次の{新規作成or修正}内容について、必要なファイルを適宜読み込んだ上でレビューして。仕様・テスト・実装間で不整合が生じないようにすること：{レビュー依頼内容}"

## 実行手順

1. 実装手順に従い、レビュー依頼する内容を整理する
2. 対象プロジェクトのディレクトリを特定する
3. 上記コマンド形式でCodexを実行
  - 実装計画をリポジトリにファイル化していれば、その実装計画ファイルのパスも渡すこと
 まずは以下からレビューして："
4. 結果を受け取り、修正内容を把握する
