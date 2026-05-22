---
feature: session-lifecycle
status: ready
reviewed_by:
approved_at:
---

## 機能概要

クイズセッションの開始・進行・再開・完了を管理する。LangGraphのインメモリステートとQuizSessionテーブルを連携させ、中断したセッションの再開を可能にする。

## 振る舞い

### セッション開始

ユーザーがロードマップ項目を選択してセッションを開始する。

- QuizSessionレコードを作成（status: in_progress）
- LangGraphセッションを開始
- 問題セット設計ノードに進む

### セッション進行

LangGraphのループで問答を繰り返す。各回答はQuizAnswerに即座に記録される。

### セッション再開

in_progressのセッションを再開する（ADR-005参照）。

- QuizSessionに紐づくQuizAnswer履歴を取得
- 履歴をLLMに渡して新しいLangGraphセッションとして続行
- 「ここまでの問答を踏まえて、続きから出題して」と指示

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

### 具体例

```
開始: ユーザーが「ジェネリクスの基本構文と型パラメータ」を選択
  → QuizSession作成（status: in_progress）
  → 問題セット設計 → 出題開始

中断: 3問回答した後、ブラウザを閉じる
  → QuizSession: in_progress のまま
  → QuizAnswer: 3件記録済み

再開: ユーザーがアプリを開き、in_progressのセッションを選択
  → QuizAnswer 3件をLLMに渡す
  → 4問目から続行

完了: 全確認ポイント終了
  → 総合評価 → score更新 → status: completed
```

## 技術判断

- statusを in_progress / completed の2値とする理由: 中断もタイムアウトもin_progressとして扱い、再開可能にする。abandonedを別ステータスにする必要がない
- LangGraphのチェックポイント永続化を使わない理由: QuizAnswer履歴で代替可能。LangGraphへの依存を減らす（ADR-005参照）

## 境界条件

- 同一ロードマップ項目でin_progressのセッションが既にある場合 → そのセッションの再開を促す（新規作成しない）
- QuizAnswer 0件のセッションを再開 → 実質新規開始と同じ
- 長期間放置されたin_progressセッション → 再開可能。期限は設けない

## スコープ外

- 複数セッションの同時進行
- セッションの削除
- セッション履歴の一覧表示（参照系はanalytics側）

## 受け入れ基準

- [ ] ロードマップ項目を選択してセッションを開始できる
- [ ] 各回答がQuizAnswerに即座に記録される
- [ ] in_progressのセッションをQuizAnswer履歴から再開できる
- [ ] 全確認ポイント完了時にstatusがcompletedに変わる
- [ ] 完了時にRoadmapItem.scoreが更新される
- [ ] 同一項目でin_progressのセッションがあれば再開を促す
