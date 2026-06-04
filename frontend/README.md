# Frontend

フロントエンド単体の起動方法:

```bash
cd frontend
pnpm install
pnpm dev
```

開発サーバーは `/api` をバックエンドへプロキシします。既定の接続先は `http://localhost:8001` です。必要なら `VITE_API_BASE_URL` を指定してください。

```bash
cd frontend
VITE_API_BASE_URL=http://localhost:8001 pnpm dev
```

利用可能なコマンド:

```bash
pnpm dev
pnpm run build
pnpm run lint
pnpm test
```

リポジトリ全体のセットアップは [../README.md](../README.md) を参照してください。
