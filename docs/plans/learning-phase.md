# クイズセッションに学習フェーズを追加

## Context

クイズ開始時にいきなり出題されるため、学習者が準備なく問われる。
「学習フェーズ（トピック解説）→ テストフェーズ（出題）」の2段階にする。

## 前提: グラフ構造は変更しない

現行のグラフは `question_set_design → question_delivery → await_input` で、`start_graph()` 時点で初問まで生成済み。learning フェーズは **初問を隠しているだけの UI フェーズ** であり、バックエンド側でグラフノードの追加や interrupt ポイントの変更は行わない。「テスト開始」ボタンは単にフロントの phase を `learning` → `question` に切り替えるだけ。

## 前提: learning 判定は初回 hydration 時のみ

`learning` への遷移は **sessionState 初期化時の useEffect 内でのみ** 行う。phase が一度でも `question` 以降に移ったら、answers が空であっても `learning` に戻さない。これにより chat/explanation 送信後の sessionState 更新で learning に巻き戻る問題を防ぐ。

## 前提: リロード時の learning 再表示は通常運用のみ保証

`GET /sessions/{id}` の `graph_state` が取得できる場合（MemorySaver に checkpoint が残っている場合）のみ `topic_overview` を含む状態を復元できる。

`graph_state` 欠落時の挙動:
- `graph_state` なし → status に関わらず復旧不能エラー UI（「セッションの状態を復元できません」+ ロードマップへの導線）
- 現行 backend は `graph_state` なし completed 時に answers を DB から補完する処理を持たないため、completed でも復旧不能扱いにする（backend 変更不要で済む簡素な方針）

`graph_state` がない原因は backend 再起動（MemorySaver リセット）に限らず、`graph_runner is None` や `LookupError` でも発生しうる。フロント側は原因を区別せず「`graph_state` がない」という観測事実で分岐する。

## 前提: answers の判定条件

fresh session では `answers` キー自体が存在しない（`undefined`）。learning 判定は「`answers` が未設定（`undefined`）または空配列」の両方を許容する。

## 意思決定

| 項目 | 決定 | 理由 |
|------|------|------|
| 再表示ルール | `answers` が空なら learning 表示、回答済みなら question | シンプル、リロード時に概要を見返せる |
| 戻り値の形 | dataclass `QuestionSetDesignResult` (DTO) | 正式な契約変更 |
| 仕様書更新 | 実装と同時に更新 | 契約変更を含むため仕様が先にズレる |
| SessionProgress | learning 中は非表示 + 1カラムレイアウト | 2カラムのまま非表示にすると288px空白 |

---

## 変更対象ファイル

### Backend 実装

| ファイル | 変更内容 |
|---------|---------|
| `backend/quiz/domain/session_state.py` | `topic_overview: str` フィールド追加 (NotRequired) |
| `backend/quiz/application/question_set_design_types.py` | `QuestionSetDesignResult` dataclass 新規追加、Protocol 戻り値変更 |
| `backend/quiz/application/question_set_design.py` | DTO から `topic_overview` を取り出して state に格納 |
| `backend/quiz/infrastructure/codex_llm_adapters.py` | LLM プロンプト修正、JSON 形式を `{"topic_overview": "...", "confirmation_points": [...]}` に、パース後に `QuestionSetDesignResult` を返す |

### Backend テスト

| ファイル | 変更内容 |
|---------|---------|
| `backend/quiz/domain/test_session_state.py` | `_SESSION_STATE_KEYS` に `topic_overview` 追加、フィールド数 18 → 19、`str` 型検証、optional 検証、partial state 検証、all-keys count 検証を更新 |
| `backend/quiz/application/test_question_set_design.py` | stub を `QuestionSetDesignResult` 返却に変更、result 期待値に `topic_overview` 追加 |
| `backend/quiz/application/test_question_set_design_types.py` | `QuestionSetDesignResult` の型テスト追加 |
| `backend/quiz/infrastructure/test_codex_llm_adapters.py` | JSON レスポンス形式変更に合わせて更新 |
| `backend/tests/integration/test_quiz_scenarios.py` | LLM 応答スタブを配列 → `{"topic_overview": ..., "confirmation_points": [...]}` に更新 |
| `backend/api/routers/test_routers.py` | `GET /sessions/{id}` の router テストで `graph_state` に `topic_overview` が含まれることを検証 |
| `backend/tests/integration/test_quiz_scenarios.py` | 実 `QuizGraphRunner` を使い `start_graph → checkpoint → get_state → GET /sessions/{id}` を通して `graph_state.topic_overview` が返ることを確認する E2E 統合ケースを追加 |

