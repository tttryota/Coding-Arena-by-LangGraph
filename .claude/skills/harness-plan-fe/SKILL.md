---
description: 'フロントエンド仕様書から実装 plan 群を生成する。使用場面: ready の仕様書から Component / Logic / Page の plan を対話的に生成。トリガー: "/harness-plan-fe"'
name: harness-plan-fe
---
# /harness-plan-fe — FE Plan 生成

ready の仕様書 + コンポーネント定義書 + Figma キャッシュから、実装 plan 群を生成する。

## 入力要件

以下を確認してから plan 生成を開始する:

| 入力 | パス例 | 条件 |
|---|---|---|
| 仕様書 | `docs/spec/features/{feature}.md` | status: ready |
| コンポーネント定義書 | `docs/design/features/{feature}/components.md` | status: ready |
| Figma キャッシュ | `docs/design/features/{feature}/` | ディレクトリが存在 |
| テストケース | `tests/test-cases/features/{feature}.md` | ファイルが存在（Logic/Page で必要） |

いずれかが不足している場合はユーザーに伝えて、先行ステップ（仕様書 / コンポーネント定義書 / Figma キャッシュ準備）を案内する。

## 生成手順

1. 仕様書を読み、feature の全体像を把握
2. コンポーネント定義書を読み、「種別」列で新規/既存を判別。新規のみが Component plan の対象
3. 仕様書の「機能要件」セクションから必要な hooks / atoms / API クライアントを導出
4. 仕様書の「機能要件 > API 連携」セクションの有無で各 Logic plan の msw フラグを判断
5. Figma キャッシュから各コンポーネント/ページの該当ノードを抽出
6. plan 群を生成し、番号付きで依存順に出力

## 出力

出力先: `plans/{feature}/`

```
plans/quiz/
  01-components.md        ← 新規コンポーネント群（バッチ）
  02-logic-use-quiz.md    ← useQuiz hook
  03-logic-quiz-atom.md   ← quizAtom
  04-page.md              ← QuizPage 組み立て
```

## plan フォーマット

### frontmatter

```yaml
---
type: component | impl | page
profile: frontend
scope: components/quiz | hooks/use-quiz | pages/quiz
spec: docs/spec/features/quiz.md
test_cases: tests/test-cases/features/quiz.md
component_spec: docs/design/features/quiz/components.md
figma_cache: docs/design/features/quiz/
msw: true | false
---
```

type 別の必須フィールド:

| フィールド | Component | Logic | Page |
|---|---|---|---|
| type | component | impl | page |
| profile | frontend | frontend | frontend |
| scope | 必須 | 必須 | 必須 |
| spec | 必須 | 必須 | 必須 |
| test_cases | — | 必須 | 必須 |
| component_spec | 必須 | — | 必須 |
| figma_cache | 必須 | — | 必須 |
| msw | — | 必須 | 必須 |

### body セクション

```markdown
## 今回やること
実装対象の概要

## Targets（Component plan のみ）
- QuizCard
- ScoreBadge

## Dependencies
- name: Button
  import: "@/components/ui/button"
- name: useQuiz
  import: "@/hooks/use-quiz/useQuiz"

## Figma Slice
（Figma キャッシュから該当ノードの抜粋を埋め込む）

## 対象テストケース（Logic/Page のみ）
- 問題を取得して返す
- 回答を送信するとスコアが更新される

## やらないこと
- スコープ外の明示

## 完了条件
- 検証可能な基準

## 設計判断
- 実装上の判断事項
```

Page plan のみ追加:
```markdown
## Browser Scenarios
- name: Quiz回答フロー
  objective: ユーザーが問題に回答してスコアを確認できる
  route: /quiz
  preconditions:
    - ログイン済み
  steps:
    - 問題が表示される
    - 選択肢をクリック
    - 回答結果が表示される
  expect:
    - スコアが更新される
```

## plan 種別ルール

### Component plan
- scope: `components/{feature}`（feature 単位でバッチ）
- Targets に新規コンポーネント名を列挙
- msw は設定しない（Story は props ベースで状態再現、MSW 使用禁止）
- Dependencies にはデザインシステムの既存コンポーネント（shadcn/ui 等）を列挙

### Logic plan
- scope: `hooks/{name}` | `atoms/{name}` | `api/{name}`
- 1 hook/atom = 1 plan（個別実行、フル TDD サイクル）
- msw: 仕様書の API 連携セクションに該当エンドポイントがあれば true
- Dependencies には使用する他の hook/atom があれば列挙

### Page plan
- scope: `pages/{name}`
- Dependencies に使用する全 Component + Logic の名前と import を列挙
- Browser Scenarios セクション必須
- msw: ページが API 呼び出しを含む hook を使う場合は true

## MSW 判断基準

- 仕様書の「機能要件 > API 連携」セクションを確認
- 該当する hook/atom に API 呼び出しがあれば、その Logic plan に `msw: true`
- API 呼び出しがない純粋な状態管理（atom のみ等）は `msw: false`
- Component plan には msw を設定しない
- Page plan は、依存する Logic のいずれかが API を呼ぶなら `msw: true`
