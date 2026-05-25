# フィードバック一覧 — バックエンドギャップ

フロントエンド仕様 `04-feedback-list.md` に対するバックエンド実装の差分を記録する。

## 調査日: 2026-05-25

## Gap 1: `roadmap_item_id` → `roadmap_id` 解決手段がない

### 仕様

> 「関連ロードマップ」Badge クリック → `/roadmaps/{roadmapId}` へ遷移（roadmap_item_idからroadmap_idを解決）

### 現状

- `GET /ingestion/feedbacks` のレスポンスには `roadmap_item_id` のみ含まれる
- `roadmap_id` フィールドは存在しない
- フロントエンドが `roadmap_item_id` から所属する `roadmap_id` を解決する API が存在しない

### 影響

- フィードバックカードの「関連ロードマップ」Badge をクリックしても、ロードマップ詳細ページ（`/roadmaps/:roadmapId`）に直接遷移できない
- 現在のフロントエンド暫定実装: `/roadmaps` （一覧ページ）へ遷移

### 解決案

以下のいずれか:
1. `FeedbackListItem` に `roadmap_id` フィールドを追加（推奨）
2. `GET /roadmaps/items/{item_id}` のような ID 解決 API を追加
3. フロントエンドでロードマップツリーをキャッシュし、`roadmap_item_id` から逆引き

---

## 実装済み API（ギャップなし）

| API | 状態 | 備考 |
|:---|:---|:---|
| `GET /ingestion/feedbacks` | ✅ 実装済み | `date_from`, `date_to`, `read_status` パラメータ対応 |
| `PUT /ingestion/feedbacks/{feedback_id}/read` | ✅ 実装済み | 冪等動作、`FeedbackListItem` を返す |
| `date_from` / `date_to` フィルタ | ✅ 実装済み | ISO 8601 + timezone 必須（正規表現バリデーション） |
| `read_status` フィルタ | ✅ 実装済み | `all` / `unread` / `read` |
| サイドバー未読件数 | ✅ 対応可能 | `GET /ingestion/feedbacks?read_status=unread` の `total_count` で取得 |
