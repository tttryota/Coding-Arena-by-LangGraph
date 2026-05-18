---
feature: feedback-listing
status: draft
reviewed_by:
approved_at:
---

## 機能概要

蓄積されたIngestionFeedbackを汎用的なフィルタ条件で取得するAPI。フロントエンドで日付グルーピングや未確認フィルタ等の表示を可能にする。

## 振る舞い

### 基本動作

フィルタ条件を受け取り、該当するIngestionFeedbackの一覧を返す。取り込み日時の降順（新しい順）で返す。

### フィルタ条件

- **日付範囲**: created_atの開始日〜終了日
- **未確認のみ**: is_read = false のもののみ
- **トピック**: タグ（source_pathに紐づくチャンクのタグ）でフィルタ

全てオプショナル。指定なしの場合は全件返す。

### 既読管理

- フィードバックを「確認済み」にするAPI
- is_readをtrueに、read_atを現在日時に更新

### 具体例

リクエスト: `GET /feedbacks?is_read=false`

レスポンス:
```json
[
  {
    "id": "...",
    "title": "TypeScript > ジェネリクスに関するノート",
    "body": "このノートはロードマップ「TypeScript > 基礎 > ...」に...",
    "source_path": "study/typescript/generics.md",
    "roadmap_item_id": "...",
    "is_read": false,
    "created_at": "2026-05-17T15:30:00"
  },
  {
    "id": "...",
    "title": "Docker > Dockerfile に関するノート",
    "body": "...",
    "source_path": "study/docker/dockerfile.md",
    "roadmap_item_id": null,
    "is_read": false,
    "created_at": "2026-05-17T10:00:00"
  }
]
```

既読にする: `PATCH /feedbacks/{id}/read`

## 技術判断

- 汎用的なフィルタAPIとする理由: フロントエンド側で日付グルーピング・未確認バッジ等の表示を自由に実装できるようにする。バックエンドはデータ提供に徹する

## 境界条件

- フィルタ結果が0件 → 空配列を返す
- 存在しないフィードバックIDで既読にする → 404エラー
- 既にis_read=trueのフィードバックを再度既読にする → 冪等。エラーにしない

## スコープ外

- フィードバックの削除
- フィードバックの編集
- ページネーション（個人用ツールでデータ量が小規模のため不要）

## 受け入れ基準

- [ ] フィルタなしで全フィードバックが取得できる
- [ ] 日付範囲でフィルタできる
- [ ] 未確認のみでフィルタできる
- [ ] 取り込み日時の降順で返る
- [ ] フィードバックを既読にできる
- [ ] 既読にするとis_readとread_atが更新される
