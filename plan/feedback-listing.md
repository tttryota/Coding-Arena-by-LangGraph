---
type: impl
profile: backend
scope: ingestion/feedback-listing
spec: docs/spec/backend/ingestion/feedback-listing.md
test_cases: tests/test-cases/backend/ingestion/feedback-listing.md
---

## 今回やること
feedback-listing を TDD で実装する

## 対象テストケース
- TC-01: フィルタなしで全件取得、created_at instant降順ソート・total_count・成功ログを完全検証
- TC-02: read_status=unread をreaderへ委譲し、未読1件の結果と成功ログを返す
- TC-03: 未読フィードバックを既読化し、nowをそのままread_atに使い更新結果と成功ログを返す
- TC-10: read_status=read をreaderへ委譲し、既読1件の結果を返す
- TC-11: date_from/date_toをinstant比較で検証し、元文字列のままreaderへ渡す
- TC-12: 同一instantのcreated_atをid昇順でtie-breakし順序を一意に確定する
- TC-13: 片側境界とread_statusの委譲、post-filterなしの確認
- TC-14: 既読フィードバックの再既読化は冪等、read_at変更なし、update_read_status呼び出しなし
- TC-15: 1-5桁の小数秒付き日時を受理し、元文字列のままreader/writerへ渡す
- TC-20: フィルタ結果0件で空リスト・total_count=0・成功ログを返す
- TC-21: 一覧取得の入力契約違反はFeedbackListingInputError、reader呼び出しなし
- TC-22: nowの入力契約違反はFeedbackListingInputError、writer呼び出しなし
- TC-23: readerが不正なcreated_atを返した場合、FeedbackListingStoreErrorと失敗ログ
- TC-24: writer.get_by_idが不正なcreated_atを返した場合、FeedbackListingStoreError
- TC-25: writer.update_read_statusが不正なcreated_atを返した場合、FeedbackListingStoreError
- TC-30: Protocolだけを満たす最小スタブで一覧取得・既読化を完結できる
- TC-31: 存在しないfeedback_idで既読化するとFeedbackListingNotFoundError・失敗ログ
- TC-32: reader操作失敗時はFeedbackListingStoreErrorに変換し失敗ログを残す
- TC-33: writer操作失敗時はFeedbackListingStoreErrorに変換し失敗ログを残す

## やらないこと
- タグによるトピックフィルタ（cross-store join）
- ページネーション
- フィードバックの削除・編集
- 既読解除
- HTTPエンドポイントの実装

## 完了条件
- 対象テストケースが全て GREEN
- ruff + mypy がパス
- レビュー通過

## 設計判断
- 依存モジュールはProtocol DIで注入（FeedbackListingReader, FeedbackReadWriter）
- 全ファイルを backend/ingestion/infrastructure/ に配置（harness sourceLayout準拠）
- 2モジュール構成: feedback_listing_types.py, feedback_listing.py
- 既読化の時刻はnow: strパラメータで外部注入（Clock Protocolは使わない）
- ソートはモジュール側でinstant比較、同一instantはid昇順でtie-break
- read_statusはreaderへそのまま委譲、モジュール側でpost-filterしない
- 共通日時文字列契約でISO 8601 offset付き形式を検証（Z、1-6桁小数秒対応）
- reader/writer返却DTOのcreated_atも契約検証する
