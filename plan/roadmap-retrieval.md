---
type: impl
profile: backend
scope: roadmap/roadmap-retrieval
spec: docs/spec/backend/roadmap/roadmap-retrieval.md
test_cases: tests/test-cases/backend/roadmap/roadmap-retrieval.md
---

## 今回やること
roadmap-retrieval を TDD で実装する

## 対象テストケース
- TC-01: 最小3階層でget_roadmapが全フィールドを組み立て、非集約フィールドを原値保持し、成功ログを出す
- TC-10: 順不同のflat recordsから複数major/middle/detailのツリーを再構築し、order昇順で返し、段階的スコア集約する
- TC-11: スコア平均の端数を各レベルで切り捨てる
- TC-12: list_roadmapsがreader返却順を保持しつつoverall_scoreを付与し、成功ログを出す
- TC-20: 項目0件のロードマップを正常に返す
- TC-21: middleにdetailが0件のときscore=0で集約に反映
- TC-22: majorにmiddleが0件のときscore=0で集約に反映
- TC-23: 全detailのscore=0のとき全レベル0
- TC-24: ロードマップ0件で一覧取得
- TC-25: 仕様外データは期待結果対象に含めないことの確認（テスト不要）
- TC-30: 存在しないroadmap_idでNotFoundError + warningログ
- TC-31: get_roadmapでreader例外時にStoreError + errorログ
- TC-32: list_roadmapsでreader例外時にStoreError + errorログ

## やらないこと
- ロードマップの生成（roadmap-persistenceの責務）
- ロードマップの更新・削除（roadmap-item-crudの責務）
- 不正階層データの検知・修復・バリデーション
- スコアの加重平均や重み付け
- ページネーション
- フィルタ検索
- HTTPエンドポイントの実装

## 完了条件
- 対象テストケースが全て GREEN
- ruff + mypy がパス
- レビュー通過

## 設計判断
- 依存モジュールはProtocol DIで注入（RoadmapRetrievalReader）
- 全ファイルを backend/roadmap/infrastructure/ に配置（harness sourceLayout準拠）
- 2モジュール構成: roadmap_retrieval_types.py, roadmap_retrieval.py
- ツリー構築はparent_idでフラットレコードを親子に組み立て、order昇順でソート
- スコア集約はdetail→middle→major→overallの順、各レベルでfloor切り捨て
- 子0件のmiddle/majorはscore=0（未着手扱い）
- major/middleのlast_quiz_atはNone固定
- list_roadmapsはreader返却順を保持、ソートはpresentation層に委ねる
- reader返却データは契約を満たす前提、不正データのバリデーションはしない
