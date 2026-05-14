# バックエンド・ハーネス ブラッシュアップ計画

## 目的

バックエンド向けハーネスフローについて、まず現状を正確に把握する。
その上で、以下の 2 つを両立する改善方針を定める。

- トークン効率を上げる
- アウトプット品質を上げる

最終的には、議論結果をもとに実装修正プランへ落とし込む。

前提:

- レビュー工程は重くてよい。ここは品質のために意図的に厚くしている
- 最適化対象は「レビュー回数そのもの」ではなく、「レビューで指摘されにくい実装を最初から出すこと」と「同品質をより少ない無駄で達成すること」
- ただし、レビュー観点にだけ過適合するハックは避ける。改善対象は「レビューで見ている本来の品質」であって、「レビュー通過テクニック」ではない

---

## 1. 現状フローの整理

### Design Flow

入口は `tdd-harness design <category/name> "<requirements>"`。

実装上の流れ:

1. 仕様書を生成
2. 仕様書の frontmatter `status` が `ready` / `approved` であることを人間が確認
3. テストケース文書を生成
4. テストケース文書の `status` を人間が確認
5. impl フローへ進む

参照:

- [.harness/src/design-flow.ts](/Users/tsuryoryo/Desktop/repo/obsidian/.harness/src/design-flow.ts:20)
- 仕様書生成時に `CLAUDE.md` 全文を system prompt に追加: [.harness/src/design-flow.ts](/Users/tsuryoryo/Desktop/repo/obsidian/.harness/src/design-flow.ts:87)
- テストケース生成時は仕様書全文を prompt に埋め込む: [.harness/src/design-flow.ts](/Users/tsuryoryo/Desktop/repo/obsidian/.harness/src/design-flow.ts:125)

### Impl Flow

入口は `tdd-harness impl <plan-file>`。

実装上の流れ:

1. plan を読む
2. spec / test_cases / scope を guard で検証
3. テスト生成
4. lint
5. テストレビュー
6. RED 確認
7. 実装生成
8. lint
9. GREEN 確認
10. 実装レビュー
11. レポート出力

参照:

- [.harness/src/impl-flow.ts](/Users/tsuryoryo/Desktop/repo/obsidian/.harness/src/impl-flow.ts:143)
- テスト生成に spec 全文 + criteria 全文 + rules 全文を投入: [.harness/src/impl-flow.ts](/Users/tsuryoryo/Desktop/repo/obsidian/.harness/src/impl-flow.ts:192)
- 実装生成でも同様に spec 全文 + criteria/rules 全文を投入: [.harness/src/impl-flow.ts](/Users/tsuryoryo/Desktop/repo/obsidian/.harness/src/impl-flow.ts:290)
- lint は生成後・修正後に毎回再実行: [.harness/src/impl-flow.ts](/Users/tsuryoryo/Desktop/repo/obsidian/.harness/src/impl-flow.ts:317), [.harness/src/review-orchestrator.ts](/Users/tsuryoryo/Desktop/repo/obsidian/.harness/src/review-orchestrator.ts:815)

### Review Flow

テストレビュー:

1. self review
2. external review

実装レビュー:

1. self criteria review
2. self quality review
3. external review

各ステップは最大 5 サイクルまで修正と再レビューを繰り返す。

参照:

- [.harness/src/review-orchestrator.ts](/Users/tsuryoryo/Desktop/repo/obsidian/.harness/src/review-orchestrator.ts:635)
- 各レビューで対象ファイル全文を毎回読む: [.harness/src/review-orchestrator.ts](/Users/tsuryoryo/Desktop/repo/obsidian/.harness/src/review-orchestrator.ts:409), [.harness/src/review-orchestrator.ts](/Users/tsuryoryo/Desktop/repo/obsidian/.harness/src/review-orchestrator.ts:974)
- quality/external review で spec 全文を毎回読む: [.harness/src/review-orchestrator.ts](/Users/tsuryoryo/Desktop/repo/obsidian/.harness/src/review-orchestrator.ts:415), [.harness/src/review-orchestrator.ts](/Users/tsuryoryo/Desktop/repo/obsidian/.harness/src/review-orchestrator.ts:449), [.harness/src/review-orchestrator.ts](/Users/tsuryoryo/Desktop/repo/obsidian/.harness/src/review-orchestrator.ts:480)
- 指摘ごとに修正後の「判断理由」を別 LLM 呼び出しで生成: [.harness/src/review-orchestrator.ts](/Users/tsuryoryo/Desktop/repo/obsidian/.harness/src/review-orchestrator.ts:899)

