---
status: ready
---

# テストケース一覧

# 検証焦点

| テストの種類 | 検証焦点 |
|---|---|
| Phase 1（最小骨格） | `SummaryTestResultRecord` の公開フィールド契約、`get_summary_test_results(...)` の最小成功戻り値 |
| Phase 2（コアロジック） | `roadmap_item_id` 指定での履歴取得、同一項目の複数結果返却、`created_at` 降順の保持 |
| Phase 3（エッジケース） | 結果0件の空配列返却 |
| Phase 4（異常系） | application 層の `SummaryTestResultsNotFoundError` と `SummaryTestResultsError` の送出、`error_code` / `message` / `__cause__` |

## Phase 1: 最小骨格

| ID | 観点 | 前提 | 入力 | 期待結果 | 備考 |
|---|---|---|---|---|---|
| TC-01 | 既存のロードマップ項目に対してまとめテスト結果1件を返せる | `existence_checker.item_exists("rm_mid_001")` は `True` を返す。`store.find_by_roadmap_item("rm_mid_001")` は `SummaryTestResultRecord(id="str_001", session_id="sess_001", score=65, analysis="型の基礎知識は十分ですが、ジェネリクスの実践的な使用に課題があります。", created_at="2026-05-18T14:00:00")` 1件を返す | `roadmap_item_id="rm_mid_001"` を指定して `get_summary_test_results(roadmap_item_id, existence_checker=..., store=...)` を実行する | 戻り値は長さ1の `list[SummaryTestResultRecord]` である。先頭要素の `id`, `session_id`, `score`, `analysis`, `created_at` は前提の record 値と完全一致する。少なくとも `score`, `analysis`, `created_at` が欠落せず含まれることを内容検証する | 受け入れ基準「履歴取得」「各結果に score, analysis, created_at が含まれる」に対応 |
| TC-02 | `SummaryTestResultRecord` が frozen dataclass として公開フィールド5件を持つ | `SummaryTestResultRecord` を直接生成できる | `SummaryTestResultRecord(id="str_002", session_id="sess_002", score=45, analysis="全体的に理解が浅いです。", created_at="2026-05-10T10:00:00")` を生成し、その後 `score` の再代入を試みる | 生成した record は `id`, `session_id`, `score`, `analysis`, `created_at` の5属性を持ち、各値は入力と完全一致する。属性再代入は失敗し、frozen dataclass として外部から変更できないことを確認する | 型定義の公開契約確認 |

## Phase 2: コアロジック

| ID | 観点 | 前提 | 入力 | 期待結果 | 備考 |
|---|---|---|---|---|---|
| TC-10 | 指定した `roadmap_item_id` を store に委譲し、その store が返した履歴を返す | `existence_checker.item_exists("rm_large_001")` は `True` を返す。`store.find_by_roadmap_item(...)` の呼び出し引数を観測でき、`"rm_large_001"` が渡された場合のみ対象項目の履歴2件を返す stub である | `roadmap_item_id="rm_large_001"` を指定して `get_summary_test_results(...)` を実行する | `store.find_by_roadmap_item(...)` に `"rm_large_001"` が渡されたことを確認する。戻り値は store stub が返した対象項目の履歴2件と件数・順序・各 record の内容が完全一致する | 受け入れ基準「ロードマップ項目IDでまとめテスト結果の履歴が取得できる」に対応 |
| TC-11 | 複数結果が `created_at` の降順で返る | `existence_checker.item_exists("rm_large_001")` は `True` を返す。`store.find_by_roadmap_item("rm_large_001")` は `created_at` が `"2026-05-18T14:00:00"` の record と `"2026-05-10T10:00:00"` の record をこの順で返す | `roadmap_item_id="rm_large_001"` を指定して `get_summary_test_results(...)` を実行する | 戻り値は2件である。`results[0].created_at` は `"2026-05-18T14:00:00"`、`results[1].created_at` は `"2026-05-10T10:00:00"` と完全一致する。返却順は新しい実施日時から古い実施日時への降順である | store の降順契約が usecase 戻り値でも保持されることを確認する |

