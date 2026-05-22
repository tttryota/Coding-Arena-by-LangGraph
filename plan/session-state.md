---
type: impl
profile: backend
scope: quiz/session-state
spec: docs/spec/backend/quiz/session-state.md
test_cases: tests/test-cases/backend/quiz/session-state.md
---

## 今回やること
SessionState TypedDict + ConfirmationPoint + QuizAnswerRecord を TDD で実装する

## 対象テストケース
- TC-01: SessionState の公開契約と16フィールドの名称を検証する
- TC-02: ConfirmationPoint の3フィールドと QuizAnswerRecord の7フィールドを検証する
- TC-03: Literal値集合が仕様と完全一致することを検証する
- TC-10: SessionState が partial TypedDict（total=False）であることを検証する
- TC-11: C2時点の部分状態（8フィールドのみ）が有効な SessionState として構築できる
- TC-12: ConfirmationPoint が complete record（total=True）であることを検証する
- TC-13: QuizAnswerRecord が complete record（total=True）であることを検証する
- TC-20: answers=[] の初回出題前状態が構築できる
- TC-21: current_point_index == len(confirmation_points) の完了境界が表現できる
- TC-22: total_questions_asked == len(answers) + 1 の出題直後状態が表現できる
- TC-23: C4完了時点の全キー設定済み状態が構築できる

## やらないこと
- LangGraph ノード実装
- ランタイムバリデーション関数
- DB永続化・ORM定義
- レスポンスDTO

## 完了条件
- 対象テストケースが全て GREEN
- ruff + mypy がパス
- レビュー通過

## 設計判断
- SessionState は total=False の partial TypedDict（段階的初期化を許容）
- ConfirmationPoint / QuizAnswerRecord は total=True の complete record
- 値集合は Enum ではなく Literal を使用
- バリデーション関数・生成ヘルパーは含めない（型定義のみ）
- 単一ファイル構成: backend/quiz/domain/session_state.py
- テスト: backend/quiz/domain/test_session_state.py（コロケーション）
- __init__.py は空ファイル（re-export 不要）
- backend/quiz/__init__.py と backend/quiz/domain/__init__.py を新規作成する（新規パッケージ）
