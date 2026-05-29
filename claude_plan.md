# コーディング練習主軸システムへの改修計画

## Context

現状のシステムは「知識の習得」に重きを置いた学習ロードマップ＋クイズセッションだが、これを**コーディング練習に主軸**を置くシステムに変更したい。加えて、**競プロアルゴリズム一問クイズ**という新セクションも追加する。

### 要望の要約
1. **セッションフロー変更**: 座学（概念説明）→ ユーザーは質問のみ → 座学後はコーディング問題のみ
2. **難易度の段階性**: 例示→書き換え程度の初歩から、ステップバイステップで難しくなる
3. **競プロクイズ**: テーマ100+プリセット → ランダムピック → LLM出題 → 一問完結

---

## 変更の全体像

### A. ロードマップ生成の変更（小規模）
### B. クイズセッションのフロー再設計（大規模 — 新グラフ）
### C. 競プロアルゴリズムクイズの新設（中規模 — 新機能）

---

## A. ロードマップ生成：知識→コーディングスキル指向

**対象ファイル**: `backend/roadmap/infrastructure/codex_roadmap_generation_llm.py`

### 変更内容
- システムプロンプトを「学習ロードマップ」から「コーディング実践ロードマップ」に変更
- `major` は学習段階、`middle` は実装カテゴリ、`detail` は1回の演習ユニットとする
- detail の description を「理解する」ではなく「何を実装できるようになるか」形式に指示
- 各 detail は初歩の書き換えから自力実装まで5段階の練習に分解可能であることを制約に含める
- 基礎/応用の2 major構造はそのまま維持

### プロンプト変更方針
```
現行: "学習ロードマップ設計AI" / "学習目標に絞ること"
変更: "コーディング実践ロードマップ設計AI" / "1つの実装目標に絞ること。何を実装できるようになるかを書くこと"
```

DBスキーマ（`RoadmapItem`）は変更不要。`title` / `description` の意味だけを変更する。

---

## B. クイズセッション：座学→コーディング問題フロー

### B1. 新しいセッションフロー

```
lecture_generation (LLMが概念を解説生成)
  │
  ▼
await_lecture_input ◄── interrupt (ユーザーが座学を読む)
  │
  ├─ ユーザーが質問(chat) → lecture_chat_response → await_lecture_input (ループ)
  ├─ practice_start endpoint → coding_problem_set_design
  │
  ▼
coding_problem_set_design (確認ポイント生成、5段階 format 付き)
  │
  ▼
coding_problem_delivery (format に応じた問題生成)
  │
  ▼
await_coding_input ◄── interrupt (ユーザーがコード提出)
  │
  ├─ ユーザーが質問(chat) → coding_chat_response → await_coding_input
  ├─ ユーザーがコード提出(form) → code_evaluation
  │
  ▼
code_evaluation (コード評価)
  │
  ├─ next_step → coding_problem_delivery (同CP、次の format へ)
  ├─ next_cp → coding_problem_delivery (次CP、format リセット)
  ├─ complete → progress_update → END
```

### B2. 既存グラフとの関係

**新しいグラフを別途作成**する（`coding_graph.py`）。既存の `graph.py` は残す。

理由:
- 座学フェーズの interrupt が追加される（既存は1箇所、新規は2箇所）
- 5段階 format ループが deepdive とは根本的に異なるロジック
- 既存グラフに条件分岐を足すと全ノードに `session_stage` 分岐が入り肥大化
- 既存テストへの影響を回避

### B3. CodingSessionState（新規 TypedDict）

**対象ファイル**: `backend/quiz/domain/coding_session_state.py`（新規）

既存の `SessionState` とは別に定義する。`ConfirmationPointFormat` も新しい型を使う。

