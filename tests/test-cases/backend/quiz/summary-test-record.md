---
status: ready
---

# テストケース一覧

# 検証焦点

| テストの種類 | 検証焦点 |
|---|---|
| Phase 1（最小骨格） | `record_summary_test(...)` の公開契約、`SummaryAnalysis` の `score` / `analysis`、`SummaryTestStore.save_result(...)` への保存引数 |
| Phase 2（コアロジック） | `roadmap_item_title` / `roadmap_item_description` が対象ロードマップ項目の LLM コンテキストとして使われること、`state["answers"]` の全回答が欠落なく LLM に渡ること、LLM が返した分析結果が保存経路に使われること |
| Phase 3（エッジケース） | `roadmap_item_level` による early return、同一項目の複数回実施で `save_result(...)` に別 `session_id` の保存要求が発行されること、`score` 境界値 `0` / `100` が保存要求にそのまま渡ること |
| Phase 4（外部連携） | `SummaryTestLlmClient` / `SummaryTestStore` の正常連携、依存先が生成した `SummaryTestRecordError` の再送出、非再試行、構造化ログちょうど1件 |

## Phase 1: 最小骨格

| ID | 観点 | 前提 | 入力 | 期待結果 | 備考 |
|---|---|---|---|---|---|
| TC-01 | `middle` レベルのまとめテスト起動時に `SummaryTestResult` 保存要求が生成される | 呼び出し側がまとめテスト完了と判定した `roadmap_item_level="middle"` の `SessionState` があり、`answers` に配下の具体項目を横断した回答履歴が1件以上ある。`llm.analyze_session()` は `SummaryAnalysis(score=65, analysis="型の基礎知識は十分ですが、ジェネリクスの実践的な使用に課題があります。特に型パラメータを使った関数を自力で書く場面で構文ミスが目立ちました。また、型推論の仕組みは理解していますが、いつ明示的に型を指定すべきかの判断基準が曖昧です。ジェネリクスの実践問題を重点的に復習することを推奨します。")` を返す | `state={"session_id":"sess_mid_001","roadmap_item_id":"rm_typescript_basic","roadmap_item_level":"middle","roadmap_item_title":"TypeScript > 基礎","roadmap_item_description":"型注釈、型推論、ジェネリクスの基礎を扱う","answers":[{"question_number":1,"confirmation_point_id":"cp_001","question_text":"型推論とは何ですか","answer_type":"textarea","answer_text":"文脈から型を決める仕組みです","score":72,"feedback":"概念は説明できています"},{"question_number":2,"confirmation_point_id":"cp_002","question_text":"ジェネリック関数を書いてください","answer_type":"code","answer_text":"function id<T>(value: T): T { return value }","score":58,"feedback":"基本形は書けています"}]}` を渡して `record_summary_test(state, llm=..., store=...)` を実行する | `llm.analyze_session()` はちょうど1回呼ばれる。`store.save_result()` はちょうど1回呼ばれ、`session_id="sess_mid_001"`、`roadmap_item_id="rm_typescript_basic"`、`score=65` が保存要求に使われる。`analysis` は当該実行で LLM が返した分析結果に対応する保存経路の入力として使われる。処理は非エラーで完了し、構造化ログ `event="summary_test_record_failed"` は0件である | 受け入れ基準「呼び出し側がまとめテスト完了と判定して `record_summary_test` を起動した時にSummaryTestResultが作成される」「analysisが生成される」「scoreが0〜100」に対応 |

## Phase 2: コアロジック

