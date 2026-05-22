---
status: ready
---

# テストケース一覧

# 検証焦点

| テストの種類 | 検証焦点 |
|---|---|
| Phase 1（最小骨格） | `SessionState.roadmap_item_title` / `SessionState.roadmap_item_description` / `SessionState.roadmap_item_level` を読み、確認ポイント一覧と `current_point_index=0` を返す基本契約 |
| Phase 2（コアロジック） | `ConfirmationPoint` DTO、通常系の確認ポイント数3〜5件目標、`format` の公開契約、まとめテスト時の入力スコープ契約 |
| Phase 3（エッジケース） | `description` 空、概念項目での全件 `format="knowledge"`、件数逸脱時の警告継続 |
| Phase 4（外部連携） | 注入した `QuestionSetDesignLlmClient` が送出する `QuestionSetDesignError` の伝播、非再試行、構造化ログちょうど1件 |

## Phase 1: 最小骨格

| ID | 観点 | 前提 | 入力 | 期待結果 | 備考 |
|---|---|---|---|---|---|
| TC-01 | `design_question_set` が `SessionState` から必要情報を読み、戻り値の基本形を返す | `state` に `roadmap_item_title`, `roadmap_item_description`, `roadmap_item_level` が設定され、`llm.generate_confirmation_points()` は `ConfirmationPoint` DTO 3件を返す | `state={"roadmap_item_title":"TypeScript ジェネリクス","roadmap_item_description":"型パラメータと推論の理解を確認する","roadmap_item_level":"detail"}` を渡して `design_question_set(state, llm=...)` を実行する | `llm.generate_confirmation_points()` がちょうど1回呼ばれ、引数 `title`, `description`, `level` は `state` の値と完全一致する。戻り値はキー `confirmation_points`, `current_point_index` のちょうど2件を持つ dict である。`confirmation_points` は LLM 返却値と完全一致し、`current_point_index` は `0` と完全一致する | LangGraph ノードの最小契約確認 |
| TC-02 | ロードマップ項目から確認ポイントリストが生成され、各ポイントが `ConfirmationPoint` DTO で返る | `llm.generate_confirmation_points()` が仕様準拠の確認ポイントを返す | `roadmap_item_title="非同期処理の基本"`, `roadmap_item_description="Promise と async/await の役割を理解する"`, `roadmap_item_level="detail"` を含む `SessionState` を渡す | `confirmation_points` が少なくとも1件生成される。各要素は `id`(非空文字列), `content`(非空文字列), `format`(`"knowledge"` または `"knowledge_and_practice"`) を必ず持つ。返却リスト内で `id` は全件一意である。`current_point_index` は `0` である | 受け入れ基準「確認ポイントリスト生成」「各確認ポイントは ConfirmationPoint DTO」をまとめて確認する |

## Phase 2: コアロジック