---

## 2. 実測ベースの現状評価

### ベンチマーク成果物のサイズ

`benchmark/markdown-toc` の実データでは:

- spec: 10,366 bytes
- test cases: 3,440 bytes
- plan: 2,216 bytes
- common criteria + backend criteria: 1,750 bytes

参照:

- [docs/spec/benchmark/markdown-toc.md](/Users/tsuryoryo/Desktop/repo/obsidian/docs/spec/benchmark/markdown-toc.md)
- [tests/test-cases/benchmark/markdown-toc.md](/Users/tsuryoryo/Desktop/repo/obsidian/tests/test-cases/benchmark/markdown-toc.md)
- [plan/benchmark-markdown-toc.md](/Users/tsuryoryo/Desktop/repo/obsidian/plan/benchmark-markdown-toc.md)

つまり、レビュー前の時点で「仕様 + テストケース + criteria」だけでかなりの文量がある。
ここに対象コード全文とレビューテンプレートが毎回足されるため、同じ文脈の再送が大きい。

### 実行ログの傾向

`logs/` 配下の `impl_benchmark_markdown-toc` 実行を集計すると:

- 完了 run 11 件
- 外れ値を除いた平均所要時間: 約 26.4 分
- 中央値: 約 25.0 分
- 1 件、約 1009 分まで伸びた run がある

ただしこの 1009 分 run は、スリープ等の外的要因を含んでいる可能性が高く、純粋なハーネス処理時間としては扱わない。
性能評価では wall clock の外れ値そのものより、レビュー回数・再試行回数・lint/test 再実行回数を見るべきである。

その上で、反復の大きかった run では:

- `review_start`: 5 回
- `self_review`: 18 回
- `lint_passed`: 16 回

となっており、生成よりもレビューと再検査のループが支配的だった。
これは問題というより「品質重視の設計思想がそのまま実行時間に表れている」と見るのが正しい。

参照:

- [logs/2026-05-02T23-59-22_impl_benchmark_markdown-toc/harness.jsonl](/Users/tsuryoryo/Desktop/repo/obsidian/logs/2026-05-02T23-59-22_impl_benchmark_markdown-toc/harness.jsonl)
- [docs/reviews/2026-05-03T00-18-55_benchmark_markdown-toc.md](/Users/tsuryoryo/Desktop/repo/obsidian/docs/reviews/2026-05-03T00-18-55_benchmark_markdown-toc.md)

### ログ観測性の限界

Claude runner は `inputTokens` / `outputTokens` / `costUsd` を返しているが、logger には保存していない。
そのため、今は「どのステップが何トークン食っているか」を実測比較できない。

参照:

- RunnerResponse の metadata: [.harness/src/runner.ts](/Users/tsuryoryo/Desktop/repo/obsidian/.harness/src/runner.ts:20)
- Claude 側では metadata を返している: [.harness/src/claude-runner.ts](/Users/tsuryoryo/Desktop/repo/obsidian/.harness/src/claude-runner.ts:117)
- logger は command stdout/stderr しか保存していない: [.harness/src/logger.ts](/Users/tsuryoryo/Desktop/repo/obsidian/.harness/src/logger.ts:98)

---

## 3. 現状の主要課題

### 課題 A: 同じ文脈を毎ステップ・毎サイクルで再送している

特に重いのは以下。

- spec 全文の再送
- test_cases 全文の再送
- criteria 全文の再送
- 対象ファイル全文の再送

これは生成でもレビューでも繰り返されている。

影響:

- トークンコストが高い
- 長文プロンプトのため、重要な差分より背景文脈が勝ちやすい
- 同じ指摘の再発や、小出しレビューの温床になる

### 課題 B: レビュー工程が厚すぎて、コストの大半を支配している

