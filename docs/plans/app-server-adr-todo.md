# App Server ADR TODO

目的:
- SDK ベースの harness 運用で残る制御限界を検証結果として確定する
- 検証完了後に、app-server 移行判断の ADR を起票する

ステータス:
- [ ] backend benchmark の現行 run が終了している
- [ ] run 結果の事実確認が完了している
- [ ] ADR ドラフトを作成している

## 検証完了後に確認する項目

- [ ] end-to-end で完走したか
- [ ] `test_generate` の `targetTestIntentCount` と `approvedCaseCount` が一致しているか
- [ ] `test_generate` の `preTargetExplorationObserved` が残っているか
- [ ] `test_generate` の `inputTokens` / `cacheReadInputTokens` が依然として大きいか
- [ ] `apply_fixes` 後の lint が自動再修正で収束しているか
- [ ] review / fix の総サイクル数が以前より減っているか
- [ ] 最終的な失敗理由が lint 再確認ループではなくなっているか

## ADR に入れる論点

- [ ] 背景
  - Codex SDK ベースの backend harness で何が問題だったか
- [ ] SDK 側で先に実施した改善
  - context bundle 分離
  - file scope 縮小
  - placeholder reset
  - prompt 強化
  - heuristic gate
  - review loop lint repair
  - stall fallback
- [ ] 改善して解消した点
  - approved case 膨張の抑制
  - post-generate lint 収束
  - review-loop lint 再確認死の改善
- [ ] SDK でなお残った限界
  - prompt 依存の file/read scope
  - target-file-first を native に強制できない
  - pre-target exploration が止め切れない
  - review turn の文脈肥大
- [ ] 判断
  - harness の品質 policy は維持する
  - 実行制御は app-server 側へ寄せる
- [ ] app-server に期待する責務
  - step-level read/write policy enforcement
  - target-file-first execution enforcement
  - server-side placeholder reset
  - post-step artifact validation
  - deterministic repair loops

## ADR 作成の出口条件

- [ ] ログと実測値を引用できる
- [ ] SDK 継続案と app-server 移行案の比較が書ける
- [ ] 「なぜ今移すのか」を benchmark 実測で説明できる
