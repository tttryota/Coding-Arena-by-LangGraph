---
type: impl
profile: backend
scope: roadmap/topic-listing
spec: docs/spec/backend/roadmap/topic-listing.md
test_cases: tests/test-cases/backend/roadmap/topic-listing.md
---

## 今回やること
topic-listing を TDD で実装する

## 対象テストケース
- TC-01: 実装配置先と公開 API / types の静的契約が仕様どおりであり、不在条件も満たす
- TC-02: プリセットのみ存在する初回相当状態で候補一覧を返し、note_count 未返却分を 0 にする
- TC-03: 新規の自由入力トピックを登録し、一覧と同じ TopicCandidate を返す
- TC-10: 3 ソースを canonical_name 単位で統合し、preset -> manual -> note 優先、note_count 付与、最終ソートを満たす
- TC-11: preset がない重複では manual が note より優先される
- TC-12: 既存トピックとの重複登録では NFKC + casefold() の比較キーで find し、代表 record をそのまま返す
- TC-13: 重複判定は canonical_name 完全一致だけに限定され、部分一致や同義語扱いはしない
- TC-20: 3 ソースがすべて空でも一覧取得は正常終了する
- TC-21: 前後空白除去後に空文字となる自由入力は TopicListingEmptyTopicNameError を送出し、外部依存を呼ばない
- TC-22: 保存用正規化名は内部空白を保持し、比較用 canonical_name だけに NFKC + casefold() を適用する
- TC-30: list_topic_candidates は 4 依存を所定メソッドだけ 1 回ずつ呼び、登録系メソッドは使わない
- TC-31: 既存重複の自由入力登録では find のみで重複判定し、create を呼ばずに件数取得する
- TC-32: 新規の自由入力登録では create を 1 回だけ呼び、件数取得まで完了する

## やらないこと
- プリセットの管理画面
- トピックの階層構造
- トピックの統合・リネーム機能
- 同義語辞書ベース統合、略語展開、部分一致、形態素解析などの高度な表記ゆれ吸収
- HTTP エンドポイントの実装（presentation 層で別途実装）
- TopicStore / TopicNoteCountReader の実装（依存契約のみ定義）

## 完了条件
- 対象テストケースが全て GREEN
- ruff + mypy がパス
- レビュー通過

## 設計判断
- 依存モジュールは Protocol DI で注入（TopicPresetReader, NoteTopicReader, TopicStore, TopicNoteCountReader）
- 全ファイルを backend/roadmap/infrastructure/ に配置（harness sourceLayout 準拠）
- 2 モジュール構成: topic_listing_types.py, topic_listing.py
- DTO・Protocol・例外を types 側に分離し、一覧統合・正規化・登録オーケストレーションを本体モジュールにまとめる
- canonical_name の正規化は NFKC + casefold() で統一
- 保存用正規化は strip() のみ、比較用正規化と分離
- 候補統合は canonical_name 単位、優先順は preset -> manual -> note
- list_note_counts への引数は canonical_name 昇順の重複排除済み配列
- 返却順は note_count 降順、同値時は canonical_name 昇順
- 依存契約（note_id 重複排除、代表選択）は Protocol 側の責務として topic_listing 本体では再計算しない
