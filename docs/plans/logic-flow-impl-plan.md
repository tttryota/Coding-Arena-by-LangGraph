# Logic フロー実装計画

## Context

フロントエンド向けハーネスフローの Phase 4。Component フローは実装済み。
Logic フロー（hooks / Jotai atoms / API クライアント）は **既存 ImplFlow をそのまま使い、frontend profile で動かす** 方針。
新しい LogicFlow クラスは作らない。必要なのは設定追加・ルール注入・MSW 対応のみ。

議論トラッカー: `docs/plans/frontend-harness-discussion.md`

---

## 現状分析

### 既に存在するもの
- `ImplFlow` — バックエンド用の TDD フロー（テスト生成 → RED → 実装 → GREEN → レビュー）。完全に動作中
- `harness.ts` の `impl` コマンド — plan を読み、profile を解決し、ImplFlow を起動
- `plan-parser.ts` — `type`, `profile`, `msw`, `dependencies` 等のフロントエンド用フィールドを既にパース済み
- `steps.ts` — ImplFlow が使うステップ定数（TEST_GENERATE, IMPL_GENERATE 等）は既存
- `review-criteria-frontend.md` — フロントエンド用レビュー基準（React/shadcn/Tailwind/Jotai）
- `review-criteria-common.md` — 共通レビュー基準
- `tool-adapter.ts` — eslint, tsc, vitest のアダプタ定義済み

### 不足しているもの
1. `.harness.yml` に frontend profile がない
2. `boundary.ts` がフロントエンド scope を明示拒否している（L143-146）
3. `boundary.ts` / `design-flow.ts` の status チェックが `approved` のみ（`ready` 未対応）
4. `.harness/rules/logic.md` が存在しない（ルール注入の仕組みも未実装）
5. MSW 条件付き注入の仕組みがない（`msw: true` 時のテンプレート切替）

---

## 実装内容

### 1. frontend profile を `.harness.yml` に追加

```yaml
profiles:
  backend:
    # ... 既存のまま

  frontend:
    lint: [eslint, tsc]
    test: vitest
    toolRoot: frontend
    criteriaPreset: frontend
    sourceLayout:
      sourceDir: "frontend/src/{{category}}/{{name}}"
      testDir: "frontend/src/{{category}}/{{name}}/__tests__"
      scopePattern: "frontend/src/{{category}}/{{name}}/*"
      additionalAllowedPrefixes: ["docs/reviews/", "frontend/src/mocks/handlers/"]
```

**ファイル**: `.harness.yml`
**変更内容**: `profiles.frontend` ブロックを追加

---

### 2. boundary.ts のフロントエンド scope 対応

現在 `implementationGuard` が `plan.scope.startsWith("frontend")` でフロントエンド scope を拒否している（`.harness/src/boundary.ts:143-146`）。

また status チェックが `approved` のみ（L167, L171）だが、Codex 計画では `needs_input / ready` に統一する方針。

**変更内容**:

a. フロントエンド scope ガードの削除:
```typescript
// 削除: L143-146
// if (plan.scope.startsWith("frontend")) {
//   throw new GuardError("frontend スコープの impl フローは別フローとして実装予定です。");
// }
```

b. status チェックを `ready` / `approved` 両対応に（component-flow/page-flow の `isReadyLikeStatus` と同様）:
```typescript
// boundary.ts L167
if (specFm.status !== "approved" && specFm.status !== "ready") {
  throw new GuardError(`仕様書が ready ではありません（現在: ${specFm.status ?? "なし"}）`);
}
// boundary.ts L171 も同様
```

**ファイル**: `.harness/src/boundary.ts`

---

### 3. design-flow.ts の status 対応

design-flow.ts も `approved` のみチェックしている（L50, L68）。ready 対応に揃える。

```typescript
// design-flow.ts L50
if (specFm.status !== "approved" && specFm.status !== "ready") {
  console.log("仕様書を確認し、frontmatter の status を ready に更新してから再実行してください。");
  return;
}
// design-flow.ts L68 も同様
```

**ファイル**: `.harness/src/design-flow.ts`

---

### 4. ルール注入の仕組み

#### 4a. `.harness/rules/logic.md` を作成

```markdown
## 責務境界
- JSX 禁止、コンポーネント定義禁止
- 出力は .ts ファイルのみ
- hooks / atoms / API クライアントのみ

## MSW（plan に msw: true がある場合のみ適用）
- MSW ハンドラは frontend/src/mocks/handlers/ に配置
- テストファイルから import して server.use() で適用
- ハンドラのレスポンス形状はバックエンド API の契約と一致させる
```

**ファイル**: `.harness/rules/logic.md`（新規作成）

#### 4b. ImplFlow にルール注入を追加

現在の ImplFlow は `criteriaPreset` に基づいて `review-criteria-*.md` を `appendSystemPrompt` に注入している（`resolveCriteriaPaths` メソッド: `.harness/src/impl-flow.ts:48-99`）。

ルール注入は **同じ仕組みを拡張** して行う:
- plan の `type` フィールドを見て、対応する `.harness/rules/{type}.md` が存在すれば読み込む
- テスト生成・実装生成の `appendSystemPrompt` にルール内容を追加

**ファイル**: `.harness/src/impl-flow.ts`
**変更箇所**:
- 新メソッド `resolveRulesContent(planType)` を追加
- テスト生成ステップ（L157-187）の `appendSystemPrompt` にルール内容を結合
- 実装生成ステップの `appendSystemPrompt` にルール内容を結合

**実装案**:
```typescript
private resolveRulesContent(planType: string | undefined): string {
  if (!planType) return "";
  const root = this.boundary.getProjectRoot();
  const rulesPath = join(root, ".harness", "rules", `${planType}.md`);
  if (!existsSync(rulesPath)) return "";
  return readFileSync(rulesPath, "utf-8");
}
```

