---
status: ready
---

# テストケース一覧

# 検証焦点

| テストの種類 | 検証焦点 |
|---|---|
| Phase 1（最小骨格） | `chunk_index` / `embedding` の基本返却形、空バッチ短絡、最小ログ |
| Phase 2（コアロジック） | Protocol 注入、1 バッチ 1 回呼び出し、入力順保持、本文非改変、バッチ単位 fail-fast |
| Phase 3（エッジケース） | 入力契約違反、件数不一致、ベクトル形式不正、優先順位付きエラー |
| Phase 4（外部連携） | モデル例外ラップ、構造化ログ、標準モデル 1024 次元 |

## Phase 1: 最小骨格

| ID | 観点 | 前提 | 入力 | 期待結果 | 備考 |
|---|---|---|---|---|---|
| TC-01 | 単一チャンクを 1 件の結果へ再構成する | `embedding_model.embed(["TypeScript のジェネリクスは型引数を使って再利用性を高める。"])` が `[[0.12, -0.03, 0.44, 0.08]]` を返す | `chunks = [{chunk_index: 0, text: "TypeScript のジェネリクスは型引数を使って再利用性を高める。"}]`、`source_path = "study/typescript/generics.md"` | `[{chunk_index: 0, embedding: [0.12, -0.03, 0.44, 0.08]}]` を返す | 仕様書 例1 対応 |
| TC-02 | 空バッチは短絡成功し、モデルを呼ばず、空バッチ成功ログを出す | `embedding_model` は呼び出し有無を検査できるスパイ、構造化ログ収集を有効化する | `chunks = []`、`source_path = "study/empty.md"` | `[]` を返し、`embedding_model.embed(...)` は 1 回も呼ばれない。`event = "embedder_batch_completed"` のログがちょうど 1 件出力され、少なくとも `source_path = "study/empty.md"`、`chunk_count = 0`、`embedded_count = 0`、`vector_dimension = null`、`invalid_chunk_count = 0`、`model_failure_count = 0` を含む（追加キーがあってもよい） | 仕様書 例3 と空バッチ可観測性 |

## Phase 2: コアロジック

| ID | 観点 | 前提 | 入力 | 期待結果 | 備考 |
|---|---|---|---|---|---|
| TC-10 | 複数チャンクを入力順のまま 1 回だけモデルへ渡し、同一本文も独立に結果化する | `embedding_model.embed(texts)` は受け取った `texts` を記録し、`[[0.10, 0.20, 0.30, 0.40], [-0.11, 0.05, 0.18, 0.09], [0.10, 0.20, 0.30, 0.40]]` を返す | `chunks = [{chunk_index: 0, text: "Docker Compose でアプリケーションを起動する。"}, {chunk_index: 2, text: " PostgreSQL のトランザクション分離レベルを整理する。 "}, {chunk_index: 5, text: "Docker Compose でアプリケーションを起動する。"}]`、`source_path = "study/backend/infra.md"` | `embedding_model.embed(...)` は 1 回だけ呼ばれ、引数 `texts` は入力順かつ原文そのままの `["Docker Compose でアプリケーションを起動する。", " PostgreSQL のトランザクション分離レベルを整理する。 ", "Docker Compose でアプリケーションを起動する。"]` である。返却値は `[{chunk_index: 0, embedding: [0.10, 0.20, 0.30, 0.40]}, {chunk_index: 2, embedding: [-0.11, 0.05, 0.18, 0.09]}, {chunk_index: 5, embedding: [0.10, 0.20, 0.30, 0.40]}]` をこの順で返す | 入力順保持、本文非改変、重複本文非 dedupe |
| TC-11 | 非空バッチ成功時に必要項目付きの構造化ログを出す | `embedding_model.embed(["Docker Compose でアプリケーションを起動する。", "PostgreSQL のトランザクション分離レベルを整理する。"])` が `[[0.10, 0.20, 0.30, 0.40], [-0.11, 0.05, 0.18, 0.09]]` を返し、構造化ログ収集を有効化する | `chunks = [{chunk_index: 0, text: "Docker Compose でアプリケーションを起動する。"}, {chunk_index: 1, text: "PostgreSQL のトランザクション分離レベルを整理する。"}]`、`source_path = "study/backend/infra.md"` | 正常終了し、`event = "embedder_batch_completed"` のログがちょうど 1 件出力され、少なくとも `source_path = "study/backend/infra.md"`、`chunk_count = 2`、`embedded_count = 2`、`vector_dimension = 4`、`invalid_chunk_count = 0`、`model_failure_count = 0` を含む（追加キーがあってもよい） | 仕様書 例2 の可観測性拡張 |
| TC-12 | 1 件でも空白チャンクがあればバッチ全体を fail-fast し、モデルを呼ばない | `embedding_model` は呼び出し有無を検査できるスパイ | `chunks = [{chunk_index: 0, text: "React の state 管理を整理する。"}, {chunk_index: 1, text: "   "}]`、`source_path = "study/invalid.md"` | `EmbeddingBatchInputError` を送出し、`embedding_model.embed(...)` は 1 回も呼ばれない | 仕様書 例4 と部分成功禁止 |
| TC-13 | `chunk_index` が 0 以上の整数でないチャンクを含む場合はバッチ入力エラーにする | `embedding_model` は呼び出し有無を検査できるスパイ | `chunks = [{chunk_index: -1, text: "TypeScript の conditional types を整理する。"}]` | `EmbeddingBatchInputError` を送出し、`embedding_model.embed(...)` は 1 回も呼ばれない | `chunk_index` 契約違反 |
| TC-14 | `text` が文字列でないチャンクを含む場合はバッチ入力エラーにする | `embedding_model` は呼び出し有無を検査できるスパイ | `chunks = [{chunk_index: 0, text: 123}]` | `EmbeddingBatchInputError` を送出し、`embedding_model.embed(...)` は 1 回も呼ばれない | `text` 型契約違反 |