### Backend 仕様書

| ファイル | 変更内容 |
|---------|---------|
| `docs/spec/backend/quiz/session-state.md` | `topic_overview` フィールド追加（件数・キー列挙・C2 first-write 責務・部分状態例・全キー状態例をすべて更新）|
| `docs/spec/backend/quiz/question-set-design.md` | `QuestionSetDesignResult` DTO 追加、戻り値契約更新、`error_code` ごとの `message` 固定文言を実装と整合 |
| `docs/spec/backend/quiz/quiz-overview.md` | SessionState フィールド一覧・C2 書き込み責務に `topic_overview` 追加 |
| `docs/spec/backend/quiz/graph-state-retrieval.md` | フィールド数・本文・レスポンス例に `topic_overview` を追加（count だけでなく全体更新） |
| `docs/spec/backend/quiz/session-api-enrichment.md` | `graph_state` に `topic_overview` が含まれうることを注記（フロント側挙動は `03-quiz-session.md` に集約、ここには書かない）|
| `tests/test-cases/backend/quiz/session-state.md` | テストケース更新 |
| `tests/test-cases/backend/quiz/question-set-design.md` | テストケース更新 |
| `tests/test-cases/backend/quiz/graph-state-retrieval.md` | フィールド数・例の更新 |

### Backend スクリプト

| ファイル | 変更内容 |
|---------|---------|
| `backend/scripts/verify_llm_prompts.py` | `generate_confirmation_points()` 戻り値を `QuestionSetDesignResult` に対応 |

### Frontend 実装

| ファイル | 変更内容 |
|---------|---------|
| `frontend/src/types/api.ts` | `SessionState` に `topic_overview?: string` 追加 |
| `frontend/src/features/session/use-quiz-session-store.ts` | `QuizPhase` に `"learning"` 追加 |
| `frontend/src/features/session/learning-phase.tsx` | 新規: 学習フェーズ UI |
| `frontend/src/features/session/quiz-session-page.tsx` | learning フェーズ表示・遷移、learning 中は 1カラム + SessionProgress 非表示 |

### Frontend 仕様書・テスト

| ファイル | 変更内容 |
|---------|---------|
| `docs/design/frontend/03-quiz-session.md` | learning フェーズの UI 仕様・phase union・状態遷移図を追加。API 依存セクション（SessionState 形状に `topic_overview` 追加、`GET /sessions/{id}` の `graph_state` 前提更新）も同時更新。`graph_state` 欠落時の復旧不能 UI 仕様もここに集約（backend spec には書かない）|
| `frontend/src/features/session/quiz-session-page.test.tsx` | 既存テスト群を API fixture（`graph_state` 付き）主導に組み替え + learning 初回表示、テスト開始遷移、answers 未設定/空での再読込、sidebar 非表示、`graph_state` から hydration、`graph_state` 欠落での復旧不能 UI、refetch 後に learning に戻らないことの検証 |

---

## Step 1: `QuestionSetDesignResult` DTO 新規追加

`backend/quiz/application/question_set_design_types.py`:
```python
@dataclass(frozen=True)
class QuestionSetDesignResult:
    confirmation_points: list[ConfirmationPoint]
    topic_overview: str
```

Protocol `QuestionSetDesignLlmClient` の戻り値:
```python
def generate_confirmation_points(...) -> QuestionSetDesignResult: ...
```

## Step 2: SessionState に `topic_overview` 追加

`backend/quiz/domain/session_state.py`:
```python
topic_overview: str  # C2 で生成、学習フェーズで表示
```

## Step 3: LLM プロンプト修正

`backend/quiz/infrastructure/codex_llm_adapters.py`:

レスポンス形式:
```json
{
  "topic_overview": "このトピックの概要（3〜5文）",
  "confirmation_points": [{"id": "cp-001", "content": "...", "format": "..."}]
}
```