現行の impl 3 段レビューは品質重視としては合理的だが、同じコード全文と spec 全文を 3 回読む構造になっている。
さらに修正のたびに:

- 再レビュー
- lint
- 必要に応じて test
- judgment summary 生成

が入る。

影響:

- 軽微な修正でも往復コストが大きい
- minor 指摘が続いたときの時間損失が大きい
- 暴走時に止まりづらい

補足:

- 「レビューが厚いこと」自体は解消対象ではない
- 解消したいのは「レビュー観点に反する実装が生成され、レビューで初めて検出されること」
- したがって、真の改善対象はレビュー工程の存在ではなく、生成前後の品質拘束の弱さである

### 課題 F: レビュー観点が下流に寄りすぎており、上流の実装生成へ十分に内面化されていない

現状でも `criteria` は生成時の system prompt に渡しているが、レビューで実際に見ている観点が「生成前チェックリスト」や「自己検証タスク」として十分に分解されていない。

典型例:

- 仕様とズレる境界条件
- Markdown や文字種のような見落としやすい入力パターン
- レビュー観点では重要だが、lint では拾えない設計違反

影響:

- 実装生成時には「だいたい合っている」コードが出る
- その後レビューで重要観点に照らして差し戻される
- 結果としてレビューは品質担保というより、事後検査の比重が強くなる

### 課題 G: レビュー通過最適化に寄ると、品質ではなく採点器対策になる

review criteria や recurring finding を upstream に移すときに設計を誤ると、モデルが「この wording を避ける」「この形に書けば通る」といった表面的適応を起こす可能性がある。

影響:

- レビューでは指摘が減るが、本質的品質は上がらない
- hidden case や新しい観点に弱くなる
- ルールが増えるほど実装が不自然になる

### 課題 C: 品質のためのレビューと、報告のための生成が混ざっている

`generateJudgmentSummary` はレポート品質には効くが、コード品質そのものには寄与しない。
にもかかわらず、修正サイクルごとに追加 LLM 呼び出しを発生させている。

影響:

- トークン効率が悪い
- レポート都合のコストが実装フロー本体に乗っている

### 課題 D: TDD 純度と retrofit モードが同じフローに乗っている

`ALREADY_GREEN` の場合、実装生成をスキップしてレビューに進む。
既存コードの監査には有効だが、純粋な TDD としては意味が違う。

参照:

- [.harness/src/impl-flow.ts](/Users/tsuryoryo/Desktop/repo/obsidian/.harness/src/impl-flow.ts:247)
- [.harness/src/impl-flow.ts](/Users/tsuryoryo/Desktop/repo/obsidian/.harness/src/impl-flow.ts:266)

影響:

- 「新規 TDD 実装」と「既存実装レビュー」が同じ成功扱いになる
- フローの目的が曖昧になり、期待品質がぶれやすい

### 課題 E: 観測性が弱く、改善が勘になりやすい

今のログから分かるのは:

- 何回レビューしたか
- lint/pass/fail
- test 結果

までで、以下は弱い:

- 各 step の prompt サイズ
- input/output tokens
- cost
- どの step が外れ値の原因か

これは改善の優先順位を誤りやすい。

---

## 4. 議論したい論点

以下は、ユーザーとすり合わせたい論点。

### 論点 1: 「フルコンテキスト方式」をどこまでやめるか

候補:

- 仕様書全文ではなく「実装契約サマリ」を作って下流ではそれだけ渡す
- ファイル全文ではなく「変更ファイル + 周辺抜粋 + 代表関数」だけにする
- test_cases 全文ではなく、対象テストケースだけを構造化して渡す

考え方:

- トークン効率の観点では強く効く
- 品質面では、圧縮の仕方が悪いと文脈欠落のリスクがある
- したがって、単なる短縮ではなく「圧縮 artifact の設計」が必要

### 論点 2: self review を 2 段のまま維持するか

現状:

- criteria review
- quality review

候補:

- 1 回に統合する
- まず criteria review を実施し、通過時のみ quality review を走らせる
- あるいは machine-check 化できる規約を増やして criteria review 自体を薄くする

私見:

