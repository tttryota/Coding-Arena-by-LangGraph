---
feature: summary-test-record
status: ready
reviewed_by:
approved_at:
---

## 機能概要

中枠・大枠レベルのまとめテスト完了時に、LLMが全問答を分析して定性的な弱点・傾向コメントを生成し、SummaryTestResultに保存する。

## 振る舞い

### 基本動作

まとめテスト（中枠・大枠のロードマップ項目に対するクイズセッション）の完了時に実行される。

1. 全QuizAnswerをLLMに渡す
2. LLMが全体を分析し、以下を生成:
   - **score**（0〜100）— 総合的なスコア
   - **analysis**（テキスト）— 弱点・傾向の定性分析
3. SummaryTestResultに保存

### analysisの内容

個別のQuizAnswer.feedbackとは異なり、セッション全体を俯瞰した分析:
- 配下の具体項目間での理解度の偏り
- 知識問題と実践問題の差異
- 全体的な傾向や弱点の指摘
- 次に注力すべき分野の提案

### 具体例

まとめテスト: TypeScript > 基礎（中枠）
配下の具体項目を横断して出題した結果:

```
score: 65
analysis: 「型の基礎知識は十分ですが、ジェネリクスの実践的な使用に
課題があります。特に型パラメータを使った関数を自力で書く場面で
構文ミスが目立ちました。また、型推論の仕組みは理解していますが、
いつ明示的に型を指定すべきかの判断基準が曖昧です。
ジェネリクスの実践問題を重点的に復習することを推奨します。」
```

## 技術判断

- SummaryTestResultを独立テーブルとする理由: LLMによる定性分析（analysis）は単純なスコア集計では生成できない。この分析を保持することがこのテーブルの存在意義
- progress-updateとの違い: progress-updateはdetail項目のscoreを更新する。summary-test-recordは中枠・大枠のまとめテスト結果を記録するだけで、detail項目のscoreには影響しない

## 境界条件

- detail項目のセッション → SummaryTestResultは作成しない（progress-updateのみ）
- 同一ロードマップ項目でまとめテストを複数回実施 → 都度新しいレコードを作成（履歴として蓄積）

## スコープ外

- まとめテスト結果間の比較分析
- analysisに基づくロードマップの自動修正

## 受け入れ基準

- [ ] まとめテスト完了時にSummaryTestResultが作成される
- [ ] LLMによる定性分析（analysis）が生成される
- [ ] scoreが0〜100で算出される
- [ ] detail項目のセッションではSummaryTestResultが作成されない
- [ ] 同一項目の複数回テスト結果が履歴として蓄積される
