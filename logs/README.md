# logs/

開発ハーネス（`.harness/`）が実行時に出力する構造化ログの格納先。

## ディレクトリ構造

```
logs/
└── {timestamp}_{task_name}/
    ├── harness.jsonl        # ハーネスのイベントログ（JSON Lines）
    ├── claude-code.log      # claude -p の入出力全文
    └── codex-review.log     # Codexレビューの入出力全文
```

## 記録されるイベント例

- ガードチェック結果（仕様書・テストケースの存在確認）
- TDDサイクルの進行（RED → GREEN）
- リンター実行結果
- セルフレビュー・Codexレビューの指摘内容
- 迷走ガードの検知・エスカレーション

## 注意

このディレクトリ配下のログファイルは `.gitignore` で除外されています（この README を除く）。
