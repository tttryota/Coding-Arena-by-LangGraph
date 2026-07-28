# 概要
codex app-server をベースにしたコーディングトレーニング用ローカルアプリです。ロードマップ生成、理解度チェック用クイズ、コーディング演習、複数の問題演習モードをまとめて扱えます。<br>
学習テーマを選んでロードマップを生成し、その項目ごとに通常クイズやコーディング演習へ進む構成です。加えて、競プロ形式のアルゴリズム学習、競プロ初学者向けの「競プロうさぎ」、SQL練習用の SQL道場を独立した導線として持ちます。<br>
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

推奨起動方法は Docker Compose です。本READMEではそのパターンの構築手順のみ記します。

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

### Langfuseで実行を監視

Langfuseは通常起動には含まれません。初回だけローカル秘密値を生成し、
`observability`プロファイルを有効にして起動します。

```bash
scripts/init-langfuse-env.sh
docker compose --profile observability up --build
```

起動後、[Langfuse UI](http://localhost:3000)に`.env`の
`LANGFUSE_INIT_USER_EMAIL`と`LANGFUSE_INIT_USER_PASSWORD`でログインします。

UIでは次の順に確認します。

1. `Tracing`で失敗または遅いtraceを探す
2. trace詳細でLangGraphノードと、その中のCodex generationをツリー表示する
3. `Sessions`で同じクイズのstart/resume/retryを時系列にまとめて確認する
4. `Scores`で品質評価を確認する
5. `Datasets / Experiments`で変更前後の評価結果を比較する
6. `Dashboards / Monitors`でエラー率、p95 latency、品質推移を確認する

詳細な画面の見方とモニター設定は
[docs/observability.md](docs/observability.md)を参照してください。

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

LangGraphの評価:

```bash
cd backend

# 固定データの契約・経路・評価データ検証
uv run python -m evaluation.cli contract

# 実Codexによる品質評価（各ケース3回）とLangfuseへの結果送信
uv run python -m evaluation.cli quality --repeat 3 --publish

# 1回warm-up後、各ケース5回のローカル性能測定
uv run python -m evaluation.cli benchmark --repeat 5 --publish
```

評価結果は`backend/.eval-results/`にJSONとMarkdownで保存されます。
品質ベースラインは`backend/evals/baselines/quality.json`、マシン依存の
性能ベースラインは`.eval-results/benchmark-baseline.json`です。

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
- Langfuseのデータは名前付きDocker volumeに保存され、通常の
  `docker compose down`では削除されません