| ID | 観点 | 前提 | 入力 | 期待結果 | 備考 |
|---|---|---|---|---|---|
| TC-10 | 通常の詳細項目では確認ポイント数が3〜5件に収まる | `llm.generate_confirmation_points()` が通常系として確認ポイント 3〜5 件を返す | `roadmap_item_title="ジェネリクスの基本構文と型パラメータ"`, `roadmap_item_description="TypeScriptのジェネリクスの基本的な構文と、型パラメータの使い方を理解する"`, `roadmap_item_level="detail"` を含む `SessionState` を渡す | `confirmation_points` の件数が `3` 以上 `5` 以下である。各要素の `format` は `"knowledge"` または `"knowledge_and_practice"` のいずれかである。`current_point_index` は `0` である | 通常系での件数目標を確認する |
| TC-11 | `format` の公開契約として `knowledge_and_practice` と `knowledge` をそのまま返せる | `llm.generate_confirmation_points()` が、コードで表現できるポイント 1 件を `format="knowledge_and_practice"`、概念的ポイント 1 件を `format="knowledge"` として含む仕様準拠 DTO リストを返す | `roadmap_item_title="ジェネリクスの基本構文と型パラメータ"`, `roadmap_item_description="TypeScriptのジェネリクスの基本的な構文と、型パラメータの使い方を理解する"`, `roadmap_item_level="detail"` を含む `SessionState` を渡す | 戻り値の `confirmation_points` は LLM 返却値と完全一致する。したがって、stubbed LLM 出力に含めた `format="knowledge_and_practice"` の確認ポイントが少なくとも 1 件、`format="knowledge"` の確認ポイントが少なくとも 1 件そのまま返る。特定文言との意味一致は検証対象外とする | node の公開契約として `format` の受け渡しを確認する |
| TC-12 | まとめテスト（`roadmap_item_level="middle"` / `roadmap_item_level="major"`）でも入力スコープ契約どおりに `ConfirmationPoint` を返す | `llm.generate_confirmation_points()` が `middle` / `major` 向けの仕様準拠 `ConfirmationPoint` DTO を返す | `roadmap_item_title`, `roadmap_item_description`, `roadmap_item_level` に加えて他の `SessionState` キーを含む状態を渡し、`roadmap_item_level` は `middle` または `major` とする | `llm.generate_confirmation_points()` が `title=state["roadmap_item_title"]`, `description=state["roadmap_item_description"]`, `level=state["roadmap_item_level"]` でちょうど1回呼ばれる。処理は非エラーで完了し、戻り値の `confirmation_points` は LLM 返却値と完全一致する。各要素は `id`, `content`, `format` を持つ `ConfirmationPoint` DTO であり、`current_point_index` は `0` である | まとめテストで追加データソースを参照しない公開契約だけを確認する |

## Phase 3: エッジケース

| ID | 観点 | 前提 | 入力 | 期待結果 | 備考 |
|---|---|---|---|---|---|
| TC-20 | `roadmap_item_description` が空でも `roadmap_item_title` のみから確認ポイントを設計できる | `llm.generate_confirmation_points()` が `description=""` を受け取り、仕様準拠の確認ポイントを返せる | `state={"roadmap_item_title":"再帰関数の基本","roadmap_item_description":"","roadmap_item_level":"detail"}` を渡して `design_question_set` を実行する | `llm.generate_confirmation_points()` が `title=state["roadmap_item_title"]`, `description=state["roadmap_item_description"]`, `level=state["roadmap_item_level"]` でちょうど1回呼ばれる。処理は非エラーで完了し、`confirmation_points` の件数は `3` 以上 `5` 以下である。`current_point_index` は `0` である | 境界条件「descriptionが空」に対応 |
| TC-21 | 概念的な項目では全確認ポイントが `format="knowledge"` になる | LLM が概念項目を設計できる | `roadmap_item_title="プログラミングパラダイムの比較"`, `roadmap_item_description="オブジェクト指向・関数型・手続き型の違いと使い分けを理解する"`, `roadmap_item_level="detail"` を含む `SessionState` を渡す | `confirmation_points` の件数が `3` 以上 `5` 以下である。全要素の `format` が `"knowledge"` と完全一致する。`"knowledge_and_practice"` の確認ポイントは `0` 件である | 境界条件「コード実践が不適切な概念項目」に対応 |
| TC-22 | LLM が3〜5件を外しても警告して継続する | `llm.generate_confirmation_points()` が仕様外件数のリストを返し、ログを観測できる | `llm.generate_confirmation_points()` が確認ポイント `2` 件または `6` 件を返すようにして `design_question_set` を実行する | 処理は非エラーで完了し、戻り値の `confirmation_points` は LLM 返却値と完全一致する件数で返る。`current_point_index` は `0` である。warning レベルのログが少なくとも1件出力される | 仕様どおり「LLMの出力を尊重して続行する」を確認する。warning ログのイベント名・必須キーは仕様未記載のため検証対象外 |

## Phase 4: 外部連携

