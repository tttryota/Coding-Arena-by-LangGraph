---
type: impl
profile: backend
scope: roadmap/roadmap-persistence
spec: docs/spec/backend/roadmap/roadmap-persistence.md
test_cases: tests/test-cases/backend/roadmap/roadmap-persistence.md
---

## 今回やること
roadmap-persistence を TDD で実装する

## 対象テストケース
- TC-01: 仕様書 例1 の 3 段階層を完全にフラット化し、保存引数と戻り値を全フィールドで検証する
- TC-02: 空ロードマップでも roadmap_id を生成して空配列を保存できる
- TC-03: 最小有効構成 major 1 -> middle 1 -> detail 1 を 3 レコードで保存できる
- TC-10: DFS pre-order の走査順と sibling ごとの order 採番を検証する
- TC-11: topic / title は strip() ベースで妥当性判定しつつ、保存値は前後空白を保持する
- TC-12: major の children=[] を正常入力として保存できる
- TC-13: middle の children=[] を正常入力として保存できる
- TC-20: topic が空文字または空白のみなら RoadmapPersistenceInputError を送出する
- TC-21: 任意 level の title が空文字または空白のみなら RoadmapPersistenceInputError を送出する
- TC-22: created_at は ISO 8601 解析可能かつ UTC offset 必須である
- TC-23: ルート項目が major 以外なら RoadmapPersistenceInputError を送出する
- TC-24: 親子の level 関係が major -> middle -> detail を外れると RoadmapPersistenceInputError を送出する
- TC-25: detail が非空 children を持つと RoadmapPersistenceInputError を送出する
- TC-30: 成功時に Protocol 経由で依存を所定回数だけ呼び、roadmap_persisted ログを出力する
- TC-31: writer.save_items 失敗時は RoadmapPersistenceWriteError にラップし、cause chain と失敗ログを保持する

## やらないこと
- ロードマップの削除
- ロードマップ間のマージ
- 既存ロードマップの更新（常に新規保存）
- LLM 応答のパース（入力は変換済みの DTO を前提）
- score の計算・更新
- RDB 実装（writer は Protocol で注入）

## 完了条件
- 対象テストケースが全て GREEN
- ruff + mypy がパス
- レビュー通過

## 設計判断
- 依存モジュールは Protocol DI で注入（RoadmapPersistenceWriter, RoadmapIdGenerator）
- 全ファイルを backend/roadmap/infrastructure/ に配置（harness sourceLayout 準拠）
- 2 モジュール構成: roadmap_persistence_types.py, roadmap_persistence.py
- created_at は外部注入の ISO 8601 文字列（offset 必須）
- フラット化は DFS pre-order、order は同一親の children 出現順で 0 始まり
- major / middle の children=[] は許容（level 親子関係のみで 3 段固定構造を強制）
- topic / title は strip() ベースで検証、保存値は入力文字列そのまま
- structlog でイベントログ: roadmap_persisted / roadmap_persistence_failed
