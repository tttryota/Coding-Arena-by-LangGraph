# 概要
codex app-serverをベースとしたLangGraph問題生成フローによってコーディング学習を実施できるprogate的ローカルアプリケーションです。（モデルはsparkがおすすめです。sparkでもちょっと待ちます）<br>
ロードマップでテーマを選択してロードマップを生成することで、テーマを体系的に学習できます。コーディングがメインです。<br>
また、競プロ的なアルゴリズム学習セクションを特設してテーマごとに選択できるようになっています。<br>
オプションとして、Obsidianの/study配下にノートを作成すると、ベクトルとして取り込み、RAGとして参照してフィードバックをくれるオマケもあります。<br>
構成は `FastAPI + ChromaDB + SQLite + React/Vite` です。

## リポジトリ構成

- `backend/`: FastAPI アプリケーション
- `backend/src/`: backend の実コードと近接テスト
- `frontend/`: React + Vite フロントエンド
- `docs/`: 仕様・設計メモ
- `data/`: SQLite、ChromaDB、Hugging Face キャッシュ

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

Vault を取り込みたい場合だけ、`VAULT_PATH` を実際の Vault パスに設定してください。未設定でもアプリは起動できますが、`POST /ingestion/trigger` は無効になります。

```env
VAULT_PATH=/absolute/path/to/your/obsidian/vault
```

他の設定値は未指定でもデフォルトで動作します。ローカル開発時に ChromaDB を手動起動する場合だけ、必要に応じて `CHROMADB_HOST=localhost` を使ってください。

## 起動方法

### Docker Compose で起動

backend コンテナはホストの `~/.codex` を `/root/.codex` にマウントして、その認証情報を使います。ホストで `codex` に未ログインの場合は、先にログインしてください。
`VAULT_PATH` を未設定のままでも起動できます。その場合、Vault 取り込みは無効になり、feedback API の参照だけが利用可能です。

```bash
docker compose up --build
```

起動後のアクセス先:

- Frontend: [http://localhost:3080](http://localhost:3080)
- Backend API: [http://localhost:8081](http://localhost:8081)
- FastAPI Docs: [http://localhost:8081/docs](http://localhost:8081/docs)
- ChromaDB: `localhost:8000`

初回起動時は埋め込みモデル `intfloat/multilingual-e5-large` の取得に時間がかかります。キャッシュは `data/huggingface/` に永続化されます。

停止:

```bash
docker compose down
```

### ローカル開発で起動

ChromaDB だけ Docker で立てて、フロントエンドとバックエンドをローカル実行する手順です。

1. ChromaDB を起動

```bash
docker compose up -d chromadb
```

2. バックエンドを起動

```bash
cd backend
uv sync
set -a
source ../.env
set +a
uv run alembic upgrade head
uv run uvicorn --app-dir src dev_server:app --reload --host 0.0.0.0 --port 8001
```

3. フロントエンドを起動

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
- SQLite は `data/app.db`、ChromaDB は `data/chromadb/` に保存されます
- backend コンテナはホストの `~/.codex` を共有します
- `VAULT_PATH` を設定した場合だけ、Vault は Docker で `/vault` に読み取り専用マウントされます
