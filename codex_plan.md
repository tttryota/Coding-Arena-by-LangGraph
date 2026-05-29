# codex_plan.md

## Summary

このブロックを `codex_plan.md` の最終内容として固定する。  
既存の `major/middle/detail` 3階層は維持し、`detail` を「1つの座学導入 + 段階的コーディング演習ユニット」に再定義する。  
実装方針は以下で固定する。

- ロードマップ生成は知識列挙ではなく、各 `detail` が 1 セッションで扱える実装テーマになるように LLM プロンプトを変更する
- クイズは `lecture -> practice -> summary` の3段階に分離し、採点対象は `practice` のコード回答のみとする
- 座学フェーズではユーザー入力は質問だけを受け付け、回答評価は行わない
- 実践フェーズでは全問 `answer_type="code"` 固定とし、難易度は `rewrite -> fill_blank -> bug_fix -> extend -> implement` の順でのみ進行させる
- 競プロ一問クイズはロードマップ本編と完全分離した独立機能として追加し、100件超のプリセットテーマからランダム選択して LLM が問題生成する

## Key Changes

### 1. Roadmap generation の意味変更

- `backend/roadmap/infrastructure/codex_roadmap_generation_llm.py` のプロンプトを以下へ変更する
- `major` は学習段階、`middle` は実装カテゴリ、`detail` は1回の演習ユニットとする
- 各 `detail` は 1 つの実装目標だけを持つ
- 各 `detail.description` は「何を実装できるようになるか」を書く
- 各 `detail` は初歩の書き換え問題から最終的な自力実装まで 5 段階の練習に分解可能でなければならない
- DB スキーマは変更しない。`title` / `description` の意味だけを変更する

### 2. Quiz session の段階分離

- `SessionState` に `session_stage: Literal["lecture", "practice", "summary"]` を追加する
- `session_init` 完了時点では `session_stage="lecture"` を必須で設定する
- `question_set_design` は次を返す形に固定する
- `topic_overview: str` は座学本文として使う
- `confirmation_points: list[ConfirmationPoint]` は practice 用だけを生成する
- `current_point_index=0` は維持する
- `current_question_text` は lecture 中には生成しない
- `ConfirmationPoint` は次の shape に変更する
- `id: str`
- `content: str`
- `format: Literal["rewrite", "fill_blank", "bug_fix", "extend", "implement"]`
- practice セッションでは `current_answer_type` は常に `"code"` 固定とする
- `question_delivery` は `format` ごとに出題テンプレートを固定する
- `rewrite`: 例示済みコードの軽微な書き換え
- `fill_blank`: 部分穴埋め
- `bug_fix`: 壊れた実装の修正
- `extend`: 既存実装への要件追加
- `implement`: シグネチャと入出力例だけを与える自力実装
- `answer_evaluation` はコード回答専用評価に変更する
- deepdive は必ず現在ポイント以下の難度に落とす
- deepdive で `knowledge` 系の追加入力は生成しない
- `progress_update` は `answers` のうち practice のコード回答だけを集計対象にする
- lecture 中の chat は `answers` に保存しない

### 3. Lecture UI / API フロー

- セッション開始直後の状態は lecture 画面のみ表示する
- lecture 画面では `topic_overview`、practice の予定ステップ一覧、質問チャット、`演習を始める` ボタンだけを表示する
- lecture 中は回答フォームを表示しない
- practice 開始は新設 endpoint `POST /sessions/{session_id}/practice/start` でのみ行う
- `POST /sessions/{session_id}/input` は以下に固定する
- `session_stage="lecture"` の場合: `input_source="chat"` のみ許可し、質問応答だけ返す
- `session_stage="practice"` の場合: `input_source="form"` はコード回答、`input_source="chat"` は質問または解説依頼だけを扱う
- practice 中の chat で `answer` 判定はさせない。採点対象入力は form のコードだけに限定する
- frontend は `quiz-session-page.tsx` と `learning-phase.tsx` を中心に更新し、lecture と practice を明確に分離する

## Public APIs / Types

- `frontend/src/types/api.ts` と backend DTO を以下に合わせて変更する
- `SessionState.session_stage` を追加する
- `ConfirmationPoint.format` は `"knowledge" | "knowledge_and_practice"` を廃止し、`"rewrite" | "fill_blank" | "bug_fix" | "extend" | "implement"` に置換する
- `POST /sessions/{session_id}/practice/start` を追加する
- 競プロ機能として以下を追加する
- `GET /algorithm-quiz/themes` : プリセットテーマ一覧取得
- `POST /algorithm-quiz/sessions` : テーマ未指定時はランダム選択し、1問生成してセッション作成
- `POST /algorithm-quiz/sessions/{session_id}/answer` : コード回答を採点して完了

## Competitive Programming Quiz

- プリセットテーマは DB ではなく repo 管理の静的ファイルに固定する
- 保存先は `backend/quiz/infrastructure/algorithm_quiz_themes.json`
- 件数は 120 件以上、重複禁止、各要素は `{id, category, label}` の3フィールドだけに固定する
- 競プロクイズ用に SQLite へ以下の新規テーブルを追加する
- `algorithm_quiz_sessions`: `id`, `theme_id`, `theme_label`, `question_text`, `reference_solution`, `grading_rubric_json`, `status`, `created_at`, `completed_at`
- `algorithm_quiz_answers`: `id`, `session_id`, `answer_text`, `score`, `feedback`, `explanation`, `created_at`
- 問題生成時に LLM は `question_text`, `reference_solution`, `grading_rubric_json` を同時生成し、採点時は必ず保存済み rubric を使う
- UI は新規独立ページ `/algorithm-quiz` とし、ロードマップ・通常セッションとは状態共有しない
- 採点結果は roadmap の `score` や `last_quiz_at` を更新しない

## Test Plan

- roadmap generation: `detail` が実装ユニットとして扱われる前提で、既存3階層契約を壊さないことを確認する
- question set design: lecture 本文生成と practice step 5段階生成、`format` の順序制約を確認する
- session lifecycle: 開始直後が `session_stage="lecture"`、practice start endpoint 呼び出し後にのみ最初のコード問題が出ることを確認する
- question delivery: 全 `format` で `answer_type="code"` 固定、テンプレートが段階に応じて切り替わることを確認する
- answer evaluation: deepdive が難度を上げず、knowledge 問題を混入させないことを確認する
- progress update: lecture chat を無視し、practice 回答だけで score 更新することを確認する
- frontend: lecture 中に回答フォームが出ないこと、practice 開始後にコードエディタだけ出ること、既存 resume 導線が壊れないことを確認する
- algorithm quiz: テーマファイルが 120 件以上で一意、ランダム選択、問題生成保存、回答採点、完了遷移を確認する

## Assumptions / Defaults

- このターンでは Plan Mode のため `codex_plan.md` はまだ書き込まない。実行フェーズではこの内容をそのまま `codex_plan.md` に保存する
- 既存の `Roadmap`, `RoadmapItem`, `QuizSession`, `QuizAnswer` の列定義は変更しない
- 通常学習セッションの採点対象は code のみとし、knowledge 問題は完全廃止する
- 競プロクイズは v1 では RAG 非依存、ロードマップ非連動、履歴分析非対応とする
