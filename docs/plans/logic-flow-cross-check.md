# Codex 計画 vs 実コード vs Logic フロー計画 照合

## 照合表

| 項目 | Codex 計画 | 実コード | Logic 計画 |
|---|---|---|---|
| TaskPlan 拡張 | type/profile/scope/spec + FE 固有フィールド | 実装済み | 変更不要 |
| plan-parser | Targets/Dependencies/Figma Slice パース | 実装済み | 変更不要 |
| designSystem path bundle | config.ts に追加 | 未実装 | スコープ外（Logic では不要） |
| frontend scope ガード | 撤去して frontend logic 対応 | 未撤去（明示拒否中） | **対応する**（boundary.ts L143-146 削除） |
| status needs_input/ready | 全箇所統一 | component/page は対応済み、boundary/design-flow は未対応 | **対応する**（boundary.ts L167,171 + design-flow.ts L50,68） |
| rules/ ディレクトリ | component/logic/page の3ファイル | 未実装（ディレクトリなし） | **logic.md を作成** |
| ルール注入の仕組み | plan type → rules → appendSystemPrompt | 未実装 | **impl-flow.ts に resolveRulesContent 追加** |
| MSW 条件付き注入 | msw フラグで切替 | plan に msw フィールドあるが注入ロジックなし | **テンプレートに {{mswInstructions}} 追加** |
| frontend profile | .harness.yml に追加 | 未追加（backend のみ） | **.harness.yml に frontend profile 追加** |
| Component フロー | プレゼンテーション責務 | 実装済み | 触らない |
| Page フロー | 3観点レビュー + ブラウザ MCP | 実装済み | 触らない |

## 詳細

### 実装済み（変更不要）
- **types.ts**: TaskPlan に type, profile, scope, specPath, testCasesPath, componentSpecPath, figmaCachePath, msw, targets, dependencies, figmaSlice, browserScenarios すべて存在
- **plan-parser.ts**: Targets, Dependencies（name+import）, Figma Slice, Browser Scenarios パース済み。type ごとの必須検証は component-flow.ts と page-flow.ts に個別 validateXxxPlan あり
- **component-flow.ts**: プレゼンテーション責務を正しく制約。Story smoke テスト、target ごとの処理、isReadyLikeStatus で ready/approved 両対応
- **page-flow.ts**: 3観点レビュー + ブラウザ MCP 検証。validatePagePlan で全必須フィールド検証。isReadyLikeStatus 対応済み
- **review-criteria-component.md**: プレゼンテーション責務の基準記載済み

### 未実装（Logic フロー計画でカバー）
1. **boundary.ts フロントエンド scope ガード**（L143-146）: `plan.scope.startsWith("frontend")` で明示拒否中 → 削除する
2. **boundary.ts status チェック**（L167, L171）: `approved` のみ → ready/approved 両対応に
3. **design-flow.ts status チェック**（L50, L68）: `approved` のみ → ready/approved 両対応に
4. **rules/logic.md**: .harness/rules/ ディレクトリ自体が未作成 → 新規作成
5. **ルール注入**: impl-flow.ts に plan type → rules ファイル → appendSystemPrompt の仕組みなし → resolveRulesContent メソッド追加
6. **MSW 条件付き注入**: plan に msw フィールドは存在するが、テンプレートへの注入ロジックなし → {{mswInstructions}} プレースホルダー追加
7. **.harness.yml frontend profile**: backend profile のみ → frontend profile 追加

### 未実装（Logic フロー計画のスコープ外）
- **config.ts designSystem path bundle**: Logic フローではデザインシステム参照不要。Component/Page フローで必要になった時に別途対応
- **rules/component.md, rules/page.md**: 今回は logic.md のみ作成。component/page のルール注入は各フロー実装時に対応（ただし現時点で component-flow/page-flow はルール注入なしで動作している）
- **harness-plan-fe, harness-pilot skill**: skill は別 Phase

### ステータス対応箇所の全体マップ

| ファイル | 行 | 現状 | 対応 |
|---|---|---|---|
| component-flow.ts | L155-157 | ready/approved 両対応 | 対応済み |
| page-flow.ts | L216-217 | ready/approved 両対応 | 対応済み |
| boundary.ts | L167 | approved のみ | **今回対応** |
| boundary.ts | L171 | approved のみ | **今回対応** |
| design-flow.ts | L50 | approved のみ | **今回対応** |
| design-flow.ts | L68 | approved のみ | **今回対応** |
