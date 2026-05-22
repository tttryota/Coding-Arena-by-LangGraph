---
feature: quiz-overview
status: draft
reviewed_by:
approved_at:
---

## グループの責務

ロードマップの項目に基づくクイズセッションの実行を担う。出題・回答評価・深掘り・解説・前提知識の遡りといった対話的な学習体験をLangGraphワークフローとして実現し、結果をロードマップの進捗に反映する。

`quiz/` パッケージに属する学習支援固有のドメイン。LangGraphは本グループの内部実装である。

## 含まれる機能

| # | 機能 | 概要 |
|---|------|------|
| C1 | セッション開始 | 出題範囲（ロードマップ項目）を受けてセッションを生成 |
| C2 | 問題セット設計 | LLMが出題範囲に基づき問題セットを設計、予定問題数（理論値）を算出 |
| C3 | 出題 | 問題をユーザーに提示 |
| C4 | 回答評価 | ユーザーの回答（文章/コード）をLLMが評価し理解度を判定 |
| C5 | 深掘り判断 | 回答に応じて深掘り/次の問題/前提知識遡りをLLMが判断 |
| C6 | 解説生成 | ユーザーの依頼に応じてLLMが解説を生成（RAGでノート参照） |
| C7 | セッション終了・サマリー | セッション終了時にサマリー生成 |
| C8 | 進捗反映 | クイズ結果をロードマップの具体項目の進捗に反映 |
| C9 | まとめテスト結果記録 | 中枠・大枠テストの正答率等をDBに保存 |

## 処理フロー

### クイズセッションフロー

```
C1: セッション開始（出題範囲を選択）
  │
  ▼
C2: 問題セット設計（予定問題数を算出）
  │
  ▼
C3: 出題
  │
  ▼
ユーザーが回答（文章 or コード）
  │
  ▼
C4: 回答評価（理解度を判定）
  │
  ▼
C5: 深掘り判断
  ├── 次の問題 → C3 に戻る
  ├── 深掘り → 追加問題を生成 → C3 に戻る（予定問題数増減）
  ├── 前提知識遡り → 前提項目の問題を生成 → C3 に戻る（最大2段）
  └── 問題セット完了 → C7 へ
  │
  （セッション中いつでも）
  ├── ユーザーが解説依頼 → C6: 解説生成
  └── ユーザーが深掘り依頼 → C5 の深掘りと同様
  │
  ▼
C7: セッション終了・サマリー生成
  │
  ▼
C8: 進捗反映（具体項目の理解度を更新）
  │
  ▼
C9: まとめテスト結果記録（中枠・大枠の場合のみ）
```

### 出題範囲の粒度

| 粒度 | 位置づけ | 進捗への影響 |
|------|---------|-------------|
| 具体項目 | メイン。しっかり理解度チェック | 進捗管理の単位（insufficient / partial / sufficient） |
| 中枠 | まとめテスト。配下の具体を横断、問題は絞り気味 | 結果記録のみ（正答率等）、具体項目の進捗には影響しない |
| 大枠 | まとめテスト。全体の理解を問う、さらに絞り気味 | 同上 |

大枠選択時は中枠の絞り込みを促す。

### 回答形式

- 文章（概念の理解確認）
- コード（実装力の確認）

### セッション中の機能

- わからなければLLMに解説を依頼できる（C6、RAGでユーザーのノートを参照して説明）
- AI自動の深掘り / ユーザー起点の深掘り
- 前提知識の遡り確認（最大2段）

## LangGraph グラフ構造

### ノード一覧

| ノード名 | 対応機能 | 責務 |
|---|---|---|
| session_init | C1 | 開始要求では `roadmap_item_id`、再開要求では `session_id` を受ける。QuizSession作成または再開判定を行い、`RoadmapItem.id` / `level` / `title` / `description` を取得して `session_id`、`roadmap_item_*`、`is_resumed` をステートへ設定する。再開時のみ `QuizAnswer` 履歴を `answers` に復元し、C1 責務外の state は未設定のまま許容する。開始/再開失敗時は `session-lifecycle.md` の異常系契約に従う |
| question_set_design | C2 | 確認ポイントリストを設計 |
| question_delivery | C3 | 確認ポイントから問題文を動的生成 |
| input_classification | — | ユーザー入力を answer / question / explanation_request に分類 |
| chat_response | — | 出題内容への質問にLLMが回答（問答進行に影響しない） |
| answer_evaluation | C4+C5 | 回答評価 + ルーティング判断（next/deepdive/complete） |
| explanation_generation | C6 | RAGでノート参照 + 解説生成 |
| progress_update | C7+C8 | 全問答から総合score算出、RoadmapItem更新、セッション完了 |
| summary_test_record | C9 | まとめテストのLLM定性分析を保存 |

### エッジ定義

