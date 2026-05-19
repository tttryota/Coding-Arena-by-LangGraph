---
feature: ingestion/embedder
status: ready
---

# 概要

- この機能が解決する課題:
  チャンク分割済みテキストを Embedding モデルで安定してベクトル化し、後続のチャンクストアや RAG 検索で利用できる順序付きベクトル列を生成する。モデル実装を Protocol で抽象化し、ingestion パイプライン本体を具体モデル実装から分離する。
- 利用者・呼び出し元・前提条件:
  呼び出し元は ingestion 系ユースケースまたはそれに準ずるアプリケーションサービスとする。入力はチャンク分割済みであり、空本文チャンクは通常は upstream で抑止されている前提だが、本機能でも再検証する。Embedding 実行は `EmbeddingModel` Protocol を実装したアダプター経由で行い、現在の標準構成では `multilingual-e5-large` を利用する。

# 入出力

- 入力:
  `EmbeddingBatchInput` を受け取る。
  - `chunks: list[ChunkEmbeddingInput]`
    ベクトル化対象のチャンク一覧。入力順がモデル呼び出し順および結果順になる。
    - `chunk_index: int`
      ファイル内でのチャンク順序。0 以上の整数でなければならない。
    - `text: str`
      Embedding 対象の本文。検証には `strip()` を使うが、モデルへ渡す文字列自体は変更しない。
  - `embedding_model: EmbeddingModel`
    `embed(texts: list[str]) -> list[list[float]]` を提供する Protocol。呼び出し側は concrete class ではなくこのインターフェースを注入する。
  - `source_path: str | None`
    可観測性用の任意コンテキスト。ログへそのまま出力してよい。
- 出力:
  入力順を保持した `list[ChunkEmbeddingResult]` を返す。
  - `chunk_index: int`
    対応する入力チャンクの `chunk_index`。
  - `embedding: list[float]`
    そのチャンクの埋め込みベクトル。各要素は有限の実数であり、同一バッチ内の全ベクトル次元は一致しなければならない。現在の標準モデル `multilingual-e5-large` を使用する場合、次元数は 1024 である。
- エラー:
  送出する例外の型名と発生条件を定義する。
  例外型はテストで使用されるため、型名を具体的に指定すること。
  実装詳細ではなく、呼び出し元との契約として記述する。
  - `EmbeddingBatchInputError`: `chunks` または `embedding_model` が契約を満たさない場合。`chunk_index` が 0 以上の整数でない、`text` が文字列でない、`text.strip()` が空、`embedding_model.embed` が callable でないケースを含む
  - `EmbeddingModelCallError`: `embedding_model.embed(...)` の実行が失敗した場合。モデルロード失敗、推論失敗、タイムアウト、外部プロセス異常を含む
  - `EmbeddingResponseCountMismatchError`: モデルが返したベクトル件数が入力チャンク件数と一致しない場合
  - `EmbeddingVectorFormatError`: モデルが返したベクトルの形式が契約を満たさない場合。ベクトル自体が `list[float]` でない、空ベクトル、非数値、`NaN`/`inf`、バッチ内で次元不一致のケースを含む

# 具体例

代表的な入力と、それに対して期待される出力をデータ例で示す。
テストケース生成やレビューで曖昧さが出ないよう、入力・出力ともに具体値で書く。

以下の例では Protocol 実装のテストダブルが 4 次元ベクトルを返す。
本番の `multilingual-e5-large` では 1024 次元だが、振る舞い契約は同じとする。

## 例1

- 入力:
  ```yaml
  chunks:
    - chunk_index: 0
      text: "TypeScript のジェネリクスは型引数を使って再利用性を高める。"
  source_path: "study/typescript/generics.md"
  embedding_model の返却値:
    - [0.12, -0.03, 0.44, 0.08]
  ```
- 期待される出力:
  ```yaml
  - chunk_index: 0
    embedding: [0.12, -0.03, 0.44, 0.08]
  ```

