# App Server 移行メモ: Backend Benchmark 実走知見

目的:
- SDK ベース harness の実走で何が改善し、何が残ったかを移行設計の入力として残す
- app-server 側で何を native に強制すべきかを明確にする

対象 run:
- archived artifacts: [docs/plans/artifacts/app-server-migration/2026-05-15T09-22-25_impl_benchmark_markdown-toc/harness.jsonl](/Users/tsuryoryo/Desktop/repo/obsidian/docs/plans/artifacts/app-server-migration/2026-05-15T09-22-25_impl_benchmark_markdown-toc/harness.jsonl)
- archived checkpoint: [checkpoint_impl_benchmark_markdown-toc.json](/Users/tsuryoryo/Desktop/repo/obsidian/docs/plans/artifacts/app-server-migration/checkpoint_impl_benchmark_markdown-toc.json)
- plan: [plan/benchmark-markdown-toc-generation.md](/Users/tsuryoryo/Desktop/repo/obsidian/plan/benchmark-markdown-toc-generation.md)

## 事実

- `backend/uv.lock` を `allowedSideEffectFiles` に分離したことで、`uv.lock` 起因の scope guard failure は出なくなった。
- dirty な本体 worktree ではなく clean な一時 worktree を使うことで、`.claude/*` や `.harness/*` の既存差分が guard に混ざる問題は出なくなった。
- `test_generate` は 1 回で通過した。
  - `targetTestFileMaterialized: true`
  - `targetTestIntentCount: 23`
  - `approvedCaseCount: 23`
  - `postGenerateLintPassed: true`
- `test_generate` の token はまだ大きい。
  - `inputTokens: 263761`
  - `cacheReadInputTokens: 91904`
- `test_generate` 前の探索はまだ残っている。
  - `preTargetExplorationObserved: true`
  - 最初の non-write command は `rg --files backend/benchmark`
- review ループは scope/lockfile 起因では止まらず、純粋に `test_self_quality -> apply_fixes -> judgment_summary` で長く回った。
- 手動停止時点の usage 回数:
  - `test_generate`: 1
  - `test_self_quality`: 4
  - `apply_fixes`: 4
  - `judgment_summary`: 4
- `apply_fixes` 後の lint は毎回 1 回で通った。
  - `lint_passed attempt=1`
- 以前の failure mode だった
  - `backend/uv.lock` による guard failure
  - 同一 lint を 5 回再確認して落ちる
  は再現しなかった。

## 今回確認できた改善

- side-effect file の許可を profile 専用設定へ分ける設計は正しかった。
- clean worktree 前提での benchmark 実行条件は整理できた。
- `test_generate` の fidelity と lint 収束は前進した。
- review ループ内 lint repair は機能している。

## まだ残っている問題

- `test_generate` でも target file 書き込み前の探索は残る。
- `test_self_quality` が review ではなく、実行環境探索まで抱えている。
- reviewer が毎周
  - `pytest`
  - `ruff`
  - `mypy`
  - `uv`
  - `.venv`
  - `pyproject.toml`
  を探り直している。
- その結果、review 1 周ごとの token と時間が大きい。
  - 例: 4 回目 `apply_fixes` は `inputTokens: 769102`
- loop 制限は壊れていないが、1 step あたり最大 5 周なので、収束性が悪いと run 全体はかなり長くなる。
- 手動停止時点でも checkpoint は `test_generated` のままで、`impl_generate` まで到達していない。

## 原因の見立て

- SDK 直結では read/write scope が prompt 依存で、探索そのものを native に拒否できない。
- review prompt に実行環境診断の責務が残っている。
- harness 側が canonical command を固定して返すより、reviewer 自身に実行方法探索をさせている。
- 2 周目以降も full-file review に近く、差分中心の収束モードに切り替わっていない。

## App Server で強制したいこと

- step ごとの read scope を native に制限する。
  - `test_generate`: target test file、target impl file、approved cases、spec のみ
  - `test_self_quality`: target test file、approved cases、spec、直近実行結果のみ
- step ごとの write scope を native に制限する。
  - `apply_fixes`: target file のみ
  - side-effect file は profile 設定で明示許可された単一ファイルだけ
- canonical command を server 側で固定する。
  - reviewer に `pytest` / `uv run pytest` / `.venv/bin/pytest` を探させない
  - server が実行して stdout/stderr を渡す
- target-file-first の順序を server 側で強制する。
  - `test_generate` は target file 更新前の repo 横断探索を reject する
- post-step validation を server 側で強制する。
  - target file rewrite
  - placeholder 置換
  - lint/type/test 実行
  - approved case 件数の heuristic check
- review の 2 周目以降は diff 中心の再評価モードへ切り替える。

## ADR に持ち込むべき論点

- SDK 側改善で回収できた範囲
  - side-effect file 設計
  - test generation fidelity
  - lint repair
- それでも残る構造限界
  - prompt 依存の scope
  - 実行環境探索の抑止不能
  - review loop の高トークン化
- app-server に寄せる理由
  - モデル変更ではなく execution control の強化が本命だから

## 補足

- この run は手動停止した。失敗理由は scope guard ではなく、review loop の長時間継続。
- 本メモは app-server 設計入力用であり、SDK 側の最終評価書ではない。
