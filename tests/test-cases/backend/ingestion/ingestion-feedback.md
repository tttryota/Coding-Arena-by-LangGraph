---
status: ready
---

# テストケース一覧

# 検証焦点

| テストの種類 | 検証焦点 |
|---|---|
| Phase 1（最小骨格） | `status` / 件数 / `created_feedback` 全フィールド / `skip_reason` / 成功・スキップログ |
| Phase 2（コアロジック） | 文字数しきい値、`chunk_index` 昇順正規化、ファイル単位 1 レコード、ロードマップ通知行、insert-only |
| Phase 3（エッジケース） | `chunks=[]`、入力バリデーション、LLM 応答妥当性、保存抑止 |
| Phase 4（外部連携） | Protocol DI、依存障害の例外変換、失敗ログ、非呼び出し確認 |

## Phase 1: 最小骨格

| ID | 観点 | 前提 | 入力 | 期待結果 | 備考 |
|---|---|---|---|---|---|
| TC-01 | ロードマップ候補ありで 1 件のフィードバックを新規保存し、戻り値・保存本文・成功ログを完全検証する | `RoadmapItemReader` / `IngestionFeedbackLlmClient` / `IngestionFeedbackWriter` は Protocol を満たすテストダブルで差し替え可能。`writer.create(...)` の引数、`llm_client.analyze(...)` の引数、`structlog` 出力を検査できる | 仕様書 例1 の入力・依存返却値をそのまま使う | 戻り値は仕様書 例1 の期待結果と完全一致する。`llm_client.analyze(...)` はちょうど 1 回呼ばれ、分析対象は `chunk_index=0,1` の 2 件だけで、連結順は入力順ではなく `0 -> 1` の昇順である。`writer.create(...)` はちょうど 1 回呼ばれ、引数 `title` は `study/typescript/generics.md の取り込みフィードバック` と完全一致し、`body` は仕様書例の 6 セクション順と改行位置まで完全一致する。保存引数の `roadmap_item_id` は `11111111-1111-1111-1111-111111111111`、`is_read=false`、`read_at=null`、`created_at="2026-05-20T21:30:00+09:00"` である。`event="ingestion_feedback_created"` のログがちょうど 1 件出力され、少なくとも `source_path="study/typescript/generics.md"`、`input_chunk_count=3`、`used_chunk_count=2`、`skipped_chunk_count=1`、`roadmap_candidate_count=2`、`feedback_id="aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"` を含む。追加キーは許容する | 例1ベースの最小正常系 |
| TC-02 | ロードマップ候補 0 件でもフィードバックを作成でき、`roadmap_item_id=null` と通知行省略を維持する | `roadmap_reader.list_items()` は `[]` を返し、`llm_client.analyze(...)` に渡した候補情報を検査できる。`writer.create(...)` とログを検査できる | 仕様書 例2 の入力・依存返却値をそのまま使う | 戻り値は仕様書 例2 の期待結果と完全一致する。`llm_client.analyze(...)` はちょうど 1 回呼ばれ、候補一覧は空として渡される。`writer.create(...)` はちょうど 1 回呼ばれ、保存引数の `roadmap_item_id` は `null`、`body` には `反映先ロードマップ:` 行が含まれず、`正確性チェック:` から始まる。`event="ingestion_feedback_created"` のログがちょうど 1 件出力され、少なくとも `source_path="study/docker/compose.md"`、`input_chunk_count=1`、`used_chunk_count=1`、`skipped_chunk_count=0`、`roadmap_candidate_count=0`、`feedback_id="bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"` を含む。追加キーは許容する | 候補 0 件時の基本形 |
| TC-03 | 分析可能チャンクが 0 件ならスキップし、外部依存を呼ばず、スキップログを出す | `roadmap_reader` / `llm_client` / `writer` の呼び出し有無を検査でき、ログ収集を有効化する | 仕様書 例3 の入力を使う | 戻り値は仕様書 例3 の期待結果と完全一致する。`roadmap_reader.list_items()`、`llm_client.analyze(...)`、`writer.create(...)` はいずれも 1 回も呼ばれない。`event="ingestion_feedback_skipped"` のログがちょうど 1 件出力され、少なくとも `source_path="daily/2026-05-20.md"`、`input_chunk_count=2`、`used_chunk_count=0`、`skipped_chunk_count=2`、`roadmap_candidate_count=0` を含む。`feedback_id` は含まれないこと、追加キーは許容する | 全短文スキップの最小形 |