## Phase 3: エッジケース

| ID | 観点 | 前提 | 入力 | 期待結果 | 備考 |
|---|---|---|---|---|---|
| TC-20 | 既存のロードマップ項目でも結果が0件なら空配列を返す | `existence_checker.item_exists("rm_mid_002")` は `True` を返す。`store.find_by_roadmap_item("rm_mid_002")` は空リストを返す | `roadmap_item_id="rm_mid_002"` を指定して `get_summary_test_results(...)` を実行する | 戻り値は空配列 `[]` と完全一致する。例外は送出されない | 受け入れ基準「結果が0件の場合は空配列が返る」に対応 |

## Phase 4: 異常系

| ID | 観点 | 前提 | 入力 | 期待結果 | 備考 |
|---|---|---|---|---|---|
| TC-30 | 存在しないロードマップ項目 ID は application 層で `SummaryTestResultsNotFoundError` を送出する | `existence_checker.item_exists("rm_missing_001")` は `False` を返す | `roadmap_item_id="rm_missing_001"` を指定して `get_summary_test_results(...)` を実行する | `SummaryTestResultsNotFoundError` が送出される。`error_code` は `item_not_found`、`message` は `roadmap item not found` と完全一致する。HTTP 404 への変換は outer layer の責務であり、このテストの対象外とする | 異常系 `item_not_found` |
| TC-31 | 存在確認の DB 読み取り失敗は `SummaryTestResultsError` に包んで再送出する | `existence_checker.item_exists("rm_mid_003")` の呼び出しで元例外 `RuntimeError("db read failed")` が発生する | `roadmap_item_id="rm_mid_003"` を指定して `get_summary_test_results(...)` を実行する | `SummaryTestResultsError` が送出される。`error_code` は `persistence_failed`、`message` は `summary test results persistence failed` と完全一致する。`__cause__` は元の `RuntimeError("db read failed")` を保持する | DB 呼び出し失敗の存在確認側 |
| TC-32 | 結果取得の DB 読み取り失敗は `SummaryTestResultsError` に包んで再送出する | `existence_checker.item_exists("rm_mid_004")` は `True` を返す。`store.find_by_roadmap_item("rm_mid_004")` の呼び出しで元例外 `RuntimeError("db read failed")` が発生する | `roadmap_item_id="rm_mid_004"` を指定して `get_summary_test_results(...)` を実行する | `SummaryTestResultsError` が送出される。`error_code` は `persistence_failed`、`message` は `summary test results persistence failed` と完全一致する。`__cause__` は元の `RuntimeError("db read failed")` を保持する | DB 呼び出し失敗の結果取得側 |

# 網羅性チェック

仕様書の受け入れ基準の各項目に対応するテストケース ID を記載する。
全項目が少なくとも1つのテストケースでカバーされていることを確認する。

| 受け入れ基準 | 対応テストケース |
|---|---|
| ロードマップ項目IDでまとめテスト結果の履歴が取得できる | TC-01, TC-10 |
| 実施日時の降順で返る | TC-11 |
| 各結果にscore, analysis, created_atが含まれる | TC-01, TC-02 |
| 結果が0件の場合は空配列が返る | TC-20 |

# 記述ルール

- 仕様書に明記された振る舞いだけを前提にする
- 仕様未記載の振る舞いを期待結果に置く場合は `[要仕様追記]` タグを付ける
- 正常系・境界系・異常系が重複なく網羅されていることを確認する
- 仕様書の受け入れ基準の各項目に対応するテストケースが最低1つあることを確認する
- 期待結果に「含まれる」「完全一致」「少なくとも1件」などの検証粒度を明示する
- 例外検証を含む場合は、例外型、message、cause chain のうち何を確認するかを明示する
- テストが「存在確認」なのか「内容検証」なのかを期待結果で区別して書く
- テストケース文書に書いていない検証を impl レビューで追加要求しなくて済む粒度まで、期待結果を具体化する