```python
CodingDifficulty = Literal["rewrite", "fill_blank", "bug_fix", "extend", "implement"]

class CodingConfirmationPoint(TypedDict):
    id: str
    content: str
    format: CodingDifficulty  # 5段階の固定順序

class CodingProblemAttempt(TypedDict):
    confirmation_point_id: str
    format: CodingDifficulty
    question_text: str
    example_code: str
    answer_text: str
    score: int
    feedback: str

class CodingSessionState(TypedDict, total=False):
    # セッション識別
    session_id: str
    roadmap_item_id: str
    roadmap_item_level: RoadmapItemLevel
    roadmap_item_title: str
    roadmap_item_description: str
    is_resumed: bool

    # 座学フェーズ
    lecture_content: str            # LLM生成の座学テキスト
    lecture_phase_active: bool      # True=座学中, False=実践中

    # 確認ポイント
    confirmation_points: list[CodingConfirmationPoint]
    current_point_index: int

    # コーディング問題
    current_question_text: str
    current_example_code: str       # 表示するサンプルコード
    current_format: CodingDifficulty
    total_questions_asked: int
    coding_attempts: list[CodingProblemAttempt]

    # ユーザー入力
    user_input: str
    input_source: Literal["form", "chat"]

    # 評価結果
    next_action: Literal["next_step", "next_cp", "complete"]
    current_score: int
    current_feedback: str

    # チャット
    chat_response_text: str
```

### B4. 難易度プログレッション設計（5段階命名方式）

各 CP は固定順序の format を持ち、段階的に難しくなる:

| format | 問題スタイル | 例 |
|--------|-------------|-----|
| `rewrite` | 例示コード → 軽微な書き換え | 「この関数の戻り値を変更せよ」 |
| `fill_blank` | 部分穴埋め | 「フィルタ条件を埋めよ」 |
| `bug_fix` | 壊れた実装の修正 | 「このコードのバグを直せ」 |
| `extend` | 既存実装への要件追加 | 「エラーハンドリングを追加せよ」 |
| `implement` | シグネチャと入出力例のみ → 自力実装 | 「〜する関数を実装せよ」 |

**進行ルール**:
- Score >= 70: 同CPの次の format へ進む（`next_step`）
- 全 format を通過: 次CPへ（`next_cp`、format を `rewrite` にリセット）
- Score < 70: フィードバック後、同 format でリトライ1回 → それでも < 70 なら次CPへ
- 全CPを完了: `complete`
- 20問収束ルールは維持（deepdive なし）
- CP毎に全5段階を必ず通る必要はない。`coding_problem_set_design` が CP の性質に応じて開始 format と最終 format を設定する
- **CP件数は最大20件**まで許容する（下限なし。トピックの広さに応じて LLM が適切な件数を決定）

### B5. 座学→実践の遷移

**専用エンドポイント**: `POST /sessions/{session_id}/practice/start`

- 座学中は `input_source="chat"` のみ許可し、質問応答だけ返す
- practice 開始は上記エンドポイントでのみ行う（interrupt resume ではなく明示的 API）
- practice 中は `input_source="form"` がコード回答、`input_source="chat"` は質問のみ
- **practice 中の chat で answer 判定はしない**。採点対象は form のコード提出のみ

### B6. 新規 LLM アダプタ

**対象ファイル**: `backend/quiz/infrastructure/codex_coding_llm_adapters.py`（新規）

| アダプタ | 役割 |
|---------|------|
| `CodexLectureGenerationLlm` | ロードマップ項目から構造化された座学コンテンツ生成 |
| `CodexLectureChatResponseLlm` | 座学中のユーザー質問に回答 |
| `CodexCodingProblemSetDesignLlm` | 確認ポイント生成（format の順序・範囲を計画）|
| `CodexCodingProblemDeliveryLlm` | format に応じたコーディング問題生成（テンプレート切替）|
| `CodexCodeEvaluationLlm` | コード回答の評価（正しさ、品質、次アクション決定）|

### B7. 新規グラフノード

**対象ディレクトリ**: `backend/quiz/application/`

| ファイル | ノード |
|---------|--------|
| `lecture_generation.py` | 座学コンテンツ生成 |
| `lecture_chat_response.py` | 座学中チャット応答 |
| `coding_problem_set_design.py` | コーディング確認ポイント設計 |
| `coding_problem_delivery.py` | format 別コーディング問題出題 |
| `code_evaluation.py` | コード評価＋ルーティング |
| `coding_graph.py` | グラフ定義 + `CodingGraphRunner` |

各ノードに対応する `*_types.py` Protocol ファイルも作成。

### B8. フロントエンド変更

**対象ディレクトリ**: `frontend/src/features/session/`

| 変更 | 内容 |
|------|------|
| `lecture-phase.tsx`（新規） | 座学表示 + チャット入力 + 「演習を始める」ボタン |
| `question-phase.tsx`（改修） | 常にコードエディタ、`example_code` 表示、format 名表示 |
| `feedback-phase.tsx`（改修） | format 情報表示、「同じ問題をもう一度」or「次へ」の分岐 |
| `use-quiz-session-store.ts`（改修） | `"lecture"` フェーズ追加、新 state フィールド対応 |
| `quiz-session-page.tsx`（改修） | 新フェーズのルーティング |
| `types/api.ts`（改修） | `CodingSessionState` インターフェース追加 |