```
session_init → question_set_design → question_delivery → __interrupt__

__interrupt__（ユーザー入力待ち）→ input_routing（conditional: input_source）
  ├── "form"  → answer_evaluation（回答フォームからの送信は input_classification を経由せず回答として評価し、C4 完了時までに input_type="answer" を確定）
  └── "chat"  → input_classification

input_classification →（conditional: input_type）
  ├── "answer"               → answer_evaluation
  ├── "question"             → chat_response → __interrupt__
  └── "explanation_request"  → explanation_generation → question_delivery → __interrupt__

answer_evaluation →（conditional: next_action）
  ├── "next"      → question_delivery → __interrupt__
  ├── "deepdive"  → question_delivery → __interrupt__（confirmation_points を末尾追記し、current_point_index を次の未消化位置へ更新後）
  └── "complete"  → progress_update

progress_update →（conditional: roadmap_item_level）
  ├── "middle" / "major"  → summary_test_record → END
  └── "detail"            → END
```

### C1 `session_init` の状態初期化

- 開始入力は `roadmap_item_id`、再開入力は `session_id` の最小 DTO とする
- C1 は `RoadmapItem.id`、`RoadmapItem.level`、`RoadmapItem.title`、`RoadmapItem.description` を取得し、`SessionState` の `session_id`、`roadmap_item_id`、`roadmap_item_level`、`roadmap_item_title`、`roadmap_item_description`、`is_resumed` を初回設定する
- 再開時のみ、`QuizAnswer` 履歴を `QuizAnswer.question_number` 昇順で `SessionState.answers` に復元する
- 開始時の C1 では `answers` の初期化を必須にせず、C1 が責務を持たない state は未設定のまま許容する
- C1 のスコープには `confirmation_points` 生成、再開候補列挙、自動再開、複数セッション同時進行制御を含めない

### 入力分類ノードの振る舞い

ユーザー入力を3種類に分類し、後続ノードを決定する。

| 分類 | 判定基準 | 後続 |
|---|---|---|
| answer | 出題に対する回答と判断できる | answer_evaluation |
| question | 出題内容の意味や前提についての質問 | chat_response（問答進行に影響なし） |
| explanation_request | 「わからない」「解説して」等、解説を求める意思表示 | explanation_generation |

分類はLLMが `current_question_text` と `user_input` のコンテキストから判断する。曖昧な場合は answer として扱う（ユーザーが意図的に解説を求めない限り問答を進める）。

`input_classification` は `input_source="chat"` のときだけ実行される。`input_source="form"` は回答専用経路のため入力分類を経由せず `answer_evaluation` に直行し、その時点では `input_type` 未設定を許容する。ただし `answer_evaluation` の完了時には `input_type="answer"` を共有ステートへ保持し、`next_action` や `answers` を読む downstream は評価完了後の状態であれば `input_type` 必須前提で参照できる。この条件付き組み合わせは workflow 契約であり、`SessionState` TypedDict 自体は phase別 TypedDict / Union / runtime validator を提供しない。

### conditional edge の判断基準

**answer_evaluation → next_action:**
- `next`: 理解度が十分。回答済みの確認ポイントを消化し、`current_point_index` を 1 進めて次の未消化確認ポイントへ移る
- `deepdive`: 理解が浅い部分がある。深掘り確認ポイントを `confirmation_points` の末尾へ追記しつつ、`current_point_index` は回答済みポイントを消化した次位置へ 1 進める。したがって既存の未消化確認ポイントが残っていればそれを先に出題し、末尾まで到達した時点で追記済み deepdive ポイントを出題する
- `complete`: 全確認ポイント完了、または20問到達で収束。`current_point_index == len(confirmation_points)` を完了境界とする

**20問収束ルール:** `total_questions_asked == 20` に到達した評価完了状態では、`answer_evaluation` は `deepdive` を選択せず `next` または `complete` に収束させる。このとき deepdive 用 `confirmation_points` 追記を有効状態として扱わない。これは `answer_evaluation` と downstream ノードの workflow 契約であり、`SessionState` TypedDict 自体の runtime enforcement はスコープ外とする。

## SessionState（LangGraph ステート定義）

LangGraphワークフローの全ノードが共有するインメモリステート。`backend/quiz/domain/session_state.py` に TypedDict として実装する。
DBエンティティ（QuizSession, QuizAnswer）への永続化はインフラ層の責務であり、SessionStateはグラフ実行中の状態のみを表す。
deliverable は single partial TypedDict の `SessionState` と、complete record の `ConfirmationPoint` / `QuizAnswerRecord` のみとし、条件付き状態組み合わせは workflow 契約として別途運用する。

### フィールド一覧