## Phase 3: エッジケース

| ID | 観点 | 前提 | 入力 | 期待結果 | 備考 |
|---|---|---|---|---|---|
| TC-20 | `embedding_model.embed` が callable でなければ入力検証で失敗する | `embedding_model = {embed: null}` または同等の非 callable 実装 | `chunks = [{chunk_index: 0, text: "Docker Compose でアプリケーションを起動する。"}]` | `EmbeddingBatchInputError` を送出する | Protocol 契約違反 |
| TC-21 | モデル返却件数が入力件数と一致しなければ件数不一致エラーにする | `embedding_model.embed(["Docker Compose でアプリケーションを起動する。", "PostgreSQL のトランザクション分離レベルを整理する。"])` が `[[0.10, 0.20, 0.30, 0.40]]` を返す | `chunks = [{chunk_index: 0, text: "Docker Compose でアプリケーションを起動する。"}, {chunk_index: 1, text: "PostgreSQL のトランザクション分離レベルを整理する。"}]` | `EmbeddingResponseCountMismatchError` を送出する | 件数不足側の境界。超過側も同一観点で派生可能 |
| TC-22 | 返却ベクトル自体が `list[float]` 契約を満たさない場合は形式エラーにする | `embedding_model.embed(["TypeScript のジェネリクスを整理する。"])` が `[(0.12, -0.03, 0.44, 0.08)]` を返す | `chunks = [{chunk_index: 0, text: "TypeScript のジェネリクスを整理する。"}]` | `EmbeddingVectorFormatError` を送出する | ベクトル自体が `list` でないケース |
| TC-23 | 空ベクトルを返した場合は形式エラーにする | `embedding_model.embed(["TypeScript のジェネリクスを整理する。"])` が `[[]]` を返す | `chunks = [{chunk_index: 0, text: "TypeScript のジェネリクスを整理する。"}]` | `EmbeddingVectorFormatError` を送出する | 空ベクトル境界 |
| TC-24 | ベクトル要素に有限実数以外が含まれる場合は形式エラーにする | `embedding_model.embed(...)` がケース A: `[[0.1, NaN, 0.3, 0.4]]`、ケース B: `[[0.1, inf, 0.3, 0.4]]`、ケース C: `[[0.1, None, 0.3, 0.4]]`、ケース D: `[[0.1, "0.2", 0.3, 0.4]]` を返す | `chunks = [{chunk_index: 0, text: "ベクトル検索の前提を整理する。"}]` | 各ケースで `EmbeddingVectorFormatError` を送出する | `NaN` / `inf` / `None` / 文字列を一括確認 |
| TC-25 | 同一バッチ内でベクトル次元が一致しなければ形式エラーにする | `embedding_model.embed(["Docker Compose でアプリケーションを起動する。", "PostgreSQL のトランザクション分離レベルを整理する。"])` が `[[0.10, 0.20, 0.30, 0.40], [-0.11, 0.05, 0.18]]` を返す | `chunks = [{chunk_index: 0, text: "Docker Compose でアプリケーションを起動する。"}, {chunk_index: 1, text: "PostgreSQL のトランザクション分離レベルを整理する。"}]` | `EmbeddingVectorFormatError` を送出する | 次元不一致境界 |
| TC-26 | 件数不一致と形式不正が同時に疑われる場合でも件数不一致を優先する | `embedding_model.embed(["Docker Compose でアプリケーションを起動する。", "PostgreSQL のトランザクション分離レベルを整理する。"])` が `[[0.10, 0.20, "bad"]]` を返す | `chunks = [{chunk_index: 0, text: "Docker Compose でアプリケーションを起動する。"}, {chunk_index: 1, text: "PostgreSQL のトランザクション分離レベルを整理する。"}]` | `EmbeddingResponseCountMismatchError` を送出し、`EmbeddingVectorFormatError` は送出しない | ルール間相互作用の優先順位 |

