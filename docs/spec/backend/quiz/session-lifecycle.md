---
feature: session-lifecycle
status: ready
reviewed_by:
approved_at:
---

## 機能概要

クイズセッションの開始・進行・再開・完了を管理する。LangGraphのインメモリステートとQuizSessionテーブルを連携させ、中断したセッションの再開を可能にする。

## 公開契約

### 開始要求 DTO

application層が新規セッション開始で受け取る公開入力は、以下の最小 DTO に固定する。

| フィールド | 型 | 説明 |
|---|---|---|
| `roadmap_item_id` | `str` | 開始対象の `RoadmapItem.id` |

### 再開要求 DTO

application層がセッション再開で受け取る公開入力は、以下の最小 DTO に固定する。

| フィールド | 型 | 説明 |
|---|---|---|
| `session_id` | `str` | 再開対象の `QuizSession.id` |

### C1 `session_init` の公開結果

- 新規開始では `QuizSession` を1件作成し、`RoadmapItem.id` / `level` / `title` / `description` を取得して、`SessionState` に `session_id`、`roadmap_item_id`、`roadmap_item_level`、`roadmap_item_title`、`roadmap_item_description`、`is_resumed=false` を設定する
- 再開では既存 `QuizSession.id` を `session_id` として使い、同じ `RoadmapItem` 情報を `SessionState` に設定したうえで `is_resumed=true` を設定する
- 再開時のみ、`QuizAnswer` 履歴を `QuizAnswer.question_number` 昇順で復元し、`SessionState.answers` に載せる
- C1 が責務を持たない `confirmation_points`、`current_point_index`、`current_question_text`、`current_answer_type`、`user_input`、`input_source`、`input_type`、`next_action`、`total_questions_asked` は未設定のまま許容する
- C1 の責務は `QuizSession` 作成、`RoadmapItem` 情報取得、再開時の `QuizAnswer` 履歴復元までに限定し、再開候補列挙、自動再開、`confirmation_points` 生成は含めない

## 振る舞い

### セッション開始

ユーザーがロードマップ項目を選択してセッションを開始する。

- QuizSessionレコードを作成（status: in_progress）
- LangGraphセッションを開始
- 問題セット設計ノードに進む

### セッション進行

LangGraphのループで問答を繰り返す。各回答はQuizAnswerに即座に記録される。

- 各回答はDBへの永続化完了後にのみ、次の出題または完了処理へ進める
- ここでいう永続化完了は、保存呼び出しの着手ではなく、後続読取から観測可能な commit 完了相当の状態を指す
- `QuizAnswer.answer_text` はユーザー入力文字列を raw のまま保存し、trim・空白正規化・Unicode 正規化・改行変換・大小文字変換を行わない
- 再開時に復元する `QuizAnswer.answer_text` と `SessionState.answers[].answer_text` も、保存済みの raw 値をそのまま使う

### セッション再開

in_progressのセッションを再開する（ADR-005参照）。

- QuizSessionに紐づくQuizAnswer履歴を `QuizAnswer.question_number` 昇順で取得する
- 履歴は、少なくとも `question_number`・`question_text`・`answer_text` を含む問答ペア列としてLLMに渡す
- 復元した問答ペア列を使って新しいLangGraphセッションとして続行する
- 「ここまでの問答を踏まえて、続きから出題して」と指示
- `QuizAnswer` が0件の場合は空の履歴をLLMに渡し、新規開始と同じ公開結果として問題セット設計ノードから続行する

中断の発生パターン:
- ユーザーが明示的に中断ボタンを押す
- ブラウザを閉じる等で操作が途絶える

いずれの場合もQuizSessionはin_progressのまま残り、再開可能。

### セッション完了

全確認ポイントの問答が終了したとき。

- 出題項目評価ノードで総合コメント + scoreを算出
- RoadmapItem.scoreを更新
- QuizSession.statusをcompletedに変更
- QuizSession.completed_atを記録
- 観測対象は最終 persisted `QuizSession.completed_at` が非 `NULL` であることまでとし、更新回数、単回記録、idempotency、監査ログ回数は本仕様に含めない

### 具体例

