---
feature: database-migration
status: approved
reviewed_by: claude
approved_at: 2026-05-21
---

## 機能概要

SQLiteのスキーマ管理をAlembicで行う。テーブルの作成・変更をマイグレーションスクリプトとして管理し、再現可能なDB構築を実現する。

## 振る舞い

### 基本動作

- SQLAlchemyのモデル定義からAlembicがマイグレーションスクリプトを自動生成
- `alembic upgrade head` でスキーマを最新に更新
- マイグレーション履歴がバージョン管理される

### 初期マイグレーション

data-models.mdで定義された以下のテーブルを作成:
- RoadmapItem
- QuizSession
- QuizAnswer
- IngestionFeedback
- SummaryTestResult

### 開発フロー

```
1. SQLAlchemyモデルを変更
2. alembic revision --autogenerate -m "変更内容"
3. 生成されたスクリプトを確認
4. alembic upgrade head
```

### Docker環境での実行

backendコンテナ起動時に `alembic upgrade head` を自動実行し、スキーマが常に最新になるようにする。

## 技術判断

- Alembicを採用する理由: SQLAlchemy公式のマイグレーションツール。autogenerateでモデル定義との差分を自動検出できる
- 自動実行する理由: 個人用ツールのため、手動マイグレーションの運用負荷を避ける

## 境界条件

- SQLiteファイルが存在しない → Alembicが新規作成してマイグレーションを適用
- マイグレーションスクリプトとDBの状態が不整合 → alembicがエラーを報告

## スコープ外

- ダウングレード（ロールバック）の運用方針
- データマイグレーション（スキーマ変更に伴うデータ変換）
- 複数DB対応

## 受け入れ基準

- [ ] `alembic upgrade head` で全テーブルが作成される
- [ ] SQLAlchemyモデルの変更からマイグレーションスクリプトが自動生成される
- [ ] Docker起動時にマイグレーションが自動適用される
- [ ] マイグレーション履歴がバージョン管理される