## Phase 2: コアロジック

| ID | 観点 | 前提 | 入力 | 期待結果 | 備考 |
|---|---|---|---|---|---|
| TC-10 | 文字数しきい値は `strip()` 後長さで判定し、しきい値ちょうどのチャンクを採用しつつ、LLM には `chunk_index` 昇順で原文を渡す | `llm_client.analyze(...)` のリクエスト本文を検査できる。`roadmap_reader.list_items()` は 1 件の候補を返す。`writer.create(...)` は正常に保存する。各依存の呼び出し回数を検査できる | `source_path="study/python/decorators.md"`、`chunks=[{chunk_index: 2, text: "  descriptor  "}, {chunk_index: 0, text: " decorator "}, {chunk_index: 1, text: " short "}]`、`minimum_chunk_characters=9`、`generated_at="2026-05-20T22:00:00+09:00"`。`llm_client` は `selected_roadmap_item_id=null`、`accuracy_check="要点は押さえている。"`, `improvement_suggestions=["具体例を追加する。"]` を返す | `used_chunk_count=2`、`skipped_chunk_count=1` で `status="created"` を返す。分析対象は `text.strip()` 長が 9 以上の `chunk_index=0`（`" decorator "`、strip 後 9 文字）と `chunk_index=2`（`"  descriptor  "`、strip 後 10 文字）の 2 件で、`chunk_index=1`（`" short "`、strip 後 5 文字）は除外される。`llm_client.analyze(...)` はちょうど 1 回呼ばれ、`chunk_texts` は原文のまま `[" decorator ", "  descriptor  "]` の順（`chunk_index` 昇順、strip しない）である。`roadmap_reader.list_items()` はちょうど 1 回呼ばれる。`writer.create(...)` はちょうど 1 回呼ばれ、保存は 1 レコードだけ作成される | しきい値境界と順序正規化を同時確認 |
| TC-11 | ロードマップ候補は存在しても、LLM が `selected_roadmap_item_id=null` を返した場合は通知行なしで保存する | 候補 2 件を返す `roadmap_reader`、`writer.create(...)` の保存本文を検査できるテストダブルを使う。各依存の呼び出し回数と引数を検査できる | `source_path="study/network/http.md"`、分析可能チャンク 1 件、`minimum_chunk_characters=10`、`generated_at="2026-05-20T22:05:00+09:00"`。候補は `HTTP` と `TCP`。LLM は `selected_roadmap_item_id=null`、`accuracy_check="HTTP の概要説明として妥当。"`、`improvement_suggestions=["ステータスコードの具体例を追加する。"]` を返す | 戻り値は `status="created"`、`created_feedback.roadmap_item_id=null` となる。`roadmap_reader.list_items()` はちょうど 1 回呼ばれる。`llm_client.analyze(...)` はちょうど 1 回呼ばれ、`roadmap_candidates` に候補 2 件が渡される。`writer.create(...)` はちょうど 1 回呼ばれる。保存本文は `正確性チェック:` から始まり、`反映先ロードマップ:` 行を含まない。候補が存在したことを理由にダミーの通知行を入れない | 候補あり・未選択の境界 |
| TC-12 | 複数の分析可能チャンクがあっても、ファイル単位で LLM 1 回・保存 1 回・作成レコード 1 件だけに集約する | `roadmap_reader`、`llm_client`、`writer` の呼び出し回数を検査できる | `source_path="study/rust/ownership.md"`、分析可能チャンク 4 件（`chunk_index=0,1,2,3`、各テキストは `minimum_chunk_characters=5` 以上）、`generated_at="2026-05-20T22:10:00+09:00"` | `status="created"` を返し、`used_chunk_count=4`、`skipped_chunk_count=0` となる。`roadmap_reader.list_items()` はちょうど 1 回、`llm_client.analyze(...)` はちょうど 1 回、`writer.create(...)` はちょうど 1 回呼ばれる。チャンクごとの個別レコード作成は行われない。`llm_client.analyze(...)` の `chunk_texts` は 4 件を含む | 主要ルール 1 と非機能の呼び出し回数制約 |
| TC-13 | 同じ `source_path` の再取り込みでは旧レコードを残したまま新規 `create(...)` で追記する | 事前状態として `source_path="study/typescript/generics.md"` の既存フィードバック 1 件を保持した `writer` テストダブルを使い、保存後の件数を確認できる | 仕様書 例4 の入力を使う。`roadmap_reader` と `llm_client` は正常応答する | 戻り値は `status="created"` で、新しく返る `created_feedback.id` は既存 ID と異なる。保存処理は更新ではなく `create(...)` による新規追加としてちょうど 1 回実行され、保存後に同一 `source_path` のレコード件数は 2 件になる。旧レコード内容は保持される | insert-only の履歴保持 |

