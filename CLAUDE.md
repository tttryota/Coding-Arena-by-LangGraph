# プロジェクト概要
Obsidian × RAG × LangGraph 理解度チェックシステム。
個人学習用。技術理解の深化が目的。

# アーキテクチャ
- backend/: Python (FastAPI + LangGraph + LangChain)
- frontend/: TypeScript (React + Vite + shadcn/ui + Jotai)

# 技術制約
- LLM: Qwen2.5-32B（Ollama経由ローカル）
- Embedding: multilingual-e5-large（ローカル）
- VectorDB: ChromaDB（ローカル永続化）
- LangGraphのステートは SessionState を基本とする

# ディレクトリ規約
- backend/{機能}/infrastructure/  機能モジュール（Protocol DI で外部分離）
- backend/{機能}/domain/          純粋ロジック（I/Oなし、現在は chunk_splitter のみ）
- backend/infrastructure/         横断基盤（RDB, config, logging）
- frontend/src/                   Reactコンポーネント
- テスト: コロケーション方式（ソースと同ディレクトリに test_*.py）
- ※ application/ presentation/ は必要になった時点で導入

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