| ID | 観点 | 前提 | 入力 | 期待結果 | 備考 |
|---|---|---|---|---|---|
| TC-30 | 注入した `QuestionSetDesignLlmClient` がリクエスト失敗由来の `QuestionSetDesignError` を送出した場合、`design_question_set` はそのまま伝播する | `llm.generate_confirmation_points()` が、`__cause__` に依存先例外を持つ `QuestionSetDesignError(error_code="llm_request_failed", message="question set design llm request failed")` を送出し、ログを観測できる | 任意の `roadmap_item_title` / `roadmap_item_description` / `roadmap_item_level` を含む `SessionState` で `design_question_set` を実行する | `QuestionSetDesignError` が送出される。`error_code` は `llm_request_failed`、`message` は `question set design llm request failed` と完全一致する。`__cause__` は元の依存先例外を保持する。LLM 呼び出しはちょうど1回で、自動再試行は行われない。構造化ログは `event="question_set_design_failed"` を持つログがちょうど1件出力される。追加キーは許容する | リクエスト失敗分類責務は client 側、単一ログ出力責務は node 側であることを確認する |
| TC-31 | 注入した `QuestionSetDesignLlmClient` が JSON パース由来の `QuestionSetDesignError` を送出した場合、`design_question_set` はそのまま伝播する | `llm.generate_confirmation_points()` が、`__cause__` に JSON パース例外を持つ `QuestionSetDesignError(error_code="llm_response_parse_failed", message="question set design llm response parse failed")` を送出し、ログを観測できる | 任意の `roadmap_item_title` / `roadmap_item_description` / `roadmap_item_level` を含む `SessionState` で `design_question_set` を実行する | `QuestionSetDesignError` が送出される。`error_code` は `llm_response_parse_failed`、`message` は `question set design llm response parse failed` と完全一致する。`__cause__` は元の JSON パース例外を保持する。LLM 呼び出しはちょうど1回で、自動再試行は行われない。構造化ログは `event="question_set_design_failed"` を持つログがちょうど1件出力される。追加キーは許容する | JSON パース分類責務は client 側、単一ログ出力責務は node 側であることを確認する |
| TC-32 | 注入した `QuestionSetDesignLlmClient` がスキーマ不整合由来の `QuestionSetDesignError` を送出した場合、`design_question_set` はそのまま伝播する | `llm.generate_confirmation_points()` が、`__cause__` にスキーマ検証例外を持つ `QuestionSetDesignError(error_code="llm_response_parse_failed", message="question set design llm response parse failed")` を送出し、ログを観測できる | 任意の `roadmap_item_title` / `roadmap_item_description` / `roadmap_item_level` を含む `SessionState` で `design_question_set` を実行する | `QuestionSetDesignError` が送出される。`error_code` は `llm_response_parse_failed`、`message` は `question set design llm response parse failed` と完全一致する。`__cause__` は元のスキーマ検証例外を保持する。LLM 呼び出しはちょうど1回で、自動再試行は行われない。構造化ログは `event="question_set_design_failed"` を持つログがちょうど1件出力される。追加キーは許容する | スキーマ分類責務は client 側、単一ログ出力責務は node 側であることを確認する |

# 網羅性チェック

仕様書の受け入れ基準の各項目に対応するテストケース ID を記載する。
全項目が少なくとも1つのテストケースでカバーされていることを確認する。

| 受け入れ基準 | 対応テストケース |
|---|---|
| `SessionState.roadmap_item_title` / `SessionState.roadmap_item_description` / `SessionState.roadmap_item_level` から確認ポイントリストが生成される | TC-01, TC-02, TC-20 |
| 各確認ポイントは `ConfirmationPoint` DTO（`id`, `content`, `format`）で返る | TC-01, TC-02, TC-11, TC-12 |
| 通常系では、確認ポイント数は 3〜5 個を目標に生成される | TC-10, TC-21 |
| コードで表現できるポイントには `format="knowledge_and_practice"` が設定される | TC-11 |
| `roadmap_item_level="middle"` または `roadmap_item_level="major"` のまとめテストでも、ノードが参照する入力は `SessionState.roadmap_item_title` / `SessionState.roadmap_item_description` / `SessionState.roadmap_item_level` のみである | TC-12 |

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
