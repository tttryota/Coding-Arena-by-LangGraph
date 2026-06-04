# asdf 廃止 + mise 移行 + frontend の pnpm 化

## 目的

- `asdf` 依存を repo とローカル環境から撤去する
- repo の標準ランタイム管理を `mise.toml` に移行する
- frontend の package manager を `npm` から `pnpm` に切り替える
- Docker とローカル開発手順を同じ前提に揃える

## 対象

- repo 直下の runtime 管理ファイル
- frontend の lockfile / Dockerfile / package manager 設定
- README 類のセットアップ手順
- ローカルの `~/.zshrc`, `~/.tool-versions`, `~/.asdf`, Homebrew の `asdf`

## 実施手順

1. repo にこの計画ファイルを追加する
2. repo の runtime 管理を `mise.toml` に移す
3. frontend を `pnpm` で再ロックし、`npm` 依存を除去する
4. Dockerfile と README を `pnpm` / `mise` 前提に更新する
5. ホストに `mise` を導入し、`zsh` を `mise activate zsh` へ切り替える
6. `asdf` 本体、設定、shims を削除する
7. shell / frontend / Docker / backend の順で確認する

## 変更内容

### Repo

- `.tool-versions` を削除
- `mise.toml` を追加
- `frontend/package.json` に `packageManager: "pnpm@10.28.0"` を追加
- `frontend/package-lock.json` を削除
- `frontend/pnpm-lock.yaml` を追加
- `frontend/Dockerfile` を `pnpm` ベースへ変更
- `README.md` と `frontend/README.md` を `mise` / `pnpm` 手順に更新

### ローカル環境

- `brew install mise`
- `mise trust`
- `~/.zshrc` から `asdf` 初期化を削除
- `~/.zshrc` に `eval "$(mise activate zsh)"` を追加
- `mise use -g node@22.21.1 python@3.12.8 pnpm@10.28.0`
- `brew uninstall asdf`
- `rm -rf ~/.asdf ~/.tool-versions`

## 検証項目

### Shell / Runtime

- `echo $PATH` に `~/.asdf/shims` と `opt/homebrew/opt/asdf` が含まれない
- `command -v asdf` が失敗する
- `mise --version` が通る
- `which node python3 pnpm` が `asdf` 配下を指さない
- `node -v`, `python3 -V`, `pnpm -v` が期待値になる

### Frontend

- `cd frontend && pnpm install --frozen-lockfile`
- `cd frontend && pnpm test`
- `cd frontend && pnpm run lint`
- `cd frontend && pnpm run build`

### Container

- `docker compose build frontend`

### Backend

- `cd backend && uv sync`
- `cd backend && uv run pytest`

## ロールバック

- repo 側は `git diff` で差分確認後に個別で戻せる状態を保つ
- shell 設定は `~/.zshrc` の `mise` 行を外し、必要なら `asdf` 初期化行を戻す
- `mise` 導入後に問題があれば `brew uninstall mise` で撤去する
- frontend は `pnpm-lock.yaml` を削除し、`package-lock.json` を復元すれば `npm` に戻せる