```
開始: ユーザーが「ジェネリクスの基本構文と型パラメータ」を選択
  → QuizSession作成（status: in_progress）
  → 問題セット設計 → 出題開始

中断: 3問回答した後、ブラウザを閉じる
  → QuizSession: in_progress のまま
  → QuizAnswer: 3件記録済み

再開: ユーザーがアプリを開き、in_progressのセッションを選択
  → QuizAnswer を question_number 昇順の問答ペア 3件としてLLMに渡す
  → 4問目から続行

完了: 全確認ポイント終了
  → 総合評価 → score更新 → status: completed
```

## 技術判断

- statusを in_progress / completed の2値とする理由: 中断もタイムアウトもin_progressとして扱い、再開可能にする。abandonedを別ステータスにする必要がない
- LangGraphのチェックポイント永続化を使わない理由: QuizAnswer履歴で代替可能。LangGraphへの依存を減らす（ADR-005参照）

## 境界条件

- 同一ロードマップ項目でin_progressのセッションが既にある開始要求 → 新規作成せず、`resume_required=true` と `resume_session_id=<既存QuizSession.id>` を返してそのセッションの再開を促す
- QuizAnswer 0件のセッションを再開 → 空履歴で再開し、公開結果は新規開始と同じ
- 長期間放置されたin_progressセッション → 再開可能。期限は設けない

## 異常系

- 開始要求は観測可能な範囲で原子的に扱う。`QuizSession` 作成失敗時はLangGraphを開始しない。LangGraph開始失敗時は、その要求で新規に作成しようとした `QuizSession` を残さない
- 再開要求の失敗時は、既存 `QuizSession.status` を `in_progress` のまま維持し、新規 `QuizSession` を作成せず、既存 `QuizAnswer` を変更しない
- application層は開始・再開失敗を `QuizSessionLifecycleError` として送出し、例外インスタンス上で `error_code: str` と `message: str` を直接参照できるようにし、依存先で発生した元例外を `__cause__` に保持する
- application層は開始・再開失敗時に自動再試行しない。ただし再開要求で interrupt 消化済み（前回一過性エラーによる中断後のリトライ）の場合は、checkpointer の状態から失敗ノードを自動再実行する
- 再開要求の問答進行中に LLM の一過性エラー（タイムアウト等）が発生した場合、`session_resume_transient_llm_error` を送出し、セッションを `in_progress` のまま維持する。フロントエンドは同じ入力で再試行可能（HTTP 503）
- 再試行時は LangGraph checkpointer に残っている状態から、失敗したノードを再実行する
- 失敗時は `structlog` の構造化ログを各失敗につきちょうど1件出力する

| error_code | 発生条件 | message | ログイベント | 必須ログキー |
|---|---|---|---|---|
| `session_start_persistence_failed` | `QuizSession` 作成に失敗した | `quiz session start persistence failed` | `quiz_session_start_failed` | `roadmap_item_id`, `error_code`, `error_type` |
| `session_start_graph_failed` | `QuizSession` 作成後の LangGraph 開始に失敗した | `quiz session start graph failed` | `quiz_session_start_failed` | `roadmap_item_id`, `error_code`, `error_type` |
| `session_resume_history_load_failed` | `QuizAnswer` 履歴取得に失敗した | `quiz session resume history load failed` | `quiz_session_resume_history_load_failed` | `session_id`, `roadmap_item_id`, `error_code`, `error_type` |
| `session_resume_llm_start_failed` | 問答履歴を使ったLLM続行開始に失敗した | `quiz session resume llm start failed` | `quiz_session_resume_llm_start_failed` | `session_id`, `roadmap_item_id`, `error_code`, `error_type` |
| `session_resume_transient_llm_error` | LLM の一過性エラー（タイムアウト等）で問答進行に失敗した。セッションは `in_progress` のまま再試行可能 | `quiz session resume transient llm error` | `quiz_session_resume_transient_llm_error` | `session_id`, `roadmap_item_id`, `error_type` |

## スコープ外

- 複数セッションの同時進行
- セッションの削除
- アプリ起動時の再開候補列挙・自動提示
- セッション履歴の一覧表示（参照系はanalytics側）

## 受け入れ基準

