---
feature: docker-compose
status: approved
reviewed_by: claude
approved_at: 2026-05-21
---

## 機能概要

開発・実行環境をdocker-composeで一括管理する。`docker compose up` でバックエンド・フロントエンド・ChromaDBが起動する。

## 振る舞い

### コンテナ構成

| サービス | イメージ | ポート | 役割 |
|---------|---------|--------|------|
| backend | Dockerfile（自前ビルド） | 8001 | FastAPIアプリケーション |
| frontend | Dockerfile（自前ビルド） | 3000 | React/Viteアプリケーション |
| chromadb | chromadb/chroma（公式） | 8000 | ベクトルDB |

### ボリューム

| マウント | コンテナ内パス | 用途 |
|---------|--------------|------|
| `./data/app.db` | `/app/data/app.db` | SQLite永続化 |
| `./data/chromadb/` | `/chroma/chroma` | ChromaDB永続化 |
| `./data/huggingface/` | `/root/.cache/huggingface` | Embeddingモデルキャッシュ永続化 |
| ホスト側Vaultパス | `/vault` (読み取り専用) | Obsidian Vault |

### 依存関係

- backendはchromadbに依存（depends_on）
- frontendは独立（バックエンドのURLは環境変数で設定）

### 具体例

```yaml
services:
  backend:
    build: ./backend
    ports:
      - "8001:8001"
    volumes:
      - ./data:/app/data
      - ./data/huggingface:/root/.cache/huggingface
      - ${VAULT_PATH}:/vault:ro
    depends_on:
      - chromadb
    env_file:
      - .env

  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    environment:
      - VITE_API_URL=http://localhost:8001

  chromadb:
    image: chromadb/chroma
    ports:
      - "8000:8000"
    volumes:
      - ./data/chromadb:/chroma/chroma
```

## 技術判断

- SQLiteをファイルベースで永続化する理由: 個人用ツールでRDBサーバーは不要。ボリュームマウントでホスト側に永続化すればコンテナ再作成でもデータが残る
- Embeddingモデルキャッシュを永続化する理由: multilingual-e5-large（約2GB）の初回ダウンロードをコンテナ再作成のたびに繰り返さないため
- Vaultを読み取り専用でマウントする理由: システムがノートを変更することはない。取り込みのみ

## 境界条件

- VAULT_PATHが未設定 → docker compose起動時にエラー
- data/ディレクトリが未作成 → Dockerが自動作成
- ChromaDBが起動前にbackendが接続を試みる → depends_onで順序制御。ヘルスチェックの追加は将来検討

## スコープ外

- 本番デプロイ用の構成（本仕様は開発環境用）
- CI/CD用の構成
- SSL/TLS対応

## 受け入れ基準

- [ ] `docker compose up` で全サービスが起動する
- [ ] SQLiteデータがコンテナ再作成後も保持される
- [ ] ChromaDBデータがコンテナ再作成後も保持される
- [ ] Embeddingモデルキャッシュがコンテナ再作成後も保持される
- [ ] Obsidian Vaultが読み取り専用でマウントされる
