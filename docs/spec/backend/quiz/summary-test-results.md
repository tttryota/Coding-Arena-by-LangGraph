---
feature: summary-test-results
status: ready
reviewed_by:
approved_at:
---

## 機能概要

`backend/quiz/application/` に配置する application/usecase。過去のまとめテスト（中枠・大枠）の結果履歴を取得する。

## 振る舞い

### 基本動作

`get_summary_test_results(...)` はロードマップ項目IDを受け取り、その項目のまとめテスト結果履歴を返す。結果は `store.find_by_roadmap_item(...)` が返した `SummaryTestResultRecord` 一覧をそのまま返し、並び順は store 契約上の `created_at` 降順を保持する。`roadmap_item_id` による絞り込みは store に委譲し、usecase 側で返却済み record 群を追加フィルタしない。

### 具体例

呼び出し:
`get_summary_test_results("rm_mid_001", existence_checker=..., store=...)`

戻り値:
```json
[
  {
    "id": "...",
    "session_id": "...",
    "score": 65,
    "analysis": "型の基礎知識は十分ですが、ジェネリクスの実践的な使用に課題があります...",
    "created_at": "2026-05-18T14:00:00"
  },
  {
    "id": "...",
    "session_id": "...",
    "score": 45,
    "analysis": "全体的に理解が浅く、特に型推論の仕組みが曖昧です...",
    "created_at": "2026-05-10T10:00:00"
  }
]
```

## 技術判断

- ロードマップ項目IDでフィルタする理由: まとめテストは特定の中枠・大枠に対して実施されるため、項目単位での取得が自然

## 境界条件

- 結果が0件（まだテスト未実施）→ 空配列を返す
- 存在しないロードマップ項目ID → `SummaryTestResultsNotFoundError` を送出する

## スコープ外

- 結果の削除
- 結果間の比較分析（フロントエンド側で前回比等を表示する場合はレスポンスデータから算出）
- ページネーション
- 入力されたロードマップ項目IDから項目種別（中枠・大枠・detail など）を判定する契約
- detail 判定方法やロードマップ項目IDの命名規約
- `SummaryTestResultsNotFoundError` を HTTP 404 に変換する outer layer の責務
- 構造化ログ出力、logger 依存、ログイベント名やログレコード必須キーの運用契約
- 戻り値 record 単体からのロードマップ項目識別や、store が返した混在データを usecase 側で除外する責務

## 受け入れ基準

- [ ] ロードマップ項目IDでまとめテスト結果の履歴が取得できる
- [ ] 実施日時の降順で返る
- [ ] 各結果にscore, analysis, created_atが含まれる
- [ ] 結果が0件の場合は空配列が返る

## 異常系

- DB呼び出し失敗時は `SummaryTestResultsError` を送出し、`error_code: str` と `message: str` を属性として持ち、`__cause__` に元例外を保持する
- 存在しないロードマップ項目IDの場合は `SummaryTestResultsNotFoundError` を送出する

| error_code | 発生条件 | message |
|---|---|---|
| `item_not_found` | ロードマップ項目が存在しない | `roadmap item not found` |
| `persistence_failed` | DB読み取りが失敗 | `summary test results persistence failed` |

## モジュール構成

- 構成方針: 2ファイル構成（types + logic）
- モジュール一覧:
  - `backend/quiz/application/summary_test_results_types.py`
    - `SummaryTestResultsError(Exception)` — `error_code: str`, `message: str` を属性として持つ
    - `SummaryTestResultsNotFoundError(SummaryTestResultsError)` — item_not_found 用
    - `SummaryTestResultRecord` — frozen dataclass (`id: str`, `session_id: str`, `score: int`, `analysis: str`, `created_at: str`)
    - `SummaryTestResultsStore(Protocol)` — `find_by_roadmap_item(roadmap_item_id: str) -> list[SummaryTestResultRecord]`（`roadmap_item_id` による絞り込み済み、`created_at` 降順）
    - `RoadmapItemExistenceChecker(Protocol)` — `item_exists(item_id: str) -> bool`
  - `backend/quiz/application/summary_test_results.py`
    - `get_summary_test_results(roadmap_item_id: str, *, existence_checker: RoadmapItemExistenceChecker, store: SummaryTestResultsStore) -> list[SummaryTestResultRecord]` — ロードマップ項目IDでまとめテスト結果を取得。項目が存在しなければ `SummaryTestResultsNotFoundError` を送出。結果0件なら空リスト。store が返した record 群に対する追加フィルタは行わない
