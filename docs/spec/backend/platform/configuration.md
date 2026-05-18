---
feature: configuration
status: draft
reviewed_by:
approved_at:
---

## 機能概要

アプリケーションの設定をpydantic-settingsで管理する。環境変数と`.env`ファイルから設定値を読み込み、型安全に扱う。

## 振る舞い

### 基本動作

pydantic-settingsのBaseSettingsを継承した設定クラスで、全設定項目を一元管理する。環境変数と`.env`ファイルの両方に対応し、Docker環境でもローカル開発でも統一的に設定できる。

### 設定項目

| 項目 | 型 | デフォルト | 説明 |
|------|-----|----------|------|
| vault_path | Path | （必須） | Obsidian Vaultの対象パス |
| sqlite_path | Path | `data/app.db` | SQLiteファイルのパス |
| chromadb_host | str | `localhost` | ChromaDBのホスト |
| chromadb_port | int | `8000` | ChromaDBのポート |
| codex_api_url | str | （必須） | Codex app-serverのURL |
| batch_interval_minutes | int | `15` | 取り込みバッチの実行間隔（分） |
| score_threshold_not_started | int | `25` | not_started判定の上限 |
| score_threshold_insufficient | int | `50` | insufficient判定の上限 |
| score_threshold_partial | int | `75` | partial判定の上限 |
| session_max_questions | int | `20` | 1セッションの問題数上限目安 |

### 具体例

`.env`ファイル:
```
VAULT_PATH=/Users/user/ObsidianVault/study
CODEX_API_URL=http://localhost:4000
BATCH_INTERVAL_MINUTES=10
```

コード内での使用:
```python
settings = Settings()
print(settings.vault_path)  # Path("/Users/user/ObsidianVault/study")
print(settings.batch_interval_minutes)  # 10
```

## 技術判断

- pydantic-settingsを採用する理由: Pydanticベースで型安全。FastAPIとの相性が良い。環境変数と.envの両方に対応
- スコア閾値を設定で変更可能にする理由: ラベル変換の基準をハードコードせず、運用中に調整可能にする
- session_max_questionsを設定にする理由: ハードリミットではなくLLMへの指示目安だが、値を変更可能にしておく

## 境界条件

- 必須項目（vault_path, codex_api_url）が未設定 → アプリケーション起動時にバリデーションエラー
- 不正な型の値が設定された場合 → pydanticのバリデーションエラー
- .envファイルが存在しない → 環境変数のみから読み込む（エラーにはならない）

## スコープ外

- 設定のGUI管理画面
- 設定のホットリロード（変更時はアプリ再起動）
- シークレット管理（外部キーマネージャー等）

## 受け入れ基準

- [ ] .envファイルから設定が読み込まれる
- [ ] 環境変数から設定が読み込まれる（.envより優先）
- [ ] 必須項目が未設定の場合にバリデーションエラーが発生する
- [ ] デフォルト値が適用される
- [ ] スコア閾値が設定から変更できる