lecture 中は回答フォームを表示しない。practice 開始後はコードエディタのみ表示。

---

## C. 競プロアルゴリズムクイズ（新機能）

### C1. アルゴリズムテーマプリセット

**対象ファイル**: `backend/data/algo_themes.json`（新規）

```json
[
  {"id": "algo-001", "category": "探索", "label": "二分探索"},
  {"id": "algo-002", "category": "グラフ", "label": "深さ優先探索 (DFS)"},
  ...
]
```

120件以上、重複禁止、各要素は `{id, category, label}` の3フィールドのみ。
`preset_topics.json` と同パターンで repo 管理の静的ファイル。

カテゴリ例: 探索、ソート、グラフ、動的計画法、貪欲法、分割統治、文字列、数学、データ構造、幾何

### C2. バックエンド構成

**新規ディレクトリ**: `backend/competitive/`

```
backend/competitive/
├── domain/
│   └── competitive_types.py         # CompetitiveSessionState, AlgoTheme 等
├── application/
│   ├── theme_selection.py           # ランダムテーマ選択
│   ├── problem_generation.py        # LLMで問題+模範解答+rubric同時生成
│   ├── solution_evaluation.py       # 保存済み rubric を使って採点
│   └── competitive_graph.py         # グラフ定義 + CompetitiveGraphRunner
└── infrastructure/
    ├── algo_theme_file_reader.py     # JSONファイル読み込み
    ├── codex_competitive_llm.py      # LLMアダプタ
    └── sql_competitive_store.py      # DB永続化
```

### C3. 競プロ用グラフ（シンプル）

```
theme_selection → problem_generation → await_submission → solution_evaluation → END
```

4ノード、1 interrupt、ループなし。

### C4. CompetitiveSessionState

```python
class CompetitiveSessionState(TypedDict, total=False):
    session_id: str
    algo_theme_id: str
    algo_theme_label: str
    algo_theme_category: str
    problem_statement: str           # 問題文
    input_format: str                # 入出力形式
    output_format: str
    constraints: str                 # 制約
    examples: list[ProblemExample]   # 入出力例
    reference_solution: str          # LLM生成の模範解答（採点用、ユーザー非表示）
    grading_rubric: list[RubricItem] # 採点基準（問題生成時に同時生成）
    user_code: str                   # ユーザーの解答コード
    score: int
    feedback: str
    time_complexity: str
    space_complexity: str
```

**rubric 事前生成方式**: 問題生成時に `reference_solution` と `grading_rubric` を同時生成し、採点時は保存済み rubric を使う。問題生成と採点で LLM の判断がブレるリスクを排除。

**出題言語**: Python または TypeScript からランダムで選択。問題生成時にどちらの言語で出題するか決定し、模範解答もその言語で記述する。

### C5. DB テーブル

`competitive_sessions` テーブル（新規）:
- `id`, `theme_id`, `theme_label`, `theme_category`, `programming_language`, `problem_statement`, `input_format`, `output_format`, `constraints`, `examples_json`, `reference_solution`, `grading_rubric_json`, `status`, `created_at`, `completed_at`

`competitive_answers` テーブル（新規）:
- `id`, `session_id` (UNIQUE — 一問完結のため1セッション1回答), `answer_text`, `score`, `feedback`, `time_complexity`, `space_complexity`, `improvement_suggestions`, `rubric_scores_json`, `created_at`

採点結果は roadmap の `score` / `last_quiz_at` を更新しない（ロードマップ非連動）。

### C6. API エンドポイント

**対象ファイル**: `backend/api/routers/competitive.py`（新規）

| Method | Path | 用途 |
|--------|------|------|
| GET | `/algorithm-quiz/themes` | テーマ一覧取得 |
| GET | `/algorithm-quiz/sessions` | セッション一覧取得（直近50件、ダッシュボード統計用）|
| POST | `/algorithm-quiz/sessions` | セッション開始（テーマ未指定時はランダム選択、問題+rubric 同時生成）|
| POST | `/algorithm-quiz/sessions/{id}/answer` | コード提出＋保存済み rubric で採点 |
| GET | `/algorithm-quiz/sessions/{id}` | セッション状態取得 |