- 完全統合は token 削減には効くが、観点が混ざってレビュー精度が下がる可能性がある
- 優先順位としては「criteria をもっと機械へ寄せる」「LLM review は quality 中心へ寄せる」が筋が良い

### 論点 2.5: レビュー指摘を減らすために、生成前後に何を追加するか

候補:

- review criteria をそのまま渡すのではなく、「生成前チェックリスト」に変換する
- 実装生成の直後に、レビュー前の「preflight self-check」を 1 回入れる
- よく出る指摘をパターン化し、実装プロンプトに anti-pattern として埋め込む
- spec から「落としてはいけない境界条件」「壊しやすい契約」を抽出して impl prompt に明示する

私見:

- ここはかなり重要
- レビュー工程を薄くするより、「レビューで毎回指摘される類型を upstream で潰す」方が品質にも効く
- 特に backend では、境界条件・例外系・文字列処理・正規表現・整形仕様のズレが recurring finding になりやすい
- ただし、指摘文そのものを禁止語のように埋め込むのではなく、「なぜその指摘が出るのか」という失敗モードを実装前チェックへ翻訳する必要がある

### 論点 2.6: 「レビュー対策」と「品質改善」をどう見分けるか

候補:

- recurring finding をそのままルール化せず、失敗モード単位に再分類する
- review criteria 追加時は、対応する仕様・設計・テスト根拠を必須にする
- benchmark 対象とは別の hidden case で再検証する
- 文言ではなく振る舞いベースで検証する

私見:

- ここを曖昧にすると、短期的にはレビュー指摘が減っても、長期的には brittle になる
- upstream に移すべきなのは「指摘の wording」ではなく、「その指摘が検出していた実害パターン」

### 論点 3: レポート品質を実行フローから分離するか

候補:

- judgment summary を各サイクルで作らず、最後に records からまとめて生成する
- あるいは report を完全に post-process 化する

私見:

- これは token 効率改善の即効性が高い
- コード品質への負の影響が小さい
- 早めにやる価値が高い

### 論点 4: TDD モードと retrofit モードを分けるか

候補:

- `impl --strict-tdd`: RED が通ったら失敗
- `impl --review-existing`: ALREADY_GREEN を正式モードにする

私見:

- 品質議論を明確にするためにも分けるべき
- バックエンドの新規開発では strict をデフォルトに寄せたい

### 論点 5: plan 粒度をハーネス側で制御するか

現状、plan に 16-17 テストケースをまとめて流し込めてしまう。

候補:

- 1 run あたりの対象テストケース数に目安を設ける
- `Phase 1`, `Phase 2` ごとの分割を推奨する
- 閾値超過時は warning を出す

私見:

- これは品質とコストの両方に効く
- 「ハーネスの賢さ」以前に「入力単位の適正化」が重要

---

## 5. 推奨方針

以下の順でブラッシュアップするのがよい。

### 方針 A: まず観測性を上げる

最初にやるべき。

理由:

- どこにトークンが乗っているかを実測したい
- 改善前後比較ができないと議論が主観になる

やること:

- runner metadata を harness.jsonl に保存
- prompt 長（bytes or chars）を各 step で記録
- review cycle 数、lint retry 数、GREEN retry 数を step ごとに集計

### 方針 B: 次に文脈を圧縮する

主に Design → Impl の受け渡しを改善する。

やること:

- spec から「実装契約サマリ」を生成・保存する
- test_cases から「対象ケース要約」を生成する
- impl/review は原則として summary を使い、全文は fallback にする

期待効果:

- トークン削減が大きい
- 長文ノイズが減ってレビュー精度も上がりやすい

### 方針 B2: レビュー観点を upstream に移す

主に「レビューでよく出る指摘を、生成時点で出にくくする」ための方針。

やること:

- review criteria から「実装前チェックリスト」を生成する
- spec / test_cases から「絶対に外してはいけない契約」を抽出する
- 実装生成直後に lightweight な preflight check を 1 回だけ挟む
- recurring finding をナレッジ化し、プロンプトへ定常注入する

期待効果:

- external review の major 指摘を減らせる
- 修正ループ回数を減らしつつ、レビュー品質は維持できる
- レビューが「粗探し」ではなく「最終保証」に寄る

