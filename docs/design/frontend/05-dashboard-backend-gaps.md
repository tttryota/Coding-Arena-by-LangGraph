# ダッシュボード — バックエンドギャップ

フロントエンド仕様 `05-dashboard.md` に対するバックエンド実装の差分を記録する。

## 調査日: 2026-05-25

## Gap 1: `GET /roadmaps` がツリーデータを含まない

### 仕様

> `GET /roadmaps` で各ロードマップの `items: RoadmapTreeNode[]` が返り、`last_quiz_at` から直近クイズ数や最近のクイズ結果を算出する

### 現状

- `GET /roadmaps` は `RoadmapListItem[]`（`roadmap_id`, `topic`, `overall_score` のみ）を返す
- ツリーデータ（`RoadmapTreeNode[]`）は `GET /roadmaps/{id}` で個別取得が必要
- 仕様書の型定義と実際のAPIレスポンスが一致していない

### 影響

- ダッシュボードの「直近7日間のクイズ」カード数値を算出するために、全ロードマップの詳細を個別取得する必要がある（N+1）
- 「最近のアクティビティ」のクイズ結果も同様

### 暫定対応

- `useQueries` で全ロードマップの `GET /roadmaps/{id}` を並列取得
- クエリキー `["roadmap", id]` はロードマップ詳細ページと共有されるため、キャッシュが効く
- 個人アプリでロードマップ数は少数のため、実用上の問題は軽微

### 解決案

以下のいずれか:
1. `GET /roadmaps` のレスポンスにツリーデータを含める（仕様書の前提に合わせる）
2. ダッシュボード専用のサマリーAPI（`GET /dashboard/stats`）を追加し、サーバー側で集計
3. 現状維持（N+1、個人アプリなので許容）

---

## 実装済み API（ギャップなし）

| API | 状態 | 備考 |
|:---|:---|:---|
| `GET /roadmaps` | ✅ 実装済み | `roadmap_id`, `topic`, `overall_score` を返す |
| `GET /roadmaps/{id}` | ✅ 実装済み | ツリーデータ含む `RoadmapTree` を返す |
| `GET /ingestion/feedbacks?read_status=unread` | ✅ 実装済み | `items` + `total_count` で未読件数取得可能 |