### C7. フロントエンド

**新規ディレクトリ**: `frontend/src/features/competitive/`

| ファイル | 内容 |
|---------|------|
| `competitive-page.tsx` | ランディングページ（テーマ表示、ランダムスタート） |
| `competitive-session-page.tsx` | 問題表示 + コードエディタ + 提出 |
| `competitive-result.tsx` | 評価結果（スコア、計算量分析、改善点） |
| `use-competitive.ts` | TanStack Query フック |
| `use-competitive-store.ts` | Zustand ストア |

**ルーティング追加** (`App.tsx`):
- `/algorithm-quiz` → `CompetitivePage`
- `/algorithm-quiz/:sessionId` → `CompetitiveSessionPage`

**サイドバー追加** (`sidebar.tsx`):
- 「競プロ」ナビゲーション項目

---

## D. デザインファイル（.pen）の改修・新設

### 既存 pen ファイル一覧

| ファイル | 内容 | 今回の影響 |
|---------|------|-----------|
| `docs/design/pen/dashboard.pen` | ダッシュボード（統計、ロードマップ要約、最近の活動、空状態） | 改修: 競プロ統計セクション追加 |
| `docs/design/pen/quiz-session.pen` | セッション全画面（学習→出題→フィードバック→解説→サマリー 9画面） | 改修: 座学フェーズ画面追加、出題画面をコード専用に変更 |
| `docs/design/pen/roadmap-detail.pen` | ロードマップツリー、アイテム詳細、ダイアログ群 | 変更なし |
| `docs/design/pen/feedback-list.pen` | フィードバック一覧 | 変更なし |

### D1. `quiz-session.pen` の改修

セッションフローが「学習→出題」から「座学→コーディング」に変わるため、以下の画面を追加・変更する:

**追加する画面:**
- **座学フェーズ**: 座学テキスト表示エリア（コード例含む）、チャット入力欄、「演習を始める」ボタン。現行の「学習フェーズ」とは別画面として追加
- **座学チャット応答**: 座学中に質問した際のチャットバブル表示状態

**変更する画面:**
- **出題フェーズ**: textarea 入力を廃止しコードエディタのみに統一。`example_code` 表示領域を問題文の上に追加。format 名（rewrite / fill_blank / bug_fix / extend / implement）のバッジ表示を追加
- **フィードバックフェーズ**: format 情報を表示。next_action が `next_step`（同CP次の難易度）か `next_cp`（次のCP）かを視覚的に区別

### D2. `competitive-quiz.pen` の新設

**新規ファイル**: `docs/design/pen/competitive-quiz.pen`

競プロアルゴリズムクイズ専用の画面群:

| 画面 | 内容 |
|------|------|
| ランディング | テーマ一覧（カテゴリ別）、「ランダムで挑戦」ボタン、過去の挑戦履歴 |
| 問題表示 | 問題文、入出力形式、制約、入出力例、コードエディタ、「提出」ボタン、出題言語（Python/TypeScript）表示 |
| 結果 | スコア、rubric 項目別の得点内訳、計算量分析、改善提案、「別の問題に挑戦」ボタン |

### D3. `dashboard.pen` の改修

ダッシュボードに競プロ関連の統計を追加:
- 競プロ挑戦数、平均スコア等のスタットカード追加
- 最近の活動タイムラインに競プロの結果も表示

### D4. 実装タイミング

pen ファイルの作業は各 Phase のフロントエンド実装**前**に行う（デザインファースト）:
- Phase 2 開始前: `competitive-quiz.pen` 新設 + `dashboard.pen` 改修
- Phase 3 開始前: `quiz-session.pen` 改修

---

## 実装順序

スコープが大きいため、以下の順序で**1つずつ**進める:

### Phase 1: ロードマップ生成プロンプト変更（A）

**Step 1-1: プロンプト改修**
- `backend/roadmap/infrastructure/codex_roadmap_generation_llm.py` のシステムプロンプト変更
- 既存テストがあれば修正
- → Codex レビュー → 指摘対応 → LGTM
- → `feat: ロードマップ生成をコーディング実践指向に変更`

---

### Phase 2: 競プロクイズ新設（C + D2 + D3）

