---
type: impl
profile: backend
scope: quiz/session-lifecycle
spec: docs/spec/backend/quiz/session-lifecycle.md
test_cases: tests/test-cases/backend/quiz/session-lifecycle.md
---

## 今回やること
session-lifecycle (session_init ノード) を TDD で実装する

## 対象テストケース
- TC-01: 新規セッション開始で QuizSession 作成と LangGraph 開始結果が観測できる
- TC-02: 各回答が後続処理前に QuizAnswer へ永続化完了する
- TC-03: 全確認ポイント完了でセッション完了処理が行われる
- TC-10: QuizAnswer 履歴を使って in_progress セッションを順序付き問答ペアとして再開できる
- TC-11: 同一ロードマップ項目に既存 in_progress がある場合は新規作成せず再開対象を返す
- TC-12: QuizAnswer 0件の in_progress セッション再開は空履歴で実質新規開始と同じ
- TC-20: 明示的中断でも QuizSession は in_progress のまま残る
- TC-21: ブラウザ離脱による中断でも明示的な再開要求で続行できる
- TC-22: 長期間放置された in_progress セッションも期限なく再開できる
- TC-30: 再開時にDB履歴取得と LLM 続行指示が連携し順序付き問答ペアで非エラー進行する
- TC-31: セッション開始時の永続化失敗または LangGraph 開始失敗で原子性と例外契約が守られる
- TC-32: 再開時の履歴取得失敗または LLM 続行開始失敗で状態不変と例外契約が守られる

## やらないこと
- 複数セッション同時進行
- セッション削除
- アプリ起動時の再開候補列挙
- セッション履歴一覧表示

## 完了条件
- 対象テストケースが全て GREEN
- ruff + mypy がパス
- レビュー通過

## 設計判断
- session_init は quiz/application/ に配置
- Protocol dependencies: QuizSessionStore, QuizAnswerStore, RoadmapItemReader
- 例外は QuizSessionLifecycleError (error_code + message + __cause__)
- ログは structlog、EVENT_* 定数パターン
- SessionState は quiz/domain/session_state.py から import
- テスト: quiz/application/test_session_lifecycle.py（コロケーション）
- quiz/application/__init__.py を空ファイルとして新規作成