## Phase 4: 外部連携

| ID | 観点 | 前提 | 入力 | 期待結果 | 備考 |
|---|---|---|---|---|---|
| TC-30 | `EmbeddingModel` Protocol を満たす別実装へ差し替えても本体契約を保つ | 実装 A と実装 B がともに `embed(texts: list[str]) -> list[list[float]]` を実装し、同一入力に対して同じ 4 次元ベクトルを返す | 同一の `chunks = [{chunk_index: 0, text: "TypeScript のジェネリクスを整理する。"}]` を実装 A と実装 B でそれぞれ実行する | いずれも `[{chunk_index: 0, embedding: [0.12, -0.03, 0.44, 0.08]}]` を返し、ingestion 本体は具体クラス import やモデル名分岐を前提にしない | Protocol 抽象化の受け入れ基準 |
| TC-31 | モデル呼び出し失敗は原因付きでラップし、失敗ログを出す | `embedding_model.embed(...)` が `TimeoutError("embedding timed out")` を送出し、構造化ログ収集を有効化する | `chunks = [{chunk_index: 0, text: "Docker Compose でアプリケーションを起動する。"}]`、`source_path = "study/backend/infra.md"` | 元例外を原因として保持した `EmbeddingModelCallError` を送出する（`__cause__` が元の `TimeoutError` と同一オブジェクト）。`event = "embedder_model_call_failed"` のログがちょうど 1 件出力され、少なくとも `source_path = "study/backend/infra.md"`、`chunk_count = 1`、`embedded_count = 0`、`vector_dimension = null`、`invalid_chunk_count = 0`、`model_failure_count = 1` を含む（追加キーがあってもよい）。例外情報の記録は `exc_info = True` の存在で確認する | モデルロード失敗、推論失敗、タイムアウト等を同系列で扱う |
| TC-32 | 標準モデル `multilingual-e5-large` 接続時は 1024 次元ベクトルを downstream へ渡せる | `multilingual-e5-large` アダプターを `EmbeddingModel` として接続し、単一チャンク入力を実行できる環境を用意する | `chunks = [{chunk_index: 0, text: "TypeScript のジェネリクスは型引数を使って再利用性を高める。"}]` | 返却値は `[{chunk_index: 0, embedding: <1024 個の有限実数>}]` となり、`len(embedding) = 1024` を満たす | 受け入れ基準の標準モデル確認 |

# 網羅性チェック

仕様書の受け入れ基準の各項目に対応するテストケース ID を記載する。
全項目が少なくとも1つのテストケースでカバーされていることを確認する。

| 受け入れ基準 | 対応テストケース |
|---|---|
| `EmbeddingModel` Protocol を満たす実装が外部注入され、ingestion 本体は具体モデル型に依存しない | TC-20, TC-30 |
| 1 件以上の正常チャンクを含むバッチで、入力順を保った `ChunkEmbeddingResult` 一覧が返る | TC-01, TC-10 |
| `chunks=[]` の場合、空リストが返り、モデル呼び出しは行われない | TC-02 |
| `text.strip()` が空のチャンクを含む場合、`EmbeddingBatchInputError` が送出される | TC-12 |
| モデル呼び出しが失敗した場合、`EmbeddingModelCallError` が送出される | TC-31 |
| モデル返却件数が入力件数と一致しない場合、`EmbeddingResponseCountMismatchError` が送出される | TC-21, TC-26 |
| モデル返却ベクトルに非数値・空ベクトル・次元不一致がある場合、`EmbeddingVectorFormatError` が送出される | TC-22, TC-23, TC-24, TC-25 |
| 正常終了時に `embedder_batch_completed`、モデル失敗時に `embedder_model_call_failed` の構造化ログが必要項目付きで出力される | TC-02, TC-11, TC-31 |
| 標準モデル `multilingual-e5-large` を接続した場合、各ベクトル次元が 1024 で downstream に渡せる | TC-32 |

# 記述ルール

- 仕様書に明記された振る舞いだけを前提にする
- 仕様未記載の振る舞いを期待結果に置く場合は `[要仕様追記]` タグを付ける
- 正常系・境界系・異常系が重複なく網羅されていることを確認する
- 仕様書の受け入れ基準の各項目に対応するテストケースが最低1つあることを確認する
