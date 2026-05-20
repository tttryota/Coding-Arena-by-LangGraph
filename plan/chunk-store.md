---
type: impl
profile: backend
scope: ingestion/chunk-store
spec: docs/spec/backend/ingestion/chunk-store.md
test_cases: tests/test-cases/backend/ingestion/chunk-store.md
---

## 今回やること
chunk-store を TDD で実装する

## 対象テストケース
- TC-01: 正常な2チャンク保存で自然キーIDを入力順に返す
- TC-02: 取得結果をchunk_index昇順へ正規化して返す
- TC-03: 同一source_pathのみを一括削除し.bakを巻き込まない
- TC-10: 空バッチ保存は短絡成功しbackend upsertを呼ばない
- TC-11: 同一upsert内の重複chunk_indexは拒否する
- TC-12: 入力不正と重複が同時にある場合はバリデーション優先
- TC-13: ChunkCollection Protocolテストダブルだけで機能成立
- TC-14: get_by_source_pathはprefix完全一致で.bakを混同しない
- TC-20: source_pathが空文字の各操作は入力エラー
- TC-21: 保存前バリデーションが各契約違反をChunkStoreInputErrorに統一
- TC-22: 存在しないsource_pathの取得は空リスト
- TC-23: 存在しないsource_pathの削除はdeleted_count=0
- TC-24: backend取得結果が保存契約を満たさない場合はRecordFormatError
- TC-30: 保存・取得・削除の成功時に規定イベント名の構造化ログ
- TC-31: backend upsert例外は原因付きChunkStoreBackendError
- TC-32: backend get例外は原因付きChunkStoreBackendError
- TC-33: backend delete例外は原因付きChunkStoreBackendError

## やらないこと
- ChromaDB concrete client の実装
- ベクトル類似度検索、タグ検索
- リトライ・サーキットブレーカ
- チャンク単位の個別削除・取得

## 完了条件
- 対象テストケースが全て GREEN
- ruff + mypy がパス
- レビュー通過

## 設計判断
- ChunkCollection は Protocol で定義（DI）
- 仕様書ではdomain/infrastructureの3ファイル分割だが、ハーネスのscopeLayoutがinfrastructure固定のため全ファイルをinfrastructureに配置する
- ID生成は `{source_path}_{chunk_index}` のナチュラルキー
- 空バッチは短絡成功（backend呼び出しなし）
- 部分成功は不可（1件でも不正があればバッチ全体失敗）