テスト生成・実装生成時に:
```typescript
const rules = this.resolveRulesContent(plan.type);
const systemPrompt = [criteria, rules].filter(Boolean).join("\n\n");
```

---

### 5. MSW 条件付き注入

議論の決定事項:
- `msw: true` の場合のみ、テスト生成テンプレートに MSW セットアップ指示を追加
- テスト生成時: MSW server セットアップ + handler import を含むテストコードを生成
- 実装時: hook と一緒に MSW ハンドラを `frontend/src/mocks/handlers/` に生成
- `msw: false` の場合は MSW に一切触れない

**実装方式**: テンプレート変数で制御

#### 5a. テスト生成テンプレートに MSW セクションを追加

`{{mswInstructions}}` プレースホルダーを追加。

**ファイル**: `.harness/templates/test-generate.md`

#### 5b. ImplFlow でテンプレート変数を設定

テスト生成ステップで:
```typescript
const mswInstructions = plan.msw
  ? `## MSW セットアップ
- テストファイルに MSW server のセットアップ (beforeAll/afterEach/afterAll) を含める
- API モック用の handler import を含める（handler ファイルは実装フェーズで生成される）
- handler の配置先: frontend/src/mocks/handlers/
- server.use(...handlers) でモックを適用する`
  : "";
```

同様に `impl-generate.md` にも `{{mswInstructions}}` を追加:
```typescript
const mswImplInstructions = plan.msw
  ? `## MSW ハンドラ生成
- frontend/src/mocks/handlers/ に共有ハンドラファイルを生成する
- ハンドラのレスポンス形状はバックエンド API の契約と一致させる
- テストファイルから import されるパスと一致させる`
  : "";
```

**ファイル**: `.harness/src/impl-flow.ts`, `.harness/templates/impl-generate.md`

#### 5c. additionalAllowedPrefixes

`frontend/src/mocks/handlers/` は frontend profile の `additionalAllowedPrefixes` に含めておく（項目1で設定済み）。動的追加は不要。

---

## 変更対象ファイル

| ファイル | 変更種別 | 変更内容 |
|---|---|---|
| `.harness.yml` | 変更 | frontend profile 追加 |
| `.harness/rules/logic.md` | 新規 | 責務境界 + MSW 規約 |
| `.harness/src/boundary.ts` | 変更 | フロントエンド scope ガード削除（L143-146）、status ready 対応（L167, L171） |
| `.harness/src/design-flow.ts` | 変更 | status ready 対応（L50, L68） |
| `.harness/src/impl-flow.ts` | 変更 | resolveRulesContent メソッド追加、MSW テンプレート変数設定 |
| `.harness/templates/test-generate.md` | 変更 | `{{mswInstructions}}` プレースホルダー追加 |
| `.harness/templates/impl-generate.md` | 変更 | `{{mswInstructions}}` プレースホルダー追加 |

---

## plan 例

Logic フローの plan は `type: impl` で、`profile: frontend` を指定。既存の `tdd-harness impl` コマンドでそのまま動作する。

```bash
tdd-harness impl plans/quiz/02-logic-use-quiz.md
```

```markdown
---
type: impl
profile: frontend
scope: hooks/use-quiz
spec: docs/spec/features/quiz.md
test_cases: tests/test-cases/features/quiz.md
msw: true
---

## 今回やること
useQuiz hook を TDD で実装する

## 対象テストケース
- 問題を取得して返す
- 回答を送信するとスコアが更新される
- エラー時にエラー状態を返す

## やらないこと
- UI コンポーネントの実装
- ページの組み立て

## 完了条件
- 全テストケースが GREEN
- eslint + tsc がパス
- レビュー通過

## 設計判断
- API 呼び出しは fetch ベース
- エラーハンドリングは try-catch + 状態管理
```

---

## Codex 計画との照合

| 項目 | Codex 計画 | 実コード | 本計画 |
|---|---|---|---|
| TaskPlan 拡張 | FE 固有フィールド追加 | 実装済み | 変更不要 |
| plan-parser | body セクションパース | 実装済み | 変更不要 |
| designSystem path bundle | config.ts に追加 | 未実装 | スコープ外（Logic では不要） |
| frontend scope ガード | 撤去 | 未撤去 | **対応する** |
| status needs_input/ready | 全箇所統一 | component/page のみ対応 | **boundary + design-flow を対応** |
| rules/ | 3ファイル作成 | 未実装 | **logic.md を作成** |
| ルール注入 | plan type → rules → appendSystemPrompt | 未実装 | **resolveRulesContent 追加** |
| MSW 条件付き注入 | msw フラグで切替 | フィールドあり/注入なし | **テンプレート変数で注入** |
| frontend profile | .harness.yml に追加 | 未追加 | **追加する** |

---

## 検証方法

### 1. profile 解決の確認
```bash
tdd-harness impl plans/quiz/02-logic-use-quiz.md --no-interactive
# → eslint + tsc + vitest のアダプタが選択されること
# → sourceLayout が frontend/src/hooks/use-quiz/ を指すこと
```

### 2. ルール注入の確認
- ImplFlow のテスト生成・実装生成時に `appendSystemPrompt` に `rules/logic.md` の内容が含まれること

### 3. MSW 条件付き注入の確認
- `msw: true` の plan: テスト生成プロンプトに MSW セットアップ指示が含まれること
- `msw: false` の plan: MSW 関連の指示が一切含まれないこと

### 4. E2E 検証（Quiz 機能）
- `useQuiz` hook を Logic フローで TDD 実装
- テスト生成 → RED → 実装（+ MSW ハンドラ）→ GREEN → レビュー通過
- `frontend/src/mocks/handlers/` にハンドラファイルが生成されること