| ID | 観点 | 前提 | 入力 | 期待結果 | 備考 |
|---|---|---|---|---|---|
| TC-10 | `major` レベルでは対象ロードマップ項目の `title` / `description` と全回答が LLM コンテキストに使われ、セッション全体分析が保存経路に使われる | 呼び出し側がまとめテスト完了と判定した `roadmap_item_level="major"` の `SessionState` があり、`answers` には知識問題と実践問題が混在した3件の履歴がある。`llm.analyze_session()` の呼び出し引数を観測でき、`SummaryAnalysis(score=78, analysis="概念理解は安定していますが、実践問題になるとジェネリクス境界と明示的な型指定の判断に揺れがあります。知識問題より実装問題の得点が低く、具体項目間で理解度に偏りがあります。次は境界付きジェネリクスと型引数を明示する場面を重点的に復習してください。")` を返す | `state={"session_id":"sess_major_001","roadmap_item_id":"rm_typescript","roadmap_item_level":"major","roadmap_item_title":"TypeScript","roadmap_item_description":"型システム全体の理解を確認するまとめテスト","answers":[{"question_number":1,"confirmation_point_id":"cp_001","question_text":"型推論の仕組みを説明してください","answer_type":"textarea","answer_text":"引数や代入先から型を推論します","score":84,"feedback":"概念は理解できています"},{"question_number":2,"confirmation_point_id":"cp_002","question_text":"境界付きジェネリクスを使った関数を書いてください","answer_type":"code","answer_text":"function pickId<T extends { id: string }>(value: T) { return value.id }","score":63,"feedback":"境界指定はできています"},{"question_number":3,"confirmation_point_id":"cp_003","question_text":"型引数を明示すべき場面を説明してください","answer_type":"textarea","answer_text":"推論が曖昧な時です","score":56,"feedback":"判断基準がまだ曖昧です"}]}` を渡して `record_summary_test(state, llm=..., store=...)` を実行する | `llm.analyze_session()` の第1・第2引数は、対象ロードマップ項目を表す `title` / `description` の LLM コンテキストとして使われることが観測できる。第3引数 `answers` には `state["answers"]` の全3回答が欠落なく含まれる。raw 文字列完全一致、trim 禁止、空白正規化禁止、順序固定、DTO表現の無変換、各要素の全フィールド完全一致は検証対象にしない。`store.save_result()` に渡される `analysis` は当該実行で LLM が返した分析結果に対応する保存経路の入力として使われる | 受け入れ基準「全QuizAnswerをLLMに渡す」「セッション全体を俯瞰した分析を保存する」に対応 |

## Phase 3: エッジケース

| ID | 観点 | 前提 | 入力 | 期待結果 | 備考 |
|---|---|---|---|---|---|
| TC-20 | `detail` レベルのセッションでは early return し、`SummaryTestResult` を作成しない | 呼び出し側が当該セッション終了後に `record_summary_test` を起動する。`roadmap_item_level="detail"` の `SessionState` があり、`answers` は1件以上ある。`llm` / `store` の呼び出し有無を観測できる | `state={"session_id":"sess_detail_001","roadmap_item_id":"rm_ts_generics_detail","roadmap_item_level":"detail","roadmap_item_title":"TypeScript > ジェネリクス > 基本","roadmap_item_description":"detail項目の確認","answers":[{"question_number":1,"confirmation_point_id":"cp_001","question_text":"ジェネリクスとは何ですか","answer_type":"textarea","answer_text":"複数の型に対応する仕組みです","score":70,"feedback":"概念は説明できています"}]}` を渡して `record_summary_test(state, llm=..., store=...)` を実行する | 処理は非エラーで完了する。`llm.analyze_session()` は0回、`store.save_result()` は0回である。`SummaryTestResult` は新規作成されない。構造化ログ `event="summary_test_record_failed"` は0件である | 受け入れ基準「detail項目のセッションではSummaryTestResultが作成されない」に対応 |
| TC-21 | 同一 `roadmap_item_id` のまとめテストを複数回実施すると履歴蓄積に対応する別保存要求が発行される | 同じ `roadmap_item_id` に対して、呼び出し側がまとめテスト完了と判定した `middle` または `major` レベルの `SessionState` を `session_id` だけ変えて2回分用意できる。各回の `llm.analyze_session()` は別の `SummaryAnalysis` を返し、`store.save_result()` の呼び出し引数を観測できる | 1回目に `session_id="sess_hist_001"`、2回目に `session_id="sess_hist_002"`、いずれも `roadmap_item_id="rm_typescript_basic"` の `record_summary_test(...)` を順に実行する | 2回とも非エラーで完了する。`store.save_result()` は同一 `roadmap_item_id="rm_typescript_basic"` に対して2回呼ばれ、1回目は `session_id="sess_hist_001"`、2回目は `session_id="sess_hist_002"` を引数として受ける。各呼び出しは独立した保存要求として観測でき、後続実行で先行結果を上書きする単一更新契約は要求しない | 受け入れ基準「同一項目の複数回テスト結果が履歴として蓄積される」に対応 |
| TC-22 | `score` の境界値 `0` と `100` はいずれも有効値として保存要求に渡される | 呼び出し側がまとめテスト完了と判定した `SessionState` を2件用意できる。1件目の `llm.analyze_session()` は `SummaryAnalysis(score=0, analysis="基礎概念の取り違えが多く、全体的に再学習が必要です。")`、2件目は `SummaryAnalysis(score=100, analysis="知識問題・実践問題ともに安定しており、全体理解は十分です。")` を返す。`store.save_result()` の呼び出し引数を観測できる | 1回目に `middle` レベルの `record_summary_test(...)`、2回目に `major` レベルの `record_summary_test(...)` を実行する | 2回とも非エラーで完了する。1回目の `store.save_result()` 引数 `score` は `0`、2回目の `store.save_result()` 引数 `score` は `100` と完全一致する。境界値が丸め込み、拒否、欠損なく保存要求にそのまま渡る | 受け入れ基準「scoreが0〜100で算出される」の閉区間境界確認 |

