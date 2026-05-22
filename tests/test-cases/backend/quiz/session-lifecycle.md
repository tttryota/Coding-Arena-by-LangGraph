---
status: ready
---

# テストケース一覧

# 検証焦点

| テストの種類 | 検証焦点 |
|---|---|
| Phase 1（最小骨格） | セッション開始、後続処理前の回答永続化、完了時の状態更新と score 反映 |
| Phase 2（コアロジック） | `in_progress` セッションの再開、履歴引き継ぎ、同一項目の重複開始防止 |
| Phase 3（エッジケース） | 中断方法差異、回答0件再開、長期放置セッション再開 |
| Phase 4（外部連携） | DB/LLM 連携の非エラー確認、外部障害時の例外契約確認 |

## Phase 1: 最小骨格

| ID | 観点 | 前提 | 入力 | 期待結果 | 備考 |
|---|---|---|---|---|---|
| TC-01 | 新規セッション開始で `QuizSession` 作成と LangGraph 開始結果が観測できる | 対象 `roadmap_item_id` に対して `status=in_progress` の `QuizSession` が0件存在する | ユーザーがロードマップ項目を選択して開始する | `QuizSession` がちょうど1件新規作成され、`roadmap_item_id` が入力と完全一致し、`status` は `in_progress`、`completed_at` は未設定である。開始結果は問題セット設計ノードへの遷移として観測できる | 受け入れ基準「開始できる」に対応。内部呼び出し回数は固定しない |
| TC-02 | 各回答が後続処理前に `QuizAnswer` へ永続化完了する | `status=in_progress` のセッションが存在し、1問目が出題済みである | ユーザーが1件の回答を送信する | `QuizAnswer` がちょうど1件追加され、`quiz_session_id` は対象セッションと完全一致し、回答内容は入力と完全一致する。次の出題または完了処理に進んだ時点では、その回答が後続読取から観測可能な永続化完了状態になっている | 「即座に」は保存着手ではなく永続化完了で検証する |
| TC-03 | 全確認ポイント完了でセッション完了処理が行われる | `status=in_progress` のセッションが存在し、残り確認ポイントが最後の1件である | ユーザーが最後の回答を送信し、出題項目評価ノードが総合コメントと `score` を返す | `QuizSession.status` が `completed` に更新される。`QuizSession.completed_at` が1回だけ記録されて非NULLになる。`RoadmapItem.score` が評価ノードの `score` と完全一致する値へ更新される | 総合コメントの保存先は仕様未記載のため検証対象外 |

## Phase 2: コアロジック

| ID | 観点 | 前提 | 入力 | 期待結果 | 備考 |
|---|---|---|---|---|---|
| TC-10 | `QuizAnswer` 履歴を使って `in_progress` セッションを順序付き問答ペアとして再開できる | `status=in_progress` の `QuizSession` が1件存在し、同セッションに紐づく `QuizAnswer` が `question_number=1,2,3` の3件保存済みである | ユーザーが当該セッションの再開を実行する | 対象 `QuizSession` に紐づく `QuizAnswer` 履歴が3件取得される。LLM 入力には `question_number` 昇順の問答ペア列が含まれ、各要素の `question_number`・`question_text`・`answer_text` は保存済み `QuizAnswer` と完全一致する。LLM への指示文に「ここまでの問答を踏まえて、続きから出題して」が含まれる。新規 `QuizSession` は1件も作成されず、4問目相当の続きから進行する | 受け入れ基準「履歴から再開」に対応 |
| TC-11 | 同一ロードマップ項目に既存 `in_progress` がある場合は新規作成せず再開対象を返す | 対象 `roadmap_item_id` に対して `status=in_progress` の `QuizSession` が1件存在する | ユーザーが同じロードマップ項目を選択して開始しようとする | 新しい `QuizSession` は0件作成される。開始要求の結果には `resume_required=true` が含まれ、`resume_session_id` は既存 `QuizSession.id` と完全一致する単一値で返る | UI文言は固定せず、application 層の最小返却契約のみ検証する |
| TC-12 | `QuizAnswer` 0件の `in_progress` セッション再開は空履歴で実質新規開始と同じである | `status=in_progress` の `QuizSession` が1件存在し、同セッションに紐づく `QuizAnswer` が0件である | ユーザーが当該セッションの再開を実行する | 再開処理は非エラーで完了する。LLM 入力に渡される問答履歴は空である。開始結果は新規開始時と同じ「問題セット設計」ノードへの遷移として観測できる。新規 `QuizSession` は0件である | 境界条件「0件再開」に対応 |

## Phase 3: エッジケース