ガードレール:

- 指摘文の丸暗記は禁止
- 追加ルールは「失敗モード」「契約違反」「境界条件」のいずれかにマッピングできるものだけ採用する
- ルール追加後は hidden case または既存 benchmark 以外のケースで再検証する
- ルールがコードの自然さや設計を悪化させる場合は採用しない

### 方針 C: レビューを adaptive にする

やること:

- self criteria と self quality の役割を再整理
- 重大指摘がない限り外部レビューをスキップできるモードを追加
- minor のみの再レビューは 1 回で打ち切るなど、再試行条件を厳しくする

期待効果:

- 暴走抑制
- レビュー品質を落とさずコストを減らせる

補足:

- ここは「レビューを減らす」のではなく、「upstream 改善後でも冗長な往復だけを削る」という位置づけにする

### 方針 D: レポート生成を後段へ追い出す

やること:

- judgment summary の逐次生成をやめる
- review-data.json から最後にまとめて report を作る

期待効果:

- 追加 LLM 呼び出しを削減
- 実行中の往復回数を減らせる

### 方針 E: strict TDD と retrofit を分離する

やること:

- strict TDD モード追加
- ALREADY_GREEN を許容する review-existing モード追加

期待効果:

- 品質期待値が明確になる
- ベンチマークや既存コード監査も扱いやすくなる

---

## 6. 修正プラン案

### Phase 0: 計測の仕込み

対象:

- `runner.ts`
- `claude-runner.ts`
- `codex-runner.ts`
- `logger.ts`
- `impl-flow.ts`
- `review-orchestrator.ts`

変更:

- token/cost/prompt-size を structured log に保存
- review cycle ごとの統計を保存

完了条件:

- run ごとに step 別の token/cost が取れる

### Phase 1: コンテキスト圧縮 artifact 導入

対象:

- `design-flow.ts`
- `impl-flow.ts`
- `review-orchestrator.ts`
- `docs/spec/*`
- `tests/test-cases/*`

変更:

- spec digest / testcase digest を生成
- impl/review は digest 優先、全文 fallback

完了条件:

- 既存 benchmark で prompt サイズが有意に下がる
- benchmark のレビュー品質が維持される

### Phase 1.5: 指摘予防の preflight 導入

対象:

- `impl-flow.ts`
- `review-orchestrator.ts`
- impl templates
- review criteria

変更:

- review criteria から preflight checklist を作る
- 実装生成直後に lightweight self-check を 1 回だけ走らせる
- recurring finding を anti-pattern として prompt に埋め込む
- anti-pattern は wording ではなく失敗モードとして記述する
- 導入したチェックは hidden case で検証する

完了条件:

- external review の major 指摘数が benchmark で減る
- self review の再試行回数が減る
- benchmark 以外のケースでも品質低下が見られない

### Phase 2: レビュー構造の最適化

対象:

- `review-orchestrator.ts`
- review templates

変更:

- criteria review の役割縮小
- adaptive review モード追加
- minor-only ループの短縮
- external review の起動条件を見直し

完了条件:

- 1 run あたりの review 回数の中央値が下がる
- major 見逃しが増えない

### Phase 3: レポート生成の後処理化

対象:

- `review-orchestrator.ts`
- `impl-flow.ts`
- report generator

変更:

- `generateJudgmentSummary` の逐次呼び出しを廃止
- 最終レポート時にだけ要約生成

完了条件:

- fixed 1 件あたりの追加 LLM 呼び出しが減る

### Phase 4: モード分離

対象:

- `harness.ts`
- `impl-flow.ts`
- `README.md`
- `setup-guide.md`

変更:

- `--strict-tdd`
- `--review-existing`

完了条件:

- ALREADY_GREEN の扱いがモードごとに明確になる

### Phase 5: plan 粒度のガード

対象:

- `plan-parser.ts`
- `impl-flow.ts`
- docs

変更:

- テストケース数・spec サイズの warning
- 推奨分割ルールの明文化

完了条件:

- 巨大 plan を流し込んだときに事前警告できる

---

## 7. まず最初に着手すべき順番

