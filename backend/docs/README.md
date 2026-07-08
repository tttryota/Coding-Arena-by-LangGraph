# Backend Docs

backend の振る舞いと保守上の前提をまとめた docs です。

- [backend-overview.md](backend-overview.md)
  - backend 全体の責務、起動時の構成、永続化境界、機能の無効化条件
- [quiz.md](quiz.md)
  - 通常クイズと coding session のセッション設計、LangGraph の状態遷移、一時停止と再開の約束事
- [roadmap.md](roadmap.md)
  - ロードマップ生成ジョブ、一覧/詳細/CRUD の責務、ジョブ状態の制約
- [competitive.md](competitive.md)
  - 競プロクイズの 4 ノード構成、公開する状態と非公開の状態の境界

詳細な意思決定の背景は repo ルートの `docs/adr/` を参照してください。