## Phase 4: 外部連携

| ID | 観点 | 前提 | 入力 | 期待結果 | 備考 |
|---|---|---|---|---|---|
| TC-30 | `SummaryTestLlmClient` と `SummaryTestStore` の正常連携では各1回の呼び出しで完了し、失敗ログを出さない | `llm.analyze_session()` と `store.save_result()` の呼び出し回数を観測でき、どちらも成功する | 呼び出し側がまとめテスト完了と判定した任意の `middle` または `major` レベルの `SessionState` を渡して `record_summary_test(state, llm=..., store=...)` を実行する | `llm.analyze_session()` はちょうど1回、`store.save_result()` はちょうど1回呼ばれる。自動再試行は行われない。処理は非エラーで完了する。構造化ログ `event="summary_test_record_failed"` は0件である | 外部連携の正常経路確認 |
| TC-31 | LLM 呼び出し失敗時は `SummaryTestRecordError` を1件ログ出力して再送出する | `llm.analyze_session()` が `__cause__` に依存先例外を持つ `SummaryTestRecordError(error_code="llm_request_failed", message="summary test record llm request failed")` を送出し、`structlog` 出力を観測できる | 呼び出し側がまとめテスト完了と判定した任意の `middle` または `major` レベルの `SessionState` で `record_summary_test(state, llm=..., store=...)` を実行する | `SummaryTestRecordError` が送出される。`error_code` は `llm_request_failed`、`message` は `summary test record llm request failed` と完全一致し、`__cause__` は元例外を保持する。`llm.analyze_session()` はちょうど1回呼ばれ、自動再試行は行われない。`store.save_result()` は0回である。構造化ログは `event="summary_test_record_failed"` を持つログがちょうど1件出力される。必須キーは `event` のみとし、追加キーは許容する | 異常系 `llm_request_failed` |
| TC-32 | LLM 応答から `score` / `analysis` を抽出できない時は `SummaryTestRecordError` を1件ログ出力して再送出する | `llm.analyze_session()` が `__cause__` にパース例外を持つ `SummaryTestRecordError(error_code="llm_response_parse_failed", message="summary test record llm response parse failed")` を送出し、`structlog` 出力を観測できる | 呼び出し側がまとめテスト完了と判定した任意の `middle` または `major` レベルの `SessionState` で `record_summary_test(state, llm=..., store=...)` を実行する | `SummaryTestRecordError` が送出される。`error_code` は `llm_response_parse_failed`、`message` は `summary test record llm response parse failed` と完全一致し、`__cause__` は元例外を保持する。`llm.analyze_session()` はちょうど1回呼ばれ、自動再試行は行われない。`store.save_result()` は0回である。構造化ログは `event="summary_test_record_failed"` を持つログがちょうど1件出力される。必須キーは `event` のみとし、追加キーは許容する | 異常系 `llm_response_parse_failed` |
| TC-33 | 永続化失敗時は `SummaryTestRecordError` を1件ログ出力して再送出する | `llm.analyze_session()` は正常に `SummaryAnalysis` を返す。`SummaryTestStore` の契約どおり、`store.save_result()` が `__cause__` にDB例外を持つ `SummaryTestRecordError(error_code="persistence_failed", message="summary test record persistence failed")` を送出し、`structlog` 出力を観測できる | 呼び出し側がまとめテスト完了と判定した任意の `middle` または `major` レベルの `SessionState` で `record_summary_test(state, llm=..., store=...)` を実行する | `SummaryTestRecordError` が送出される。`error_code` は `persistence_failed`、`message` は `summary test record persistence failed` と完全一致し、`__cause__` は元例外を保持する。`llm.analyze_session()` はちょうど1回、`store.save_result()` はちょうど1回呼ばれ、自動再試行は行われない。構造化ログは `event="summary_test_record_failed"` を持つログがちょうど1件出力される。必須キーは `event` のみとし、追加キーは許容する | 異常系 `persistence_failed` |