優先順位は以下。

1. 観測性
2. レビュー指摘の recurring pattern 抽出
3. レポート生成の後処理化
4. コンテキスト圧縮 artifact
5. 指摘予防の preflight 導入
6. adaptive review
7. strict TDD / retrofit 分離
8. plan 粒度ガード

理由:

- 1 は全体の前提
- 2 と 5 が「レビューで指摘されにくい実装」を作る本丸
- 3 と 4 は効率改善
- 6 以降は運用品質を上げる仕上げ

---

## 8. この計画をもとに次にやること

次の会話では、以下を順に詰めるのがよい。

1. 「どのレビュー指摘を upstream で予防したいか」の優先順位付け
2. 「どこまで全文コンテキストを残すか」の方針決定
3. self review 2 段構成を維持するかの判断
4. strict TDD をデフォルトにするかの判断
5. Phase 0-1.5 の実装計画を具体タスクに分解

---

## 9. backend プロンプト棚卸し

ここでは「実際に backend フローで何を prompt に載せているか」を分解する。

### 9.1 Design Flow

#### spec 生成

入力:

- requirements
- featureName
- 出力先 path
- `docs/spec/TEMPLATE.md` 全文
- `CLAUDE.md` 全文を system prompt として追加

参照:

- [.harness/src/design-flow.ts](/Users/tsuryoryo/Desktop/repo/obsidian/.harness/src/design-flow.ts:80)

評価:

- `requirements`, `featureName`, 出力先 path は必須
- spec template は品質に効く
- `CLAUDE.md` 全文は backend spec 生成には過剰な可能性が高い

分類:

- 必須: requirements, featureName, 出力先 path, spec template
- 品質に効くが重い: なし
- 重複または要再設計: `CLAUDE.md` 全文

#### test case 生成

入力:

- spec 全文
- featureName
- 出力先 path
- `tests/test-cases/TEMPLATE.md` 全文

参照:

- [.harness/src/design-flow.ts](/Users/tsuryoryo/Desktop/repo/obsidian/.harness/src/design-flow.ts:120)

評価:

- spec 全文を入れるのは妥当
- ただし、将来的には spec 全文ではなく「受け入れ基準 + 境界条件 + スコープ外」抽出版でも成立する余地がある

分類:

- 必須: spec, 出力先 path, test case template
- 品質に効くが重い: spec 全文
- 重複または要再設計: なし

### 9.2 Impl Flow

#### test_generate

入力:

- `test-generate.md` テンプレート
- target test cases
- spec 全文
- `review-criteria-common.md` + `review-criteria-backend.md`
- 必要なら `rules/*.md`

参照:

- [.harness/src/impl-flow.ts](/Users/tsuryoryo/Desktop/repo/obsidian/.harness/src/impl-flow.ts:192)
- [.harness/templates/test-generate.md](/Users/tsuryoryo/Desktop/repo/obsidian/.harness/templates/test-generate.md)

評価:

- target test cases は必須
- spec 全文は妥当
- criteria 全文を test 生成にまで常時入れるのは効き方が弱い可能性がある
- common/backend criteria には test 生成に直接効かない項目も混ざっている

分類:

- 必須: target test cases, spec, test template
- 品質に効くが重い: spec 全文
- 重複または要再設計: criteria 全文の常時注入

#### impl_generate

入力:

- `impl-generate.md` または `impl-retry.md`
- test failure output
- spec 全文
- `review-criteria-common.md` + `review-criteria-backend.md`
- 必要なら rules

参照:

- [.harness/src/impl-flow.ts](/Users/tsuryoryo/Desktop/repo/obsidian/.harness/src/impl-flow.ts:290)
- [.harness/templates/impl-generate.md](/Users/tsuryoryo/Desktop/repo/obsidian/.harness/templates/impl-generate.md)
- [.harness/templates/impl-retry.md](/Users/tsuryoryo/Desktop/repo/obsidian/.harness/templates/impl-retry.md)

評価:

- test output は必須
- spec 全文も現状では重要
- criteria 全文を system prompt で入れる方針自体は分かるが、「実装前に効く観点」と「レビュー専用観点」が未分離
- retry prompt は短いが、失敗モードの guidance が弱い