## 例2

- 入力:
  ```yaml
  chunks:
    - chunk_index: 0
      text: "Docker Compose でアプリケーションを起動する。"
    - chunk_index: 1
      text: "PostgreSQL のトランザクション分離レベルを整理する。"
  source_path: "study/backend/infra.md"
  embedding_model の返却値:
    - [0.10, 0.20, 0.30, 0.40]
    - [-0.11, 0.05, 0.18, 0.09]
  ```
- 期待される出力:
  ```yaml
  - chunk_index: 0
    embedding: [0.10, 0.20, 0.30, 0.40]
  - chunk_index: 1
    embedding: [-0.11, 0.05, 0.18, 0.09]
  ```

## 例3

- 入力:
  ```yaml
  chunks: []
  source_path: "study/empty.md"
  ```
- 期待される出力:
  ```yaml
  []
  ```

## 例4

- 入力:
  ```yaml
  chunks:
    - chunk_index: 0
      text: "   "
  source_path: "study/invalid.md"
  ```
- 期待される出力:
  `EmbeddingBatchInputError` が送出される。`embedding_model.embed(...)` は呼び出されない。

# 主要ルール

1. Protocol によるモデル抽象化:
   - 条件:
     呼び出し元が Embedding 実装を注入する場合。
   - 振る舞い:
     本機能は `EmbeddingModel` Protocol の `embed(texts: list[str]) -> list[list[float]]` だけに依存する。具体モデルの import、モデル名分岐、デバイス制御は本機能の責務に含めない。
2. 空バッチの短絡終了:
   - 条件:
     `chunks` が空リストの場合。
   - 振る舞い:
     空リストを返す。`embedding_model.embed(...)` は呼び出さない。成功ログは出力する。
3. 入力チャンクの一括バリデーション:
   - 条件:
     `chunks` に 1 件以上のチャンクが含まれる場合。
   - 振る舞い:
     モデル呼び出し前に全チャンクを検証する。`chunk_index` は 0 以上の整数、`text` は文字列かつ `strip()` 後に空でないことを要求する。1 件でも不正があればバッチ全体を失敗とし、`EmbeddingBatchInputError` を送出する。
4. 1 バッチ 1 回のモデル呼び出し:
   - 条件:
     入力検証を通過した場合。
   - 振る舞い:
     全チャンク本文を入力順のまま `embedding_model.embed(texts)` に 1 回だけ渡す。チャンク単位の個別呼び出しへ分解しない。
5. 結果順序の保持:
   - 条件:
     モデルがベクトル一覧を正常に返した場合。
   - 振る舞い:
     返却結果は入力 `chunks` と同じ順序で `ChunkEmbeddingResult` に再構成する。`chunk_index` は入力値をそのまま返す。
6. モデル応答件数の一致:
   - 条件:
     モデル呼び出しが例外を送出せずに終了した場合。
   - 振る舞い:
     返却ベクトル件数が入力チャンク件数と完全一致しなければ `EmbeddingResponseCountMismatchError` を送出する。
7. ベクトル形式と次元の検証:
   - 条件:
     モデルがベクトル一覧を返した場合。
   - 振る舞い:
     各ベクトルは空でない `list[float]` として解釈可能でなければならない。各要素は有限の実数であり、同一バッチ内の全ベクトル次元は一致しなければならない。いずれかを満たさない場合は `EmbeddingVectorFormatError` を送出する。
8. モデル例外のラップ:
   - 条件:
     `embedding_model.embed(...)` が例外を送出した場合。
   - 振る舞い:
     元例外を原因として保持したまま `EmbeddingModelCallError` を送出する。呼び出し元は「モデル実行失敗」として一括で扱える。