# 網羅性チェック

仕様書の受け入れ基準の各項目に対応するテストケース ID を記載する。
全項目が少なくとも1つのテストケースでカバーされていることを確認する。

| 受け入れ基準 | 対応テストケース |
|---|---|
| 呼び出し側がまとめテスト完了と判定して `record_summary_test` を起動した時にSummaryTestResultが作成される | TC-01 |
| LLMによる定性分析（analysis）が生成される | TC-01, TC-10 |
| scoreが0〜100で算出される | TC-01, TC-22 |
| detail項目のセッションではSummaryTestResultが作成されない | TC-20 |
| 同一項目の複数回テスト結果が履歴として蓄積される | TC-21 |

# 記述ルール

- 仕様書に明記された振る舞いだけを前提にする
- 仕様未記載の振る舞いを期待結果に置く場合は `[要仕様追記]` タグを付ける
- 正常系・境界系・異常系が重複なく網羅されていることを確認する
- 仕様書の受け入れ基準の各項目に対応するテストケースが最低1つあることを確認する
- 期待結果に「含まれる」「完全一致」「少なくとも1件」「ちょうど1件」などの検証粒度を明示する
- `answers` の受け渡しでは、仕様に明記された「全回答が欠落なく渡る」ことまでを検証対象とし、順序固定、DTO表現の無変換、各フィールド完全一致は仕様追記なしに要求しない
- `roadmap_item_title` / `roadmap_item_description` の受け渡しでは、対象ロードマップ項目の LLM コンテキストとして使われることまでを検証対象とし、raw 文字列完全一致、trim 禁止、空白正規化禁止、要約禁止、再整形禁止は仕様追記なしに要求しない
- `analysis` の保存では、LLM が返した分析結果が保存経路に使われることまでを検証対象とし、無加工保存、前後空白処理禁止、要約禁止、再整形禁止は仕様追記なしに要求しない
- 永続化については `SummaryTestStore.save_result(...)` への保存要求までを検証対象とし、保存後 read-back、取得 API、観測可能フィールドの追加契約は `summary-test-record` の仕様追記なしに要求しない
- ログ検証を含む場合は、検証対象イベント名、必須キー、期待値、件数制約、追加キー許容の有無を明示する
- 例外検証を含む場合は、例外型、message、cause chain、ログ記録有無のうち何を確認するかを明示する
- テストが「存在確認」なのか「内容検証」なのかを期待結果で区別して書く
- テストケース文書に書いていない検証を impl レビューで追加要求しなくて済む粒度まで、期待結果を具体化する