**Step 2-1: デザイン — `competitive-quiz.pen` 新設**
- ランディング画面、問題表示画面、結果画面の3画面を作成
- → Codex レビュー → 指摘対応 → LGTM
- → `docs: 競プロクイズのデザインファイルを作成`

**Step 2-2: デザイン — `dashboard.pen` 改修**
- 競プロ統計セクション追加
- → Codex レビュー → 指摘対応 → LGTM
- → `docs: ダッシュボードに競プロ統計セクションを追加`

**Step 2-3: BE ドメイン層**
- `backend/competitive/domain/competitive_types.py` — `CompetitiveSessionState`, `AlgoTheme`, `ProblemExample`, `RubricItem` 等
- `backend/data/algo_themes.json` — 120件以上のテーマプリセット
- テスト: 型定義の整合性テスト
- → Codex レビュー → 指摘対応 → LGTM
- → `feat: 競プロクイズのドメイン型とテーマプリセットを追加`

**Step 2-4: BE インフラ層**
- `backend/competitive/infrastructure/algo_theme_file_reader.py` — JSON読み込み
- `backend/competitive/infrastructure/codex_competitive_llm.py` — 問題生成 + rubric 生成 / 採点の2アダプタ
- `backend/competitive/infrastructure/sql_competitive_store.py` — DB永続化
- DB マイグレーション（`competitive_sessions`, `competitive_answers` テーブル）
- テスト: 各インフラの単体テスト
- → Codex レビュー → 指摘対応 → LGTM
- → `feat: 競プロクイズのインフラ層を実装`

**Step 2-5: BE アプリケーション層（グラフ）**
- `backend/competitive/application/theme_selection.py` — ランダムテーマ選択ノード
- `backend/competitive/application/problem_generation.py` — 問題生成ノード
- `backend/competitive/application/solution_evaluation.py` — 解答評価ノード
- `backend/competitive/application/competitive_graph.py` — グラフ定義 + `CompetitiveGraphRunner`
- 各ノードの `*_types.py` Protocol
- テスト: 各ノード単体テスト + グラフ統合テスト（モック LLM）
- → Codex レビュー → 指摘対応 → LGTM
- → `feat: 競プロクイズのLangGraphグラフを実装`

**Step 2-6: BE API 層**
- `backend/api/routers/competitive.py` — 4エンドポイント
- DI コンテナ更新（`dependencies.py`）
- テスト: API エンドポイントテスト
- → Codex レビュー → 指摘対応 → LGTM
- → `feat: 競プロクイズのAPIエンドポイントを追加`

**Step 2-7: FE 実装**
- `frontend/src/types/api.ts` — 競プロ関連型追加
- `frontend/src/features/competitive/` — 全コンポーネント + フック + ストア
- `App.tsx` ルーティング追加、`sidebar.tsx` ナビ追加
- テスト: コンポーネントテスト（vitest）
- → Codex レビュー → 指摘対応 → LGTM
- → `feat: 競プロクイズのフロントエンドを実装`

**Step 2-8: FE ダッシュボード改修**
- `dashboard-page.tsx` に競プロ統計セクション追加
- → Codex レビュー → 指摘対応 → LGTM
- → `feat: ダッシュボードに競プロ統計を追加`

---

### Phase 3: コーディングセッションフロー（B + D1）

**Step 3-1: デザイン — `quiz-session.pen` 改修**
- 座学フェーズ画面追加（座学テキスト + チャット + 「演習を始める」ボタン）
- 出題画面をコードエディタ専用に変更、format バッジ追加、example_code 領域追加
- フィードバック画面に format 情報・next_action 区別を追加
- → Codex レビュー → 指摘対応 → LGTM
- → `docs: クイズセッションのデザインを座学+コーディング構成に改修`

**Step 3-2: BE ドメイン層**
- `backend/quiz/domain/coding_session_state.py` — `CodingSessionState`, `CodingConfirmationPoint`, `CodingProblemAttempt`, `CodingDifficulty` 型
- テスト: 型定義の整合性テスト
- → Codex レビュー → 指摘対応 → LGTM
- → `feat: コーディングセッションのドメイン型を追加`

**Step 3-3: BE インフラ層（LLM アダプタ）**
- `backend/quiz/infrastructure/codex_coding_llm_adapters.py` — 5アダプタ
  - `CodexLectureGenerationLlm` — 座学生成
  - `CodexLectureChatResponseLlm` — 座学チャット
  - `CodexCodingProblemSetDesignLlm` — CP設計
  - `CodexCodingProblemDeliveryLlm` — format別出題
  - `CodexCodeEvaluationLlm` — コード評価