9. structlog による構造化ログ出力:
   - 条件:
     バッチ成功時またはモデル失敗時。
   - 振る舞い:
     `structlog` で構造化ログを出力する。成功時は `embedder_batch_completed`、モデル失敗時は `embedder_model_call_failed` をイベント名とし、少なくとも `source_path`、`chunk_count`、`embedded_count`、`vector_dimension`、`invalid_chunk_count`、`model_failure_count` を含める。空バッチ成功時の `vector_dimension` は `null` としてよい。

# 境界条件

- ケース:
  `chunks` が空リスト。
  - 振る舞い:
    空リストを返す。モデル呼び出しを行わない。
  - 理由:
    ingestion パイプラインの上流が空結果を返した場合でも、後続を例外で止める必要はないため。
- ケース:
  複数チャンクのうち 1 件だけが空文字または空白のみ。
  - 振る舞い:
    バッチ全体を `EmbeddingBatchInputError` とする。正常チャンクだけを部分成功させない。
  - 理由:
    返却順序と件数の契約を保ったまま partial success を導入すると呼び出し元契約が複雑化するため。
- ケース:
  モデルが 2 件入力に対して 1 件または 3 件のベクトルを返す。
  - 振る舞い:
    `EmbeddingResponseCountMismatchError` を送出する。
  - 理由:
    入力順と出力順の対応が壊れ、後続の chunk-store へ安全に渡せないため。
- ケース:
  返却ベクトルの一部に `NaN`、`inf`、`None`、文字列が含まれる。
  - 振る舞い:
    `EmbeddingVectorFormatError` を送出する。
  - 理由:
    ベクトル検索や永続化で不正値が伝播すると障害原因の特定が難しくなるため。
- ケース:
  同一バッチで 1 件目が 1024 次元、2 件目が 768 次元。
  - 振る舞い:
    `EmbeddingVectorFormatError` を送出する。
  - 理由:
    同一コレクションへ格納するベクトルとして整合しないため。
- ケース:
  異なる `chunk_index` を持つが本文が完全一致するチャンクが複数含まれる。
  - 振る舞い:
    重複排除せず、それぞれ独立にベクトル化して結果を返す。
  - 理由:
    本機能の責務は本文の同一性判定ではなく、入力チャンク列の順序付き変換であるため。
- ルール間の相互作用:
  1. まず `embedding_model` の callable 性と `chunks` 全件の入力妥当性を検証し、不正があればモデル呼び出し前に失敗させる。
  2. `chunks` が空リストの場合のみ、個別チャンク検証より先に短絡成功してよい。
  3. モデル呼び出し後は、件数一致確認を先に行い、その後で各ベクトルの型・有限値・次元一致を検証する。
  4. モデル自身の例外は `EmbeddingModelCallError` を優先し、応答形式検証エラーとは分離する。

# 非機能・制約

- 性能:
  正常系では 1 バッチにつき 1 回のモデル呼び出しで完了すること。前処理と応答検証はチャンク数および総ベクトル要素数に対して線形時間で完了すること。
- 可観測性:
  `structlog` により、少なくとも `event`、`source_path`、`chunk_count`、`embedded_count`、`vector_dimension`、`invalid_chunk_count`、`model_failure_count` を機械可読なキーで出力できること。モデル失敗時は例外スタックトレースを含めること。
- 外部依存:
  `EmbeddingModel` Protocol を満たすアダプター実装、`structlog` のロガー設定、必要に応じて現在の標準モデル `multilingual-e5-large` を提供する `core/embedding/` 配下の実装に依存する。本仕様自身は ChromaDB や Hugging Face キャッシュ実装には依存しない。

# 技術判断

品質に直結する技術選定や実装方針がある場合は、その判断と理由を書く。

- 判断:
  空文字チャンクはゼロベクトル化せず、`EmbeddingBatchInputError` として fail-fast する。
  - 理由:
    空本文は upstream 異常の可能性が高く、ゼロベクトルで黙って通すと検索品質劣化と障害検知遅延を招くため。
- 判断:
  モデル呼び出しはチャンク単位ではなくバッチ単位で 1 回にまとめる。
  - 理由:
    モデルロードや推論オーバーヘッドを抑えつつ、要件のバッチ処理対応を明確に満たせるため。
