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

## App Server に持ち込む内容

### 1. step-level execution policy を server の責務にする

- `test_generate` は
  - 読み取り可能: spec、approved test cases、target test file、target implementation file、言語設定ファイル
  - 書き込み可能: target test file のみ
- `test_self_quality` は
  - 読み取り可能: target test file、approved test cases、spec、直近実行結果
  - 書き込み不可
- `apply_fixes` は
  - 読み取り可能: target files、spec、approved test cases、直近 review 結果、直近 lint/test 結果
  - 書き込み可能: target files のみ
- side-effect file は profile ごとの明示設定で 1 件ずつ許可する。`backend/uv.lock` のようなファイルはこの例外で扱う。

理由:
- prompt で「探索するな」と書いても、実際には `rg --files backend/benchmark` のような探索が先に走っている。
- 制御したいのはプロンプト文言ではなく、実行権限そのもの。

### 2. canonical command の決定権をモデルから剥がす

- `pytest` / `ruff` / `mypy` / `uv` / `.venv/bin/pytest` を reviewer に探させない。
- app-server が profile から canonical command を解決し、実行結果だけをモデルへ渡す。
- これにより reviewer は
  - 実行方法探索
  - pyproject / venv / lockfile の発見
  を毎周繰り返さずに済む。

理由:
- 今回の run では review ループが、品質判断よりも実行環境探索に token を使っている。
- モデルに任せるべきなのは「何が悪いか」「どう直すか」であって、「どう起動するか」ではない。

### 3. target-file-first を native rule として強制する

- `test_generate` は主対象テストファイルに一定時間内で write が発生しなければ reject する。
- target file に最初の write が起こる前の repo 横断探索は violation として扱う。
- target implementation file の参照は、import / public contract 確認に必要な最小限に制限する。

理由:
- benchmark 専用チューニングの中で、唯一そのまま本番に昇格させる価値が高いのがこの規律。
- 実際に `preTargetExplorationObserved: true` が残っており、これは benchmark だけの問題ではなく通常運用でも無駄。

### 4. post-step validation を app-server 側の固定処理にする

- 各 step の直後に server が以下を実行する。
  - target file が更新されたか
  - lint/type/test が通るか
  - allowed scope 外の変更がないか
  - approved case 件数から大きく逸脱していないか
- validation 結果だけを次 step へ渡す。

理由:
- 今の harness は validation の考え方自体は正しいが、一部が benchmark 専用分岐に埋まっている。
- validation は benchmark のためではなく、本番でも必要な品質ゲート。

### 5. review loop を full-context 再送から diff-centered 再評価へ変える

- 2 周目以降の review は
  - 前回指摘
  - 今回差分
  - 直近 lint/test 結果
  のみを主入力にする。
- spec 全文、criteria 全文、対象ファイル全文を毎周再送する構造はやめる。
- `judgment_summary` はレポート用途のため、実装修正ループから切り離す。

理由:
- 現状は `test_self_quality -> apply_fixes -> judgment_summary` の往復が長く、4 回目 `apply_fixes` では `inputTokens: 769102` に達している。
- 品質ゲートとレポート生成を同じ loop に乗せるべきではない。

## benchmark 専用チューニングの扱い

### 本番フローへ昇格させるもの

- target-file-first の規律
- post-step validation
- `primaryTargetFileTouched` / `preTargetExplorationObserved` のような observability

これらは benchmark 固有ではなく、本番でも品質と token 効率の両方に効く。

### benchmark runner の外側へ追い出すもの

- placeholder reset
- placeholder 置換の強制
- `ALREADY_GREEN` を benchmark だけ失格にする処理
- `Generation Benchmark Discipline` のような benchmark 名指しの prompt

これらは採点条件や fixture 準備であって、`impl` フロー本体の責務ではない。

### 結論

- app-server 移行後の本番フローは 1 本にする。
- benchmark はその同一フローを clean worktree と固定 fixture 上で走らせ、外側の runner が採点する。
- つまり移行先で強化すべきなのは benchmark 専用分岐ではなく、本番にも効く execution policy である。

## 移行判断

- harness の品質 policy 自体は維持する。
- ただし execution control は SDK prompt ではなく app-server native control に寄せる。
- 移行理由は「モデルを変えたいから」ではなく、
  - prompt 依存の scope 制御では限界が見えた
  - 実行環境探索を止められない
  - review loop の token 膨張を execution layer でしか抑えられない
  ためである。

## 補足

- この run は手動停止した。失敗理由は scope guard ではなく、review loop の長時間継続。
- 本メモは app-server 設計入力用であり、SDK 側の最終評価書ではない。