分類:

- 必須: test output, spec, impl template
- 品質に効くが重い: spec 全文, criteria 全文
- 重複または要再設計: review 用 criteria をそのまま実装生成へ載せている点

### 9.3 Review Flow

#### test self review

入力:

- test code 全文
- test cases 全文
- spec 全文
- `review-test-quality.md`
- `review-response-format.md`

参照:

- [.harness/src/review-orchestrator.ts](/Users/tsuryoryo/Desktop/repo/obsidian/.harness/src/review-orchestrator.ts:409)

評価:

- 3 点セットは必要
- ただし response-format が 1.6KB と相対的に大きい
- 各 review で毎回同じ response-format を再送している

分類:

- 必須: test code, test cases, spec, review scope
- 品質に効くが重い: test cases 全文, spec 全文
- 重複または要再設計: response-format の毎回全文注入

#### impl self criteria review

入力:

- impl code 全文
- `review-criteria-common.md` + `review-criteria-backend.md`
- `review-impl-criteria.md`
- `review-response-format.md`

参照:

- [.harness/src/review-orchestrator.ts](/Users/tsuryoryo/Desktop/repo/obsidian/.harness/src/review-orchestrator.ts:426)

評価:

- criteria review としては筋が通っている
- ただし criteria は「実装前チェック」と「レビュー専用ルール」が混在している
- file 全文を毎回読むので再レビュー時コストが高い

分類:

- 必須: code, criteria, criteria review template
- 品質に効くが重い: code 全文, criteria 全文
- 重複または要再設計: response-format, criteria の未分離

#### impl self quality review

入力:

- impl code 全文
- spec 全文
- `review-impl-quality.md`
- `review-response-format.md`

参照:

- [.harness/src/review-orchestrator.ts](/Users/tsuryoryo/Desktop/repo/obsidian/.harness/src/review-orchestrator.ts:444)

評価:

- ここは本質的品質にかなり効いている
- 一方で code 全文 + spec 全文の再送は高コスト
- 受け入れ基準と境界条件に絞った digest に落とせる可能性が高い

分類:

- 必須: code, spec の品質判断に必要な部分, quality review template
- 品質に効くが重い: code 全文, spec 全文
- 重複または要再設計: response-format の毎回再送

#### external test / impl review

入力:

- code 全文
- test cases 全文 or spec 全文
- respective review template
- `review-response-format.md`

参照:

- [.harness/src/review-orchestrator.ts](/Users/tsuryoryo/Desktop/repo/obsidian/.harness/src/review-orchestrator.ts:459)
- [.harness/src/review-orchestrator.ts](/Users/tsuryoryo/Desktop/repo/obsidian/.harness/src/review-orchestrator.ts:475)

評価:

- 最終保証として必要
- ただし self review とかなり同じ材料を再読している
- external review が見るべき「差分観点」がまだ明確に絞れていない

分類:

- 必須: code, spec/test contract, external review template
- 品質に効くが重い: code 全文, spec/test cases 全文
- 重複または要再設計: self review とほぼ同じ文脈の再送

### 9.4 文脈サイズの概況

主要ファイルのサイズ:

- `CLAUDE.md`: 1,727 bytes
- `review-response-format.md`: 1,640 bytes
- `review-criteria-common.md`: 1,198 bytes
- `review-criteria-backend.md`: 552 bytes
- review templates 群合計: 約 6.5KB

ポイント:

- 単体で最も無駄が目立つのは `review-response-format.md` の常時再送
- 次に、review criteria を未分離のまま impl 生成と criteria review の両方に流している点
- そして本丸は、spec 全文と file 全文の反復再送

### 9.5 ここから導ける判断

backend prompt 改善で先に見るべき順番は以下。

1. `review-response-format` の再送方式見直し
2. review criteria を「実装前に効く制約」と「レビュー専用観点」に分割
3. spec 全文を digest 化できるか検証
4. external review に渡す観点を self review と差別化

重要なのは、ここで削るべきなのは「レビューの質」ではなく「同じ情報の重複送信」と「生成時に効いていない長文文脈」であること。