- [ ] ロードマップ項目を選択してセッションを開始できる
- [ ] 各回答が次の出題または完了処理より前にQuizAnswerへ永続化完了する
- [ ] in_progressのセッションを `QuizAnswer.question_number` 昇順の問答ペア履歴から再開できる
- [ ] 全確認ポイント完了時にstatusがcompletedに変わる
- [ ] 完了時にRoadmapItem.scoreが更新される
- [ ] 同一項目でin_progressのセッションがあれば再開を促す

## モジュール構成

- 構成方針: 2ファイル構成（types + logic）
- モジュール一覧:
  - `backend/quiz/application/session_lifecycle_types.py`
    - `StartSessionInput` — frozen dataclass (`roadmap_item_id: str`)
    - `ResumeSessionInput` — frozen dataclass (`session_id: str`)
    - `StartSessionResult` — frozen dataclass (`session_id: str`, `resume_required: bool`, `resume_session_id: str | None`)。`resume_required=True` 時は新規作成せず `resume_session_id` を返す
    - `QuizSessionLifecycleError(Exception)` — `error_code: str`, `message: str` を属性として持ち、`__cause__` に元例外を保持
    - `QuizSessionRecord` — Protocol が返すセッションレコード。`id: str`, `roadmap_item_id: str`, `status: str`, `completed_at: str | None`
    - `QuizAnswerHistoryRecord` — Protocol が返す回答履歴レコード。`question_number: int`, `question_text: str`, `answer_text: str`, `answer_type: str`, `score: int`, `feedback: str`, `confirmation_point_id: str`
    - `RoadmapItemRecord` — Protocol が返すロードマップ項目レコード。`id: str`, `level: str`, `title: str`, `description: str`
    - `QuizSessionStore(Protocol)` — `create_session(roadmap_item_id: str) -> QuizSessionRecord`, `find_in_progress_by_item(roadmap_item_id: str) -> QuizSessionRecord | None`, `find_session(session_id: str) -> QuizSessionRecord`, `mark_completed(session_id: str, completed_at: str) -> None`, `delete_session(session_id: str) -> None`（開始失敗時のロールバック用）
    - `QuizAnswerStore(Protocol)` — `save_answer(quiz_session_id: str, answer: QuizAnswerHistoryRecord) -> None`, `find_by_session(session_id: str) -> list[QuizAnswerHistoryRecord]`（question_number 昇順）
    - `RoadmapItemReader(Protocol)` — `find_item(item_id: str) -> RoadmapItemRecord`, `update_score(item_id: str, score: int) -> None`
    - `GraphRunner(Protocol)` — `start_graph(state: SessionState) -> None`（LangGraph グラフを開始し、問題セット設計ノードへ遷移させる）, `resume_graph(state: SessionState) -> None`（再開時に LLM へ履歴を渡してグラフを続行する。「ここまでの問答を踏まえて、続きから出題して」と指示）
  - `backend/quiz/application/session_lifecycle.py`
    - `start_session(input: StartSessionInput, *, session_store: QuizSessionStore, item_reader: RoadmapItemReader, graph_runner: GraphRunner) -> StartSessionResult` — 新規開始。in_progress 既存時は `resume_required=True` を返しグラフは開始しない。新規時は QuizSession 作成 → RoadmapItem 取得 → SessionState 構築 → graph_runner.start_graph 呼び出し。QuizSession 作成後にグラフ開始が失敗した場合は delete_session でロールバック
    - `resume_session(input: ResumeSessionInput, *, session_store: QuizSessionStore, answer_store: QuizAnswerStore, item_reader: RoadmapItemReader, graph_runner: GraphRunner) -> SessionState` — 再開。QuizAnswer 履歴を question_number 昇順で復元 → SessionState 構築 → graph_runner.resume_graph 呼び出し
    - `record_answer(session_id: str, answer: QuizAnswerHistoryRecord, *, answer_store: QuizAnswerStore) -> None` — 回答を QuizAnswer に永続化。後続処理（次の出題/完了）より前に呼び出される
    - `complete_session(session_id: str, score: int, *, session_store: QuizSessionStore, item_reader: RoadmapItemReader) -> None` — 完了処理。status 更新 + completed_at 記録 + score 反映