- 判断:
  ベクトルの有効性検証には「件数一致」「空でない」「有限実数のみ」「同一バッチ内で次元一致」を含める。
  - 理由:
    下流の vector DB や検索処理に不正な数値を持ち込まないための最低限の契約だから。
- 判断:
  具体モデル名はログや設定で識別可能であっても、仕様上の主要契約は `EmbeddingModel` Protocol に閉じ込める。
  - 理由:
    将来モデルを差し替えても ingestion 本体の責務を変えず、テストダブルでも同一契約を検証できるため。

# スコープ外

この機能では扱わないこと、別 issue / 別機能で扱うことを明示する。

- 対応しないこと:
  Embedding モデルのダウンロード、キャッシュ永続化、GPU/CPU 切り替え
- 対応しないこと:
  生成したベクトルの ChromaDB への格納・更新・削除
- 対応しないこと:
  リトライ戦略、バックオフ、サーキットブレーカなどの回復制御
- 対応しないこと:
  ベクトルの正規化、次元削減、後処理最適化
- 対応しないこと:
  部分成功を返す API 契約

# 受け入れ基準

検証可能な条件をチェックリスト形式で書く。実装手段ではなく、満たされるべき事実を書く。

- [ ] `EmbeddingModel` Protocol を満たす実装が外部注入され、ingestion 本体は具体モデル型に依存しない
- [ ] 1 件以上の正常チャンクを含むバッチで、入力順を保った `ChunkEmbeddingResult` 一覧が返る
- [ ] `chunks=[]` の場合、空リストが返り、モデル呼び出しは行われない
- [ ] `text.strip()` が空のチャンクを含む場合、`EmbeddingBatchInputError` が送出される
- [ ] モデル呼び出しが失敗した場合、`EmbeddingModelCallError` が送出される
- [ ] モデル返却件数が入力件数と一致しない場合、`EmbeddingResponseCountMismatchError` が送出される
- [ ] モデル返却ベクトルに非数値・空ベクトル・次元不一致がある場合、`EmbeddingVectorFormatError` が送出される
- [ ] 正常終了時に `embedder_batch_completed`、モデル失敗時に `embedder_model_call_failed` の構造化ログが必要項目付きで出力される
- [ ] 標準モデル `multilingual-e5-large` を接続した場合、各ベクトル次元が 1024 で downstream に渡せる

# テスト観点メモ

各主要ルールに対して最低1つ、各境界条件に対して最低1つの観点を列挙する。
受け入れ基準の各項目が少なくとも1つの観点でカバーされていることを確認する。

- 正常系:
  1 件入力で 1 件のベクトルが同じ `chunk_index` 付きで返ること
  2 件以上の入力で、モデルに渡る本文順と返却結果順が一致すること
  同一本文を複数チャンクで渡しても、件数を保ったまま結果が返ること
  `multilingual-e5-large` アダプター接続時に 1024 次元ベクトルが返ること
- 境界系:
  空バッチで空リストを返し、モデルが呼ばれないこと
  1 件だけ空白文字列を含むバッチで `EmbeddingBatchInputError` になること
  モデルが空ベクトルを返した場合に `EmbeddingVectorFormatError` になること
  モデルがベクトル件数不足または超過で返した場合に `EmbeddingResponseCountMismatchError` になること
  同一バッチ内で次元不一致のベクトルを返した場合に `EmbeddingVectorFormatError` になること
- 異常系:
  `embedding_model.embed` が存在しない場合に `EmbeddingBatchInputError` になること
  `embedding_model.embed` が例外を送出した場合に `EmbeddingModelCallError` へラップされること
  ベクトル要素に `NaN`、`inf`、`None`、文字列が含まれる場合に `EmbeddingVectorFormatError` になること
  モデル失敗時に `embedder_model_call_failed` ログが例外情報付きで出力されること
