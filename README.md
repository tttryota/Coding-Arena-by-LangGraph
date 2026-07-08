# 概要
codex app-server をベースにしたローカル学習アプリです。ロードマップ生成、理解度チェック用クイズ、コーディング演習、複数の問題演習モードをまとめて扱えます。<br>
学習テーマを選んでロードマップを生成し、その項目ごとに通常クイズやコーディング演習へ進む構成です。加えて、競プロ形式のアルゴリズム学習、初学者向けの「競プロうさぎ」、SQL 道場を独立した導線として持ちます。<br>
構成は `FastAPI + SQLite + React/Vite` です。

## 主な機能

- ロードマップ生成
  - 学習テーマから階層型ロードマップを生成し、進捗とスコアを保持します。
- 通常クイズ
  - ロードマップ項目ごとに確認ポイントを設計し、対話形式で理解度を確認します。
- コーディング演習
  - ロードマップ項目に紐づく lecture + practice フローで、説明から実装課題まで進めます。
- 競プロ
  - テーマ選択式で問題を出題し、提出コードを採点します。
- 競プロうさぎ
  - 初学者向けに unit 単位で問題を整理し、問題一覧から 1 問ずつ解けます。
- SQL 道場
  - SQL のテーマ別演習を出題し、回答とフィードバックを返します。

## リポジトリ構成

- `backend/`: FastAPI アプリケーション
- `backend/src/`: backend の実コードと近接テスト
- `backend/docs/`: backend の振る舞い docs
- `frontend/`: React + Vite フロントエンド
- `docs/`: 仕様・設計メモ
- `data/`: SQLite データなどのローカル保存領域

backend の docs は [backend/docs/README.md](/Users/tsuryoryo/Desktop/repo/obsidian/backend/docs/README.md) から辿れます。overview と機能別 docs を分けていて、実装詳細よりも API 契約、状態遷移、永続化境界を優先して記述しています。

## 前提環境

推奨起動方法は Docker Compose です。

- Docker / Docker Compose
- `codex` にログイン済みのホスト環境

ローカル開発をする場合は以下を前提にします。

- `mise`
- `uv`
- Node.js `22.21.1`
- Python `3.12.8`
- `pnpm 10.28.0`

セットアップ:

```bash
brew install mise
echo 'eval "$(mise activate zsh)"' >> ~/.zshrc
exec zsh
mise trust
mise install
lefthook install
```

## 環境変数

まず `.env` を作成します。

```bash
cp .env.example .env
```

主要な設定値は未指定でもデフォルトで動作します。必要に応じて `.env.example` の値を有効化してください。

## 起動方法

### Docker Compose で起動

backend コンテナはホストの `~/.codex` を `/root/.codex` にマウントして、その認証情報を使います。ホストで `codex` に未ログインの場合は、先にログインしてください。

```bash
docker compose up --build
```

起動後のアクセス先:

- Frontend: [http://localhost:3080](http://localhost:3080)
- Backend API: [http://localhost:8081](http://localhost:8081)
- FastAPI Docs: [http://localhost:8081/docs](http://localhost:8081/docs)

停止:

```bash
docker compose down
```

### ローカル開発で起動

1. バックエンドを起動

```bash
cd backend
uv sync
set -a
source ../.env
set +a
uv run alembic upgrade head
uv run uvicorn --app-dir src dev_server:app --reload --host 0.0.0.0 --port 8001
```

2. フロントエンドを起動

```bash
cd frontend
pnpm install
pnpm dev
```

このときフロントエンドの開発サーバーは Vite のデフォルトポートで起動し、`/api` へのリクエストを `http://localhost:8001` にプロキシします。別の API を向けたい場合は `VITE_API_BASE_URL` を指定してください。

```bash
cd frontend
VITE_API_BASE_URL=http://localhost:8001 pnpm dev
```

## テスト・品質チェック

### Backend

```bash
cd backend
uv run pytest
uv run ruff check .
uv run mypy .
```

### Frontend

```bash
cd frontend
pnpm test
pnpm run lint
pnpm run build
```

## Git Hooks

`lefthook` を使って以下を自動実行します。

- `pre-commit`: 変更に `backend/` が含まれると `uv run ruff check . && uv run mypy .`
- `pre-commit`: 変更に `frontend/` が含まれると `pnpm run lint`
- `pre-push`: `backend/` の変更で `uv run ruff check . && uv run mypy . && uv run pytest`
- `pre-push`: `frontend/` の変更で `pnpm run lint && pnpm test`
- `pre-push`: `backend/api/**` または `frontend/src/types/api.ts` の変更では backend と frontend の両方

`README.md`、`docs/`、`mise.toml`、`lefthook.yml`、`scripts/hooks/`、画像だけの変更では hook は no-op です。

## 補足

- Docker 起動時、バックエンドコンテナは起動時に Alembic migration を自動実行します
- SQLite は `data/app.db` に保存されます
- backend コンテナはホストの `~/.codex` を共有します