topic_overview の指示:
- タイトルと説明の範囲で、学習者が問題に取り組む前に知っておくべき概要を3〜5文で書く
- 用語の定義、基本概念、なぜ重要かを含める

パース後に `QuestionSetDesignResult` を返す。

`topic_overview` のバリデーション:
- `strip()` 後に非空であることを検証。空文字の場合は `QuestionSetDesignError(error_code="llm_response_parse_failed")` を送出
- adapter テストにも空文字ケースを追加

エラーメッセージ正規化:
- `error_code="llm_request_failed"` → `message="question set design llm request failed"`
- `error_code="llm_response_parse_failed"` → `message="question set design llm response parse failed"`
- 現行実装の `"confirmation points generation failed: ..."` を仕様の固定文言に揃える

## Step 4: question_set_design ノード修正

`backend/quiz/application/question_set_design.py`:
- LLM から `QuestionSetDesignResult` を受け取る
- `topic_overview` と `confirmation_points` の両方を state に格納

## Step 5: Frontend — 型・store

- `frontend/src/types/api.ts`: `topic_overview?: string` 追加
- `use-quiz-session-store.ts`: `QuizPhase` に `"learning"` 追加

## Step 6: LearningPhase コンポーネント新規作成

`frontend/src/features/session/learning-phase.tsx`:
- ExplanationPhase を参考にした構成
- トピックタイトル + 概要テキスト
- 確認ポイント一覧（これから問われる内容のプレビュー）
- 「テスト開始」ボタン

## Step 7: quiz-session-page.tsx 修正

判定ロジック（**sessionState 初期化の useEffect 内で、`data.graph_state` を直接参照。`hasHydratedRef` で一度きり実行を保証**）:
```typescript
const hasHydratedRef = useRef(false);

useEffect(() => {
  if (!data || hasHydratedRef.current) return;

  const gs = data.graph_state;
  if (!gs) {
    // graph_state なし → 復旧不能エラー UI（status に関わらず）
    return;
  }

  hasHydratedRef.current = true;
  setSessionState(gs);

  if (data.session.status === "completed") {
    setPhase("summary");
  } else if (gs.topic_overview && (!gs.answers || gs.answers.length === 0)) {
    setPhase("learning");
  }
  // それ以外は初期値 "question" のまま
}, [data]);

// graph_state 欠落時の専用描画分岐（既存の 404/汎用エラーとは別）:
// `!isLoading && !isError && data && !data.graph_state` の条件で
// 既存の汎用エラー UI を文言変更して再利用する
// （「セッションの状態を復元できません」+ ロードマップへの導線）
// sessionState が null のままでも描画されるよう、既存条件の外に配置
```
- `hasHydratedRef` で初回のみ実行。refetch / sessionState 更新で再実行しない
- 判定元は `data.graph_state`（API レスポンス直値）、`sessionState` 経由ではない
- phase が一度でも `question` 以降に遷移したら `learning` に戻さない

レイアウト:
- learning 中は **1カラム**（SessionProgress 非表示、grid-cols-[1fr_288px] を適用しない）
- learning 中は **SessionHeader も非表示**（summary と同じ扱い。LearningPhase 内でタイトルを表示するため二重表示を防ぐ）
- question 以降は通常の 2カラム + SessionHeader 表示

---

## 受け入れた仕様上の許容事項

- 初回回答前に解説だけ依頼してリロード → learning に戻る（回答前なので概要を見直す意味がある、意図した動作）
- backend 再起動後（MemorySaver リセット）は graph_state なし → 復旧不能エラー UI 表示（learning もスキップ）

## 検証

1. `cd backend && uv run pytest` — 既存テスト全通過
2. `docker compose up --build backend frontend -d`
3. クイズ開始 → learning フェーズ表示（概要 + 確認ポイント一覧、1カラム、SessionHeader なし、サイドバーなし）
4. 「テスト開始」→ question フェーズ表示（2カラム、SessionHeader あり、サイドバーあり）
5. リロード → answers 未設定/空なので learning 再表示
6. 回答後リロード → question フェーズ表示（learning スキップ）
7. graph_state なし（原因不問）→ 復旧不能エラー UI 表示
8. 統合テスト `test_quiz_scenarios.py` が通過する
9. `topic_overview` が `GET /sessions/{id}` のレスポンスに含まれることをテストで確認
