---
type: impl
profile: backend
scope: ingestion/embedder
spec: docs/spec/backend/ingestion/embedder.md
test_cases: tests/test-cases/backend/ingestion/embedder.md
---

## 今回やること
embedder を TDD で実装する

## 対象テストケース
- TC-01: 単一チャンクを1件の結果へ再構成する
- TC-02: 空バッチは短絡成功しモデルを呼ばず成功ログを出す
- TC-10: 複数チャンクを入力順のまま1回だけモデルへ渡す
- TC-11: 非空バッチ成功時に必要項目付きの構造化ログを出す
- TC-12: 1件でも空白チャンクがあればバッチ全体をfail-fast
- TC-13: chunk_indexが0以上の整数でない場合はバッチ入力エラー
- TC-14: textが文字列でない場合はバッチ入力エラー
- TC-20: embedding_model.embedがcallableでなければ入力検証で失敗
- TC-21: モデル返却件数が入力件数と一致しなければ件数不一致エラー
- TC-22: 返却ベクトルがlist[float]契約を満たさない場合は形式エラー
- TC-23: 空ベクトルを返した場合は形式エラー
- TC-24: ベクトル要素に有限実数以外が含まれる場合は形式エラー
- TC-25: 同一バッチ内でベクトル次元が一致しなければ形式エラー
- TC-26: 件数不一致と形式不正の同時発生時は件数不一致を優先
- TC-30: Protocol互換の別実装へ差し替えても本体契約を保つ
- TC-31: モデル呼び出し失敗は原因付きでラップし失敗ログを出す

## やらないこと
- Embedding モデル本体の実装（Protocol で定義）
- ベクトルの ChromaDB への格納
- リトライ・サーキットブレーカ等の回復制御
- ベクトルの正規化・次元削減

## 完了条件
- 対象テストケースが全て GREEN
- ruff + mypy がパス
- レビュー通過

## 設計判断
- EmbeddingModel は Protocol で定義（DI）
- 入力バリデーション → モデル呼び出し → 応答検証の3段構成
- 空バッチは短絡成功（モデル呼び出しなし）
- 部分成功は不可（1件でも不正があればバッチ全体失敗）