## Phase 3: エッジケース

| ID | 観点 | 前提 | 入力 | 期待結果 | 備考 |
|---|---|---|---|---|---|
| TC-20 | `chunks=[]` はスキップし、件数 0 / 外部依存未呼び出し / スキップログを返す | `roadmap_reader` / `llm_client` / `writer` の呼び出し有無とログを検査できる | `source_path="study/empty.md"`、`chunks=[]`、`minimum_chunk_characters=10`、`generated_at="2026-05-20T22:15:00+09:00"` | 戻り値は `{status: "skipped", used_chunk_count: 0, skipped_chunk_count: 0, created_feedback: null, skip_reason: "no_analyzable_chunks"}` と完全一致する。外部依存は 1 回も呼ばれない。`event="ingestion_feedback_skipped"` のログがちょうど 1 件出力され、少なくとも `source_path="study/empty.md"`、`input_chunk_count=0`、`used_chunk_count=0`、`skipped_chunk_count=0`、`roadmap_candidate_count=0` を含む。追加キーは許容する | `chunks=[]` 専用境界 |
| TC-21 | 入力契約違反は `IngestionFeedbackInputError` を送出し、しきい値判定や外部依存呼び出しへ進まない | `roadmap_reader` / `llm_client` / `writer` の呼び出し有無を検査できる | ケースA: `source_path=""`。ケースB: `minimum_chunk_characters=0`。ケースC: `generated_at="2026/05/20 22:20"`。ケースD: `chunks=[{chunk_index:-1, text:"valid text"}]`。ケースE: `chunks=[{chunk_index:0, text:"valid text A"}, {chunk_index:0, text:"valid text B"}]` | 各ケースで `IngestionFeedbackInputError` を送出する（例外型のみ検証し、message 内容は検証対象外）。`roadmap_reader.list_items()`、`llm_client.analyze(...)`、`writer.create(...)` は各ケースで 1 回も呼ばれない。`status` や部分結果は返さない | バリデーション優先 |
| TC-22 | LLM 応答の契約違反は `IngestionFeedbackResponseFormatError` として扱い、保存しない | `writer.create(...)` の呼び出し有無を検査できる。必要に応じて候補一覧あり・なしを切り替えられる | ケースA: 候補 2 件ありで `selected_roadmap_item_id` が候補外 UUID。ケースB: 候補 0 件で `selected_roadmap_item_id` が非 `null`。ケースC: `improvement_suggestions=[]`。ケースD: `accuracy_check` が必須項目欠落。ケースE: `accuracy_check="   "` のみ | 各ケースで `IngestionFeedbackResponseFormatError` を送出する。`writer.create(...)` は各ケースで 1 回も呼ばれない。成功ログは出力されない | 応答妥当性の境界を集約 |

## Phase 4: 外部連携

