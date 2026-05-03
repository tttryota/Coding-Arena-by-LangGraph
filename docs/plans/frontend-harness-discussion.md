# フロントエンドハーネス設計 — 議論トラッカー

計画ファイル: `.claude/plans/cosmic-exploring-naur.md`

---

## 議論対象一覧

### 設計判断が必要
- [x] 1. 実装の優先順位/フェーズ分け
- [x] 2. harness.ts の plan type 分岐設計
- [x] 3. MSW ハンドラ生成のトリガーと仕組み

### 実装詳細（仮おき防止のため事前に詰める）
- [x] 4. プロンプトテンプレートの文面設計（#4a〜#4e で全テンプレート決定済み）
- [x] 5. Storybook の設定と Story 生成パターン
- [x] 6. frontend sourceLayout の具体的な値
- [x] 7. review-criteria-component.md の内容
- [x] 8. review-page-design.md の内容（#4d で決定済み）
- [x] 9. review-page-behavior.md の内容（#4e で決定済み）
- [x] 10. .harness/rules/*.md の内容
- [x] 11. コンポーネント定義書テンプレートの詳細
- [x] 12. /harness-plan-fe skill のプロンプト設計

### 追加項目
- [x] 13. harness-pilot skill の内容設計

### 別タスク（今回のスコープ外）
- [ ] .harness.yml をプロジェクトルートから .harness/harness.yml に移動
- [ ] harness エントリポイントスクリプトを .harness/bin/harness に移動
- [ ] config.ts の CONFIG_FILENAMES パスを更新

### 実測後に決定
- [ ] 14. Figma MCP の呼び出し粒度
- [ ] 15. Component バッチの上限
- [ ] 16. ブラウザ MCP の安定性と使い方

---

## 決定事項ログ

### #2 harness.ts の plan type 分岐設計
- impl を god コマンドにしない。各フローは独立したサブコマンド
- `design-fe` / `component` / `impl` / `page` を harness.ts のエントリポイントで分岐
- 各フローは独立したクラス（ComponentFlow, ImplFlow, PageFlow）
- ステップの部品化は不要。共通ユーティリティ（LintGuard, ReviewOrchestrator, Runner, Boundary）は既に部品化済み
- 統一入り口が必要なら `run` コマンドを薄いルーターとして追加可能
- harness-guide skill を新設。ハーネス全体（BE/FE共通）の操作ガイドを提供

### #4 プロンプトテンプレート設計方針
- design-fe.md: 1 claude -p で仕様書 + コンポーネント定義書を同時生成
- コンポーネント定義書生成時、デザインシステム（既存コンポーネント + 設定ファイル）をパスで渡し LLM に読ませる
- パスは profile の designSystem 設定から取得（ハーネスはスタイリング手法を関知しない）
- profile 定義例:
  ```yaml
  designSystem:
    components: "frontend/src/components"
    config:
      - "frontend/tailwind.config.ts"
      - "frontend/src/lib/utils.ts"
  ```
- テンプレートの制約部分は .harness/rules/*.md から注入（テンプレート本体には直書きしない）

### #1 実装の優先順位/フェーズ分け
```
Phase 0: Figma MCP 実測
Phase 1: Infrastructure（profile, routing, rules injection, status management）
Phase 2: Design フロー（design-fe-flow.ts, Figma MCP 連携, テンプレート）
Phase 3: Skills + Component フロー（harness-pilot, harness-plan-fe, component-flow.ts, Storybook）
Phase 4: Logic フロー対応（frontend profile, MSW 条件付き注入）
Phase 5: Page UI フロー（page-flow.ts, 3観点レビュー, ブラウザ MCP）
```
- 各 Phase 完了時に Quiz 機能で E2E 検証
- Phase 0 の実測結果が Design フローの設計に影響するため先行必須

### #13 harness-pilot skill
- 名称: harness-pilot（ガイドではなく自律実行する skill）
- BE/FE 共通。ユーザーのゴールを受けてワークフロー全体を自律的に実行
- 判断フロー: 対象特定（BE/FE）→ profile 検証 → 進捗確認 → 次ステップ実行
- profile チェック（.harness.yml の設定が適切か）も pilot が担当
- init との差別化: init = 初期セットアップ案内、pilot = 機能開発の自律実行
- status 管理: needs_input で停止して人間に伝達、ready で次ステップへ進行可能

### #12 /harness-plan-fe skill
- 名称を /plan-fe から /harness-plan-fe に変更（ハーネス用 skill であることを明示）
- トリガー: ready の仕様書パスが渡されたとき
- 手順: 仕様書 + コンポーネント定義書 + Figma キャッシュ → plan 群生成
- 出力: 番号付き plan（01-components, 02-logic-{name}, 最終-page）
- plan 形式は既存互換の Markdown + frontmatter を維持
- 各 plan の frontmatter に `type`, `profile`, `scope`, `spec`, `test_cases`, `component_spec`, `figma_cache`, `msw` を設定
- 本文に `## Targets`, `## Dependencies`, `## Figma Slice` を含める
- dependencies は `name` + `import` を持つリストで設定
- Figma データは元キャッシュ参照パス + 該当ノード抜粋を plan に埋め込む

### #11 コンポーネント定義書テンプレート
- frontmatter に status（ハーネスが自動設定: needs_input / ready）
- 種別列: 新規 / 既存(shadcn) で /harness-plan-fe が作成対象を即判断
- 各コンポーネント: 名前、種別、責務、Props 概要、Figma ノード対応
- 依存関係セクション（親子関係）
- 特記事項セクション（粒度判断の根拠）

### #8-9 review-page-design.md / review-page-behavior.md
- #4d, #4e で決定済み

### #10 .harness/rules/*.md
- rules/component.md: 責務境界（プレゼンテーション責務のみ。API/server state/atom/global state/ビジネスロジック禁止）+ 生成規約（fn component, Tailwind, cn()）+ Story 規約（CSF3, 状態ごと1 Story）
- rules/logic.md: 責務境界（JSX 禁止、.ts のみ）+ MSW 規約（msw: true 時のみ適用、handlers/ 配置、API 契約一致）
- rules/page.md: 責務境界（接続のみ、ロジック/新コンポーネント禁止）+ テスト規約（DOM 非依存、role/API/状態でアサート）

### #7 review-criteria-component.md
- Props: 全型定義、命名規則（is/has/on）
- スタイリング: インラインスタイル禁止、ハードコード色/spacing 禁止、cn() カスタマイズ
- コンポーネント設計: 単一責任、責務境界違反チェック（API/server state/共有状態/ビジネスロジック禁止）
- Story: CSF3 形式、画面状態ごとの Story、fn() 使用

### #6 frontend sourceLayout
```ts
sourceDir: "frontend/src/{{category}}/{{name}}"
testDir: "frontend/src/{{category}}/{{name}}/__tests__"
scopePattern: "frontend/src/{{category}}/{{name}}/*"
```
- category: components, hooks, atoms, api, pages 等
- テストはコロケーション（__tests__/）
- Component plan は `1 feature = 1 batch` を維持し、scope は feature 単位の component 領域を指す
- batch 内の新規作成対象は plan 本文の `## Targets` に列挙して固定する

### #5 Storybook 設定と Story 生成パターン
- Storybook 10.x、CSF3 形式（satisfies Meta<typeof Component>）
- ファイル配置: コロケーション（ComponentName.stories.tsx）
- カバレッジ: 全組み合わせではなく、ユーザーが実際に遭遇する画面状態ごとに 1 Story
  - Default + 各 variant + 各実用的な状態 + エッジケース
  - CSS 疑似クラス（hover/focus）は Story 不要
  - 実際に起きない組み合わせは Story 不要
- コールバック Props には fn() を使用
- loading / error / empty / selected / open などの状態は props と局所 UI state で再現する
- Component Story では MSW を使わない
- テスト: Vitest addon（@storybook/addon-vitest）。旧 test-runner は非推奨
- shadcn/ui: グローバル CSS import + @storybook/addon-themes でダークモード
- Story 生成ルールは rules/component.md に含める

### #4a Design フロープロンプト（design-fe.md）+ 仕様テンプレート更新
- 仕様書の「API 連携」セクションにキャッシュ戦略・mutation 後の振る舞いを含めるよう定義:
  ```markdown
  ## 機能要件（UX から導出）
  - API 連携:
    - エンドポイント、メソッド、用途
    - キャッシュ戦略（キャッシュ有無、TTL、無効化タイミング）
    - mutation 後の再取得方針（楽観的更新 / サーバー再取得）
  ```
- design-fe.md のプロンプトに「API 連携にはキャッシュ戦略と mutation 後の振る舞いを含めること」と制約追加

### #4a-original Design フロープロンプト（design-fe.md）
- 1 claude -p セッションで仕様書 + コンポーネント定義書を同時生成
- Figma キャッシュを1回だけコンテキストに載せ、2つの成果物を出力
- プロンプトは「成果物1: 仕様書」「成果物2: コンポーネント定義書」で構造的に分離
- ステータス管理: ハーネスが [要確認] タグの有無で status を自動設定
  - needs_input: [要確認] あり（人間の追記待ち）
  - ready: [要確認] なし（LLM 観点で進行可能。人間は異議があれば修正して再実行）
- ready は「次工程へ進める状態」を意味し、人間最終承認を意味しない
- この status 管理は BE/FE 共通の改善として適用可能

### #4e review-page-behavior.md
- 仕様書に記載された動作要件のみをレビュー対象とする
- 観点: 状態遷移、a11y 要件、仕様記載のレンダリング要件、エラー/ローディング/空データ状態
- API キャッシュ戦略・mutation 後の再取得は仕様書の API 連携セクションに定義 → 動作品質で検証
- 不要な再レンダリング等の実装最適化は対象外（コード品質レビューの責務）
- UX に影響するもの → 仕様 → 動作品質レビュー
- UX に影響しない実装品質 → review-criteria → コード品質レビュー

### #4d review-page-design.md
- LLM レビューの観点は「Figma データと照合可能なもの」に限定
- 要素欠落、トークン使用、レイアウト構造、spacing/padding/gap/色/フォントの値一致
- Figma の数値 vs Tailwind クラスのデータ照合（ピクセル見た目比較ではない）
- ブラウザレンダリング固有の差異は対象外（ブラウザ MCP + 人間が担当）
- severity は通常通り critical / major / minor

### #4c page-generate.md
- 入力: 仕様書 + Figma デザインデータ + デザインシステムパス
- 依存コンポーネント/hooks は plan に `name` + `import` を記載
- LLM は plan の import 情報を正として使い、必要に応じて実ファイルを読んで型を確認する
- plan フォーマットの dependencies に components/hooks の structured list を追加
- 特別なステップは不要、LLM の通常動作として処理

### #4b component-generate.md（Story 生成を統合）
- 入力: コンポーネント定義書 + Figma デザインデータ + デザインシステムパス
- 1 claude -p セッションでコンポーネント + Story を同時生成
- story-generate.md は不要（component-generate.md に統合）
- Story に関するルールも rules/component.md に含める
- 制約は {{rules}} で注入、テンプレート本体は簡潔に

### #3 MSW ハンドラ生成のトリガーと仕組み
- MSW 生成はフローの独立ステップにしない
- /harness-plan-fe が API 呼び出しの有無を判断し、plan に `msw: true/false` フラグを付与
- `msw: true` の場合のみ:
  - テスト生成テンプレートに MSW server セットアップ + handler import を注入
  - 実装フェーズで hook と一緒に MSW ハンドラを生成（frontend/src/mocks/handlers/）
  - 実装レビューに「MSW ハンドラが API 契約と一致しているか」の観点を追加
  - Boundary の additionalAllowedPrefixes に mocks/handlers/ を追加
- MSW の適用対象は Logic plan と、必要な Page UI plan のみ
- Component plan では MSW に触れず、Story は props ベースで状態再現する
- `msw: false` の場合は MSW に一切触れない（トークン効率）
- RED はハンドラ未実装の import エラーで失敗。GREEN で hook + ハンドラが揃って通過

---

## 計画ファイル転記（.claude/plans/cosmic-exploring-naur.md の内容）

※ 以下は議論開始時点の計画ファイルの内容。議論で決定した事項と齟齬がある場合は上記の決定事項ログが正。

---

# フロントエンド向けハーネスフロー設計

## Context

バックエンド向けの TDD ハーネスフロー（design + impl）は完成済み。
フロントエンドでは対象の性質が異なる（視覚的成果物、コンポーネント合成、状態管理等）ため、
バックエンドと同じフロー構造では粒度・コスト・レビュー精度の面で合わない。
フロントエンド専用のフロー定義と、ライブラリとしてのエントリポイント設計が必要。

---

## 全体アーキテクチャ

```
┌──────────────────────────────────────────────────────┐
│ Design フロー（feature 単位、1 run で完結）             │
│   入力: Figma URL + テキスト要件                       │
│   処理: Figma MCP で全データ取得・キャッシュ             │
│         + 仕様書生成 + コンポーネント定義書生成          │
│   出力: 仕様書 + コンポーネント定義書 + Figma キャッシュ │
│   → ready なら plan 生成へ進行可能。人間は異論があれば差し戻し可能 │
└───────────────────────┬──────────────────────────────┘
                        │
┌───────────────────────▼──────────────────────────────┐
│ Plan 生成スキル（/harness-plan-fe）                     │
│   入力: ready の仕様書 + コンポーネント定義書            │
│         + Figma キャッシュ                             │
│   処理: 実装単位に分解、Figma 詳細データを plan に埋め込み│
│   出力: 実装 plan 群（Component / Logic / Page UI）     │
│   → 人間が確認・調整                                   │
└───────────────────────┬──────────────────────────────┘
                        │
┌───────────────────────▼──────────────────────────────┐
│ Implementation（plan 単位で個別実行）                   │
│   Component plan → Component フロー                   │
│   Logic plan     → Logic フロー（= BE impl フロー）    │
│   Page UI plan   → Page UI フロー                     │
│   各 plan = 1 run = 1 LLM セッション                  │
│   ルール: plan の type に応じて .harness/rules/*.md を  │
│          自動注入                                      │
└──────────────────────────────────────────────────────┘
```

### 粒度ルール
- **Design**: feature 単位（≒ ページ単位）。1 feature = 1 仕様書 + 1 コンポーネント定義書
- **Plan 生成**: 仕様書 + コンポーネント定義書から実装単位に自動分解
- **Implementation**: plan 単位。1 plan = 1 run。人間が順に実行

### Plan の粒度ルール
| plan 種別 | 粒度 | 理由 |
|---|---|---|
| Component | 1 feature 分のコンポーネント群をまとめて 1 plan | プレゼンテーション責務はまとめて扱えるためバッチ可能 |
| Logic | 1 hook/atom = 1 plan | フル TDD + レビューがあるので個別実行 |
| Page UI | 1 page = 1 plan | 組み立て + 3観点レビュー |

### 人間のワークフロー
```bash
tdd-harness design-fe <feature> "<要件>" --figma <url>  # 1. 仕様生成 → ready / needs_input 判定
/harness-plan-fe docs/spec/features/quiz.md              # 2. plan 群を対話的に生成
tdd-harness component plans/quiz/01-components.md        # 3. plan を順に実行
tdd-harness impl plans/quiz/02-logic-use-quiz.md
tdd-harness impl plans/quiz/03-logic-quiz-atom.md
tdd-harness page plans/quiz/04-page.md
```

---

## 設計判断（確定）

- **フロー構成**: フロントエンド専用フローを新設（Component, Page UI）。Logic は既存 impl フロー + frontend profile
- **CLI エントリポイント**: 各フローは独立したサブコマンド（design-fe / component / impl / page）
- **Design フロー**: 1 claude -p で仕様書 + コンポーネント定義書を同時生成。Figma データも同セッションで取得・キャッシュ
- **仕様構造**: UX 要件を起点に機能要件を導出。Figma は見た目の正解データ
- **Plan 生成**: Claude Code skill（/harness-plan-fe）として提供
- **ルール注入**: plan の type に応じてハーネスが `.harness/rules/*.md` を自動注入
- **レビュー戦略**: 観点ごとにステップを分離し、各ステップの観点を1つに限定
- **仕様駆動レビュー**: レビューは仕様記載範囲のみを対象
- **Figma データ取得**: Design フローで一括取得・キャッシュ。URL 共有は1回のみ
- **ステータス管理**: ハーネスが [要確認] タグの有無で needs_input / ready を自動設定
- **MSW**: plan に msw: true/false フラグ。true 時のみ MSW 関連を注入
- **デザインシステム参照**: profile の designSystem 設定からパスを取得、LLM に読ませる
- **harness-pilot**: BE/FE 共通のワークフロー自律実行 skill
- **plan 形式**: 既存互換の Markdown + frontmatter。軽い機械項目は frontmatter、依存関係と Figma 抜粋は本文に置く

---

## Design フロー

### 入力
```bash
tdd-harness design-fe features/quiz "クイズページ。ユーザーが問題に回答し、スコアを確認できる" --figma <url>
```

### フロー構造
```
LLM セッション（claude -p、allowedTools に Figma MCP + Read/Write を含む）:

  1. Figma MCP でデータ取得 → ローカルキャッシュ保存
     → docs/design/features/quiz/ に保存

  2. キャッシュ + 要件テキスト → 仕様書 + コンポーネント定義書を同時生成
     → docs/spec/features/quiz.md
     → docs/design/features/quiz/components.md

  3. ハーネスが [要確認] タグの有無を検査
     → あり: status: needs_input → 人間が追記して再実行
     → なし: status: ready → 次ステップへ進行可能

再実行時（needs_input だった場合）:
  LLM が人間の追記を検証 + 清書 → ready or needs_input に再判定
```

### ステータス遷移
```
needs_input → ready                 （人間が追記 → LLM 検証通過）
needs_input → needs_input           （未解消で差し戻し）
直接 ready                          （[要確認] なし）
ready → needs_input                 （人間が異議あり修正して再実行）
```

---

## フロントエンド仕様テンプレート

```markdown
# {Feature}

## UX 要件
- ユーザーは○○できる
- ○○すると△△が表示される
- ○○の結果は□□に反映される

## 機能要件（UX から導出）
- 状態遷移: UX 要件を満たすために必要な画面状態
- API 連携:
  - エンドポイント、メソッド、用途
  - キャッシュ戦略（キャッシュ有無、TTL、無効化タイミング）
  - mutation 後の再取得方針（楽観的更新 / サーバー再取得）
- 状態管理: UX 要件を満たすために必要な状態保持
- a11y: UX 要件の操作をキーボード等でも保証
- レンダリング: UX 体験を損なわないための最適化

## スコープ外

## Figma 参照
docs/design/{scope}/
```

---

## コンポーネント定義書テンプレート

```markdown
---
status: needs_input | ready
feature: {featureName}
---

# {Feature} コンポーネント定義

## コンポーネント一覧
| 名前 | 種別 | 責務 | Props 概要 | Figma ノード |
|---|---|---|---|---|
| QuizCard | 新規 | 問題文と選択肢の表示 | question, options, onAnswer | node-id-xxx |
| Button | 既存(shadcn) | 回答送信ボタン | - | - |

## 依存関係
## 特記事項
```

---

## frontend plan テンプレート

```markdown
---
type: component | impl | page
profile: frontend
scope: {scope}
spec: docs/spec/features/{feature}.md
test_cases: tests/test-cases/features/{feature}.md
component_spec: docs/design/features/{feature}/components.md
figma_cache: docs/design/features/{feature}/figma.json
msw: true | false
---

## 今回やること

## Targets
- Component plan の新規作成対象を列挙

## Dependencies
- name: QuizCard
  import: "@/components/quiz/QuizCard"
- name: useQuiz
  import: "@/hooks/useQuiz"

## Figma Slice
- 対象ノードの抜粋

## 対象テストケース

## やらないこと

## 完了条件

## 設計判断
```

---

## フロー間の責務境界ルール

| フロー | 出力 | 許可される内容 | 禁止される内容 |
|---|---|---|---|
| Component | `.tsx` + Story | 描画、Props に基づく表示分岐、局所 UI state、プレゼンテーションロジック | API、server state、atom/global state、ビジネスロジック |
| Logic | `.ts` + テスト | hooks / atoms / API クライアント | JSX、コンポーネント定義 |
| Page UI | `.tsx` + テスト | Component + Logic の接続、ページ構成、レイアウト | ロジック直接実装、新コンポーネント定義 |

判断基準: テストすべきロジック → Logic フロー、外部依存 → 必ず Logic フロー

---

## 3 実装フロー定義

### 1. Component フロー
- 1 claude -p でコンポーネント + Story を同時生成
- ルール注入: .harness/rules/component.md
- 対象はプレゼンテーション責務のみ。局所 UI state と表示分岐は含めてよい
- TDD なし。品質ゲート: Storybook + 人間
- レビュー: review-criteria-component.md（セルフレビュー1回）

### 2. Logic フロー（既存 impl フロー + frontend profile）
- バックエンドと同一のフロー構造
- ルール注入: .harness/rules/logic.md
- MSW: plan の msw フラグが true の場合のみ、実装フェーズで hook と一緒に生成
- テスト生成時に MSW server セットアップ + handler import を含める

### 3. Page UI フロー
- ルール注入: .harness/rules/page.md
- 依存コンポーネント/hooks は plan に `name` + `import` で記載し、LLM はそれを正として配線する
- 3観点レビュー:
  - デザイン忠実性: Figma データとの照合（要素欠落、トークン、spacing/色/フォント一致）
  - 動作品質: 仕様書の動作要件のみ（状態遷移、a11y、API キャッシュ/mutation）
  - コード品質: review-criteria-frontend.md（パフォーマンス含む）
- ブラウザ MCP + 人間確認が最終ゲート

---

## Figma 連携

- Design フローで一括取得・キャッシュ（URL 共有1回のみ）
- 以降のフローはローカルキャッシュ参照
- 呼び出し粒度は実測後に決定
- レート制限: 200/日、15/分

---

## 共有インフラ

### MSW ハンドラ
- frontend/src/mocks/handlers/ に配置
- additionalAllowedPrefixes で書き込み許可
- msw: true の Logic/Page plan でのみ関与

### Storybook
- 10.x、CSF3 形式、コロケーション
- 画面状態ごとに 1 Story（全組み合わせ不要）
- Vitest addon でテスト
- Component Story は props ベースで状態再現し、MSW は使わない

### デザインシステム
- profile.designSystem.components: 既存コンポーネントパス
- profile.designSystem.config: 設定ファイルパス群
- ハーネスはスタイリング手法を関知しない

---

## 実装フェーズ

```
Phase 0: Figma MCP 実測
Phase 1: Infrastructure（profile, routing, rules injection, status management）
Phase 2: Design フロー（design-fe-flow.ts, Figma MCP 連携, テンプレート）
Phase 3: Skills + Component フロー（harness-pilot, harness-plan-fe, component-flow.ts, Storybook）
Phase 4: Logic フロー対応（frontend profile, MSW 条件付き注入）
Phase 5: Page UI フロー（page-flow.ts, 3観点レビュー, ブラウザ MCP）
```
各 Phase 完了時に Quiz 機能で E2E 検証。

---

## 実装対象ファイル

### 新規作成
- `.harness/src/design-fe-flow.ts`
- `.harness/src/component-flow.ts`
- `.harness/src/page-flow.ts`
- `.harness/rules/component.md`
- `.harness/rules/logic.md`
- `.harness/rules/page.md`
- `.harness/templates/design-fe.md`
- `.harness/templates/component-generate.md`（Story 生成を統合、story-generate.md は不要）
- `.harness/templates/page-generate.md`
- `.harness/templates/review-page-design.md`
- `.harness/templates/review-page-behavior.md`
- `.harness/templates/review-criteria-component.md`
- `docs/spec/TEMPLATE-frontend.md`
- `docs/design/TEMPLATE-components.md`
- `.claude/skills/harness-plan-fe/SKILL.md`
- `.claude/skills/harness-pilot/SKILL.md`

### 変更
- `.harness/src/harness.ts` — design-fe / component / page サブコマンド追加
- `.harness/src/config.ts` — frontend profile + designSystem 定義
- `.harness/src/steps.ts` — フロントエンド用ステップ定数
- `.harness.yml` — frontend profile 追加
- `.harness/src/boundary.ts` — frontend sourceLayout パターン

### 既存流用
- `.harness/src/impl-flow.ts` — Logic フロー
- `.harness/src/review-orchestrator.ts` — レビューサイクル
- `.harness/src/lint-guard.ts` — eslint + tsc アダプタ
- `.harness/src/runner-registry.ts` — ルール注入拡張
