# プロジェクト概要
LangGraph ベースの理解度チェックシステム。
個人学習用。技術理解の深化が目的。

# アーキテクチャ
- backend/: Python (FastAPI + LangGraph + LangChain)
- frontend/: TypeScript (React + Vite + shadcn/ui + TanStack Query + Zustand)

# 技術制約
- LLM: Codex（app-server経由）
- LangGraphのステートは SessionState を基本とする

# ディレクトリ規約
- backend/{機能}/domain/             ドメイン層（Protocol定義、DTO、純粋ロジック。I/Oなし）
- backend/{機能}/application/        アプリケーション層（オーケストレーション。Protocol経由でI/O）
- backend/{機能}/infrastructure/     インフラ層（concrete実装。直接I/O）
- backend/infrastructure/            横断基盤（RDB, config, logging）
- frontend/src/features/{機能}/      機能単位グルーピング（コンポーネント・フック・テスト共存）
- frontend/src/components/           横断コンポーネント（layout/, common/, ui/）
- frontend/src/lib/                  UI非関連ユーティリティ
- テスト: コロケーション方式
  - backend: ソースと同ディレクトリに test_*.py
  - frontend: ソースと同ディレクトリに *.test.ts / *.test.tsx（vitest）

# コーディング規約
- Python: ruff でフォーマット・リント
- TypeScript: ESLint + Prettier
- 型アノテーション必須（Python: mypy --strict, TS: strict mode）

# コミット規約
- メッセージ形式: `prefix: 変更内容`
  - prefix例: feat, update, fix, refactor, docs, test, chore
  - 例: `docs: logs/README.mdを追加してログディレクトリの目的を記載`
  - 例: `fix: チャンク分割で空ファイル時にクラッシュする問題を修正`
- 1コミット1目的。複数の目的を混ぜない
- 1ファイルに複数目的の変更が混在した場合は `git add -p` でhunk単位に分割してコミットする

# 禁止事項
- 外部APIキーのハードコード
- tests/ 以外のファイル削除を自律的に行わない
- 設計書にない機能の追加
- 既存テストを削除・無効化しない