| ID | 観点 | 前提 | 入力 | 期待結果 | 備考 |
|---|---|---|---|---|---|
| TC-30 | Protocol だけを満たす依存オブジェクトで生成処理を完結でき、concrete class への依存がない | Protocol が定義するメソッド（`list_items()`、`analyze()`、`create()`）だけを持ち、`__slots__ = ()` を設定した最小スタブを注入する。Protocol 外の属性アクセスがあれば `AttributeError` で失敗する | 任意の正常入力 1 件。例: `source_path="study/go/interfaces.md"`、分析可能チャンク 1 件、`minimum_chunk_characters=5`、`generated_at="2026-05-20T22:25:00+09:00"` | `status="created"` を返し、処理は成功する。依存オブジェクトに対するアクセスは Protocol で定義されたメソッド呼び出しだけで完了し、追加属性や concrete class 固有 API への参照は発生しない | 主要ルール 10 の確認 |
| TC-31 | ロードマップ取得失敗時は `IngestionFeedbackRoadmapLookupError` を送出し、後続依存を呼ばず、失敗ログを出す | `roadmap_reader.list_items()` が `TimeoutError("roadmap timeout")` を送出する。`llm_client` / `writer` の呼び出し有無とログを検査できる | 分析可能チャンク 1 件の正常入力 | `IngestionFeedbackRoadmapLookupError` を送出する。`llm_client.analyze(...)` と `writer.create(...)` は 1 回も呼ばれない。`event="ingestion_feedback_roadmap_lookup_failed"` のログがちょうど 1 件出力され、少なくとも `source_path`、`input_chunk_count`、`used_chunk_count`、`skipped_chunk_count`、`roadmap_candidate_count=0`、`error_type="TimeoutError"` を含む。追加キーは許容する | 外部依存エラー 1 |
| TC-32 | LLM 呼び出し失敗時は `IngestionFeedbackLlmCallError` を送出し、保存せず、失敗ログを出す | `roadmap_reader.list_items()` は正常に候補一覧を返し、`llm_client.analyze(...)` が `ConnectionError("llm unavailable")` を送出する。`writer` とログを検査できる | 分析可能チャンク 2 件の正常入力 | `IngestionFeedbackLlmCallError` を送出する。`writer.create(...)` は 1 回も呼ばれない。`event="ingestion_feedback_llm_failed"` のログがちょうど 1 件出力され、少なくとも `source_path`、`input_chunk_count`、`used_chunk_count`、`skipped_chunk_count`、`roadmap_candidate_count`、`error_type="ConnectionError"` を含む。追加キーは許容する | 外部依存エラー 2 |
| TC-33 | 保存失敗時は `IngestionFeedbackPersistenceError` を送出し、失敗ログを出す | `roadmap_reader` と `llm_client` は正常。`writer.create(...)` が `RuntimeError("insert failed")` を送出する。ログを検査できる | 分析可能チャンク 1 件の正常入力 | `IngestionFeedbackPersistenceError` を送出する。`event="ingestion_feedback_persist_failed"` のログがちょうど 1 件出力され、少なくとも `source_path`、`input_chunk_count`、`used_chunk_count`、`skipped_chunk_count`、`roadmap_candidate_count`、`error_type="RuntimeError"` を含む。追加キーは許容する | 外部依存エラー 3 |

# 網羅性チェック

仕様書の受け入れ基準の各項目に対応するテストケース ID を記載する。
全項目が少なくとも1つのテストケースでカバーされていることを確認する。

| 受け入れ基準 | 対応テストケース |
|---|---|
| 分析可能チャンクが 1 件以上あるファイルでは、フィードバックが 1 レコードだけ新規保存される | TC-01, TC-02, TC-12 |
| 短すぎるチャンクは分析対象から除外され、全チャンクが短い場合のみ保存がスキップされる | TC-03, TC-10 |
| ロードマップ候補が 0 件のとき、保存レコードの `roadmap_item_id` は `null` で、本文に反映先ロードマップ行が含まれない | TC-02 |
| ロードマップ候補があるとき、LLM が返した候補内 ID だけが `roadmap_item_id` として保存される | TC-01, TC-22 |
| 保存レコードは常に `is_read=false`、`read_at=null`、`created_at=generated_at` で作成される | TC-01, TC-02 |
| 同じ `source_path` の再取り込みでは旧フィードバックを残したまま新規レコードが追加される | TC-13 |
| 成功・スキップ・失敗の各ケースで structlog のイベント名と主要フィールドが定義どおり出力される | TC-01, TC-02, TC-03, TC-20, TC-31, TC-32, TC-33 |
| 具体例から期待される保存本文と戻り値を一意に判断できる | TC-01, TC-02, TC-03 |

# 記述ルール

- 仕様書に明記された振る舞いだけを前提にする
- 仕様未記載の振る舞いを期待結果に置く場合は `[要仕様追記]` タグを付ける
- 正常系・境界系・異常系が重複なく網羅されていることを確認する
- 仕様書の受け入れ基準の各項目に対応するテストケースが最低1つあることを確認する
- 期待結果に「含まれる」「完全一致」「少なくとも1件」「ちょうど1件」などの検証粒度を明示する
- ログ検証を含む場合は、検証対象イベント名、必須キー、期待値、件数制約、追加キー許容の有無を明示する
- 例外検証を含む場合は、例外型、message、cause chain、ログ記録有無のうち何を確認するかを明示する
- テストが「存在確認」なのか「内容検証」なのかを期待結果で区別して書く
- テストケース文書に書いていない検証を impl レビューで追加要求しなくて済む粒度まで、期待結果を具体化する