| ID | 観点 | 前提 | 入力 | 期待結果 | 備考 |
|---|---|---|---|---|---|
| TC-20 | 明示的中断でも `QuizSession` は `in_progress` のまま残る | `status=in_progress` のセッションが存在し、`QuizAnswer` が2件保存済みである | ユーザーが中断ボタンを押す | 対象 `QuizSession.status` は `in_progress` のままで変更されない。既存 `QuizAnswer` 2件はそのまま保持され、件数はちょうど2件である。`completed_at` は未設定のままで、後続の再開操作対象として参照可能である | 中断を別ステータスにしない判断を確認する |
| TC-21 | ブラウザ離脱による中断でも明示的な再開要求で続行できる | `status=in_progress` のセッションが存在し、`QuizAnswer` が `question_number=1,2,3` の3件保存済みである | 3問回答後にブラウザを閉じ、後でアプリを開き直して同じ `QuizSession.id` を指定した再開要求を実行する | ブラウザ離脱時点で `QuizSession.status` は `in_progress` のままである。`QuizAnswer` 3件が保持されている。明示的な再開要求は非エラーで完了し、`question_number` 昇順の問答ペア履歴を使って4問目相当から続行できる | アプリ起動時の候補列挙はスコープ外とする |
| TC-22 | 長期間放置された `in_progress` セッションも期限なく再開できる | 更新日時が長期間前の `status=in_progress` セッションが存在し、`QuizAnswer` が1件以上保存済みである | ユーザーが当該セッションの再開を実行する | 期限切れによる拒否は発生しない。再開処理は非エラーで完了し、保存済み `QuizAnswer` 履歴が少なくとも1件取得されて続行に使用される | 期限を設けない仕様を検証する |

## Phase 4: 外部連携

| ID | 観点 | 前提 | 入力 | 期待結果 | 備考 |
|---|---|---|---|---|---|
| TC-30 | 再開時にDB履歴取得と LLM 続行指示が連携し、順序付き問答ペアで非エラー進行する | `status=in_progress` のセッションが存在し、`QuizAnswer` が `question_number` 付きで複数件保存済みである | ユーザーが再開を実行する | `QuizAnswer` のDB取得は成功し、取得件数は保存済み件数と完全一致する。取得履歴は `question_number` 昇順の問答ペア列として LLM 入力に含まれ、LangGraph は非エラーで次の出題へ進む | 外部連携の正常経路確認。内部呼び出し回数は固定しない |
| TC-31 | セッション開始時の永続化失敗または LangGraph 開始失敗で原子性と例外契約が守られる | `QuizSession` 作成処理、または LangGraph 開始処理のどちらかが外部要因で失敗するようにする | ユーザーがロードマップ項目を選択して開始する | application 層は `QuizSessionLifecycleError` を送出し、`error_code` は `QuizSession` 作成失敗なら `session_start_persistence_failed`、LangGraph 開始失敗なら `session_start_graph_failed` である。`message` はそれぞれ `quiz session start persistence failed` または `quiz session start graph failed` と完全一致し、`__cause__` は元の依存先例外を保持する。自動再試行は行われない。構造化ログは `quiz_session_start_failed` がちょうど1件出力され、`roadmap_item_id`・`error_code`・`error_type` を必須キーとして含む。LangGraph は `QuizSession` 作成失敗時に開始されず、いずれの失敗でもその要求で新規に作成しようとした `QuizSession` は残らない | 異常系。開始要求の原子性を検証する |
| TC-32 | 再開時の履歴取得失敗または LLM 続行開始失敗で状態不変と例外契約が守られる | `QuizAnswer` 履歴取得、または LLM 続行開始のどちらかが外部要因で失敗するようにする | ユーザーが `in_progress` セッションの再開を実行する | application 層は `QuizSessionLifecycleError` を送出し、`error_code` は履歴取得失敗なら `session_resume_history_load_failed`、LLM 続行開始失敗なら `session_resume_llm_start_failed` である。`message` はそれぞれ `quiz session resume history load failed` または `quiz session resume llm start failed` と完全一致し、`__cause__` は元の依存先例外を保持する。自動再試行は行われない。構造化ログは履歴取得失敗なら `quiz_session_resume_history_load_failed`、LLM 続行開始失敗なら `quiz_session_resume_llm_start_failed` がちょうど1件出力され、いずれも `session_id`・`roadmap_item_id`・`error_code`・`error_type` を必須キーとして含む。既存 `QuizSession.status` は `in_progress` のまま維持され、新規 `QuizSession` は0件、既存 `QuizAnswer` は件数・内容ともに不変である | 異常系。再開失敗時の状態不変条件を検証する |

# 網羅性チェック

仕様書の受け入れ基準の各項目に対応するテストケース ID を記載する。
全項目が少なくとも1つのテストケースでカバーされていることを確認する。

| 受け入れ基準 | 対応テストケース |
|---|---|
| ロードマップ項目を選択してセッションを開始できる | TC-01 |
| 各回答が次の出題または完了処理より前にQuizAnswerへ永続化完了する | TC-02 |
| in_progressのセッションを `QuizAnswer.question_number` 昇順の問答ペア履歴から再開できる | TC-10, TC-30 |
| 全確認ポイント完了時にstatusがcompletedに変わる | TC-03 |
| 完了時にRoadmapItem.scoreが更新される | TC-03 |
| 同一項目でin_progressのセッションがあれば再開を促す | TC-11 |

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