- テスト: 各アダプタの単体テスト
- → Codex レビュー → 指摘対応 → LGTM
- → `feat: コーディングセッション用LLMアダプタを実装`

**Step 3-4: BE アプリケーション層（グラフノード）**
- `backend/quiz/application/lecture_generation.py` + `*_types.py`
- `backend/quiz/application/lecture_chat_response.py` + `*_types.py`
- `backend/quiz/application/coding_problem_set_design.py` + `*_types.py`
- `backend/quiz/application/coding_problem_delivery.py` + `*_types.py`
- `backend/quiz/application/code_evaluation.py` + `*_types.py`
- テスト: 各ノード単体テスト
- → Codex レビュー → 指摘対応 → LGTM
- → `feat: コーディングセッションのグラフノードを実装`

**Step 3-5: BE アプリケーション層（グラフ定義）**
- `backend/quiz/application/coding_graph.py` — グラフ定義 + `CodingGraphRunner`
- テスト: グラフ統合テスト（モック LLM でフロー全体を通す）
- → Codex レビュー → 指摘対応 → LGTM
- → `feat: コーディングセッションのLangGraphグラフを実装`

**Step 3-6: BE API 層**
- `backend/api/routers/quiz.py` 改修 — `POST /sessions/{id}/practice/start` 追加、既存エンドポイントの `CodingSessionState` 対応
- DI コンテナ更新
- テスト: API エンドポイントテスト
- → Codex レビュー → 指摘対応 → LGTM
- → `feat: コーディングセッションのAPIエンドポイントを追加`

**Step 3-7: FE 実装**
- `frontend/src/types/api.ts` — `CodingSessionState` 型追加
- `frontend/src/features/session/lecture-phase.tsx` — 座学画面（新規）
- `frontend/src/features/session/question-phase.tsx` — コード専用に改修
- `frontend/src/features/session/feedback-phase.tsx` — format 対応に改修
- `frontend/src/features/session/use-quiz-session-store.ts` — 新フェーズ対応
- `frontend/src/features/session/quiz-session-page.tsx` — ルーティング改修
- テスト: コンポーネントテスト（vitest）
- → Codex レビュー → 指摘対応 → LGTM
- → `feat: セッションUIを座学+コーディング構成に改修`

---

### 各ステップ共通のフロー

```
実装 → ビルド/リント確認 → Codex レビュー依頼（プレーン）
  → 指摘あり → 修正 → 再レビュー（前回指摘を含めない）
  → 指摘なし(LGTM) → コミット（1コミット1目的）→ 次のステップへ
```

- Codex レビュー待ち中は次ステップの作業をしない
- 再レビューでも前回指摘を含めずプレーンに依頼する
- コミットメッセージは `prefix: 変更内容` 形式

---

## 検証方法

### バックエンド
- 各ノードの単体テスト（`test_*.py` コロケーション）
- グラフ統合テスト（モック LLM でフロー全体を通す）
- API エンドポイントテスト

### フロントエンド
- 各フェーズコンポーネントのテスト（vitest）
- 手動 E2E: ブラウザで座学→コーディング問題フロー、競プロフローを通す

### プロンプト品質
- ロードマップ生成: 実際に数トピックで生成し、コーディングスキル指向になっているか確認
- 難易度段階性: 各 format の問題が実際に段階的に難しくなるか確認
- 競プロ問題: 出題内容がテーマに合致し、解答可能な難易度か確認

---

## 設計判断の根拠

| 項目 | 判断 | 根拠 |
|------|------|------|
| 難易度表現 | 5段階命名（rewrite〜implement） | 数値レベルより具体的、出題テンプレートと直結 |
| グラフ構成 | 新グラフ分離 | 既存破壊リスク回避、ノード肥大化防止 |
| practice 開始 | 専用エンドポイント | ライフサイクルイベントの明確化 |
| practice 中 chat | answer 判定禁止 | 採点対象は form コードのみに限定 |
| 競プロ rubric | 問題生成時に同時生成 | 採点一貫性の確保 |
| 競プロ配置 | `backend/competitive/` 独立 | `backend/{機能}/` 規約に準拠、責務境界の明確化 |
| SessionState | 新型 `CodingSessionState` を別定義 | 既存 `SessionState` の後方互換維持 |