| フィールド | 型 | 初期設定 | 説明 |
|---|---|---|---|
| session_id | str | C1 | QuizSession.id |
| roadmap_item_id | str | C1 | 出題対象のRoadmapItem.id |
| roadmap_item_level | "detail" / "middle" / "major" | C1 | 出題粒度。まとめテスト判定に使用 |
| roadmap_item_title | str | C1 | LLMコンテキスト用 |
| roadmap_item_description | str | C1 | LLMコンテキスト用 |
| is_resumed | bool | C1 | 再開セッションか（ADR-005） |
| confirmation_points | list[ConfirmationPoint] | C2 | 確認ポイントリスト。深掘り時にC4が追加 |
| current_point_index | int | C2 | 次に出題する未消化確認ポイントのインデックス。C4 は現在問を消化した次位置へ更新する |
| current_question_text | str | C3 | 出題中の問題文 |
| current_answer_type | "textarea" / "code" | C3 | 回答形式 |
| user_input | str | 外部 | ユーザーの最新入力テキスト |
| input_source | "form" / "chat" | 外部 | 入力元。formは常にanswer扱い、chatは入力分類ノードへ |
| input_type | "answer" / "question" / "explanation_request" | 入力分類 / C4 | ユーザー入力の分類結果。chat は入力分類ノード、form は C4 完了時に `"answer"` を保持 |
| next_action | "next" / "deepdive" / "complete" | C4 | 評価後のルーティング判断 |
| answers | list[QuizAnswerRecord] | C1（再開時） / C4 | 再開時は保存済み `QuizAnswer` 履歴を復元し、以後は C4 が追記のみ行う |
| total_questions_asked | int | C3 | 出題総数（20問で収束） |

### ConfirmationPoint

| フィールド | 型 | 説明 |
|---|---|---|
| id | str | 確認ポイントの識別子 |
| content | str | 確認すべき内容 |
| format | "knowledge" / "knowledge_and_practice" | 出題形式（知識のみ / 知識+実践） |

### QuizAnswerRecord

SessionState内の問答記録。QuizAnswerテーブルへの永続化はインフラ層が担う。

| フィールド | 型 | 説明 |
|---|---|---|
| question_number | int | セッション内の問題番号 |
| confirmation_point_id | str | 対応する確認ポイントのid |
| question_text | str | 出題内容 |
| answer_type | "textarea" / "code" | 回答形式 |
| answer_text | str | ユーザーの回答。保存・復元では raw 値をそのまま使い、trim・空白正規化・Unicode 正規化・改行変換・大小文字変換を行わない |
| score | int | 0〜100（LLM評価の出力。ADR-004） |
| feedback | str | LLMからのフィードバック |

### ノードごとのステート操作

| ノード | 読み取り | 書き込み |
|---|---|---|
| C1 セッション開始 | 開始時: `roadmap_item_id` / 再開時: `session_id` | `session_id`, `roadmap_item_*`, `is_resumed`, `answers`（再開時のみ履歴復元） |
| C2 問題セット設計 | roadmap_item_*, is_resumed | confirmation_points, current_point_index |
| C3 出題 | confirmation_points, current_point_index, answers | current_question_text, current_answer_type, total_questions_asked |
| 入力分類 | user_input | input_type |
| C4 回答評価 | current_question_text, user_input, input_source, input_type, answers, total_questions_asked | input_type（form 経路では `"answer"` を補完）, next_action, answers（追記）, confirmation_points（深掘り時は末尾追記）, current_point_index |
| C6 解説生成 | current_question_text, answers | （ステート変更なし。レスポンスのみ返却） |
| C7/C8 完了・進捗反映 | answers, roadmap_item_id | （DB書き込み。ステート変更なし） |
| C9 まとめテスト記録 | answers, roadmap_item_level | （DB書き込み。ステート変更なし） |

## 外部依存

### このグループが利用するもの

| 依存先 | インターフェース | 用途 |
|--------|----------------|------|
| `core/llm/` | LLMクライアント | 出題・評価・深掘り判断・解説・サマリー生成 |
| `core/rag/` | RAG検索 | 解説時にユーザーのノートから関連チャンクを取得 |
| `roadmap/` | ロードマップ取得・進捗反映 | 出題範囲の参照、結果の進捗書き込み |
| `infrastructure/rdb/` | SQLite操作 | セッション結果・まとめテスト結果の永続化 |

### このグループを利用するもの

| 利用元 | 用途 |
|--------|------|
| `domain/analytics/` | クイズ結果を元にした弱点分析・反復リマインド |
| `roadmap/` | セッション終了時の改善提案生成 |

## 具体仕様書の一覧

| ファイル | 対象機能 |
|---------|---------|
| `session-lifecycle.md` | セッション開始・再開・完了の管理 |
| `question-set-design.md` | 確認ポイントリストの設計（知識+実践のセット出題） |
| `question-delivery.md` | 文脈を踏まえた問題文の都度生成 |
| `answer-evaluation.md` | 回答評価 + ルーティング統合（判定→アクション→score→feedback） |
| `explanation-generation.md` | RAGでノート参照 + 解説生成 + 別角度で再出題 |
| `progress-update.md` | 全問答から総合コメント→score算出、RoadmapItem更新 |
| `summary-test-record.md` | まとめテストのLLM定性分析を保存 |
| `summary-test-results.md` | まとめテスト結果の取得API（analyticsから移管） |

※ 以下は議論の結果、統合・整理:
- deepdive-routing → answer-evaluationに統合（scoreは判断の出力であり入力ではない。ADR-004）
- session-summary → progress-updateに包含（セッション完了時の処理として一体）
