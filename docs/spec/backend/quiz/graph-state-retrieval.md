---
status: draft
---

# 概要

- LangGraph 実行後の最新 `SessionState` を呼び出し側が取得できないため、`chat_response` や `explanation_generation` の結果を application 層が確実に参照できない課題を解消する。
- `GraphRunner` を利用する application 層の呼び出し元、`GraphRunner` の concrete 実装、`SessionState` を共有する LangGraph ノード実装を利用者とする。
- authoritative scope は `backend/quiz/application/**` と `backend/quiz/domain/**` に限定し、この機能の requirements で必要な変更対象もその範囲に限る。
- 前提条件:
  - 対象グラフは LangGraph の checkpointer を有効にして compile 済みである。
  - `thread_id` は `start_graph` / `resume_graph` / `retry_graph` と `get_state` で同一値を使用する。
  - `SessionState` の既存 16 フィールド契約は維持し、この機能では 2 フィールドのみ追加する。

# 入出力

- 入力:
  - `GraphRunner.get_state(*, thread_id: str)` に渡す `thread_id`
  - 同じ `thread_id` で直前に実行された `GraphRunner.start_graph(...)` / `resume_graph(...)` / `retry_graph(...)`
  - LangGraph ノードが返す state 更新 dict
    - `chat_response` ノード: `{"chat_response_text": str}`
    - `explanation_generation` ノード: `{"explanation_text": str}`
- 出力:
  - `GraphRunner` Protocol に `get_state(self, *, thread_id: str) -> SessionState` を追加する。
  - `get_state(...)` は checkpointer に保存された最新 checkpoint の root graph state を返す。
  - 返却する `SessionState` は既存 16 フィールドを保持したまま、以下 2 フィールドを追加した合計 18 フィールド契約とする。
    - `explanation_text: str`
    - `chat_response_text: str`
  - `get_state(...)` は checkpoint metadata、`next`、`tasks` ではなく `SessionState` 本体だけを返す。
  - 依存注入面の変更は `GraphRunner` に `get_state` を 1 メソッド追加することだけに限定し、既存の `start_graph` / `resume_graph` / `retry_graph` の呼び出し形と戻り値契約は維持する。
- エラー:
  送出する例外の型名と発生条件を定義する。
  例外型はテストで使用されるため、型名を具体的に指定すること。
  実装詳細ではなく、呼び出し元との契約として記述する。
  - `ValueError`: `thread_id` が空文字である
  - `LookupError`: 指定 `thread_id` に返却可能な checkpoint/root state が存在しない
  - `RuntimeError`: checkpointer 未設定、checkpoint 読み出し失敗、または取得した checkpoint の `StateSnapshot.values` が mapping ではない

# 具体例

代表的な入力と、それに対して期待される出力をデータ例で示す。
テストケース生成やレビューで曖昧さが出ないよう、入力・出力ともに具体値で書く。

## 例1

- 入力:
  - `thread_id="sess_001"` で `resume_graph({"user_input": "型パラメータって何ですか？", "input_source": "chat"})` を実行済み
  - 直前のルーティングで `input_type="question"` と判定され、`chat_response` ノードが `{"chat_response_text": "型パラメータは、関数や型に後から具体的な型を渡すための型の引数です。"}` を返した
  - その直後に `get_state(thread_id="sess_001")` を呼ぶ
- 期待される出力:

```python
{
    "session_id": "sess_001",
    "roadmap_item_id": "ri_ts_generics",
    "roadmap_item_level": "detail",
    "roadmap_item_title": "TypeScript ジェネリクス",
    "roadmap_item_description": "型パラメータと型推論の理解を確認する",
    "is_resumed": True,
    "confirmation_points": [
        {
            "id": "cp_001",
            "content": "ジェネリクスの必要性を説明できる",
            "format": "knowledge",
        }
    ],
    "current_point_index": 0,
    "current_question_text": "ジェネリクスの型パラメータとは何ですか？",
    "current_answer_type": "textarea",
    "user_input": "型パラメータって何ですか？",
    "input_source": "chat",
    "input_type": "question",
    "chat_response_text": "型パラメータは、関数や型に後から具体的な型を渡すための型の引数です。",
    "answers": [],
    "total_questions_asked": 1,
}
```

## 例2

- 入力:
  - `thread_id="sess_002"` で `resume_graph({"user_input": "わからないので解説してください", "input_source": "chat"})` を実行済み
  - 直前のルーティングで `input_type="explanation_request"` と判定され、`explanation_generation` ノードが `{"explanation_text": "あなたのノートでは『ジェネリクスは型を後から具体化する仕組み』とあります。つまり..."}` を返した
  - その直後に `get_state(thread_id="sess_002")` を呼ぶ
- 期待される出力:

```python
{
    "session_id": "sess_002",
    "roadmap_item_id": "ri_ts_generics",
    "roadmap_item_level": "detail",
    "roadmap_item_title": "TypeScript ジェネリクス",
    "roadmap_item_description": "型パラメータと型推論の理解を確認する",
    "is_resumed": True,
    "confirmation_points": [
        {
            "id": "cp_001",
            "content": "ジェネリクスの必要性を説明できる",
            "format": "knowledge",
        }
    ],
    "current_point_index": 0,
    "current_question_text": "ジェネリクスの型パラメータとは何ですか？",
    "current_answer_type": "textarea",
    "user_input": "わからないので解説してください",
    "input_source": "chat",
    "input_type": "explanation_request",
    "explanation_text": "あなたのノートでは『ジェネリクスは型を後から具体化する仕組み』とあります。つまり...",
    "answers": [],
    "total_questions_asked": 1,
}
```

# 主要ルール

1. `GraphRunner.get_state` 公開契約:
   - 条件:
     - `backend/quiz/application/session_lifecycle_types.py` で `GraphRunner` Protocol を公開する
   - 振る舞い:
     - `GraphRunner` に `get_state(self, *, thread_id: str) -> SessionState` を追加する。
     - `get_state(...)` は既存の `GraphRunner` 系メソッドと同じ keyword-only の `thread_id` を要求し、位置引数では呼ばない。
     - 依存注入面の変更は `GraphRunner` に 1 メソッド追加することだけに限定する。
     - 既存の `start_graph(...) -> None`、`resume_graph(...) -> None`、`retry_graph(...) -> None` の呼び出し面と戻り値契約は変更しない。
     - 呼び出し側がグラフ実行後の state を必要とする場合は、実行メソッドの返り値ではなく `get_state(...)` を使って取得する。

2. 最新 checkpoint の取得:
   - 条件:
     - `get_state(thread_id=...)` が有効な `thread_id` で呼ばれる
   - 振る舞い:
     - `QuizGraphRunner` は LangGraph の checkpointer から、その `thread_id` に対応する最新 checkpoint を 1 件だけ読む。
     - `LookupError` は、対象 `thread_id` に返却可能な checkpoint/root state が存在しない場合にだけ送出する。`StateSnapshot.values` の空/非空では判定しない。
     - latest `StateSnapshot.values` が mapping である場合、その root graph の state を `SessionState` として `{}` を含めてそのまま返し、checkpoint metadata や実行履歴は返さない。
     - `get_state(...)` は partial TypedDict である `SessionState` に対する追加の runtime schema validation を行わず、required key の充足確認や個別フィールド型の厳密検証は行わない。
     - latest `StateSnapshot.values` が mapping ではない場合だけ `RuntimeError` を送出する。
     - `get_state(...)` 自体はグラフを再実行せず、checkpoint の読取だけを行う。

3. `SessionState` のフィールド追加:
   - 条件:
     - `backend/quiz/domain/session_state.py` で `SessionState` TypedDict を定義する
   - 振る舞い:
     - 既存 16 フィールドを変更せず維持する。
     - 以下 2 フィールドを optional な共有 state キーとして追加する。
       - `explanation_text: str`
       - `chat_response_text: str`
     - 追加後の `SessionState` の総フィールド数は 18 とする。
     - どちらのフィールドも partial TypedDict の性質に従い、該当ノード未実行フェーズでは未設定を許容する。

4. ノード出力の state 保存:
   - 条件:
     - `chat_response` ノードまたは `explanation_generation` ノードが正常終了する
   - 振る舞い:
     - `chat_response` ノードが返した `chat_response_text` は、その値を変換せずに graph state へ保存する。
     - `explanation_generation` ノードが返した `explanation_text` は、その値を変換せずに graph state へ保存する。
     - `get_state(...)` で取得した `SessionState` から、直前に保存された当該キーの値をそのまま読める。

5. 呼び出し側の取得タイミング:
   - 条件:
     - application 層が `start_graph` / `resume_graph` / `retry_graph` 実行後の最新 state を返却または参照したい
   - 振る舞い:
     - `backend/quiz/application/session_lifecycle.py` の公開関数では、`resume_session(...) -> SessionState` のみが `resume_graph(...)` 成功後に同じ `thread_id` で `get_state(...)` を呼び、その戻り値を返す。
     - `resume_session(...)` は実行前に組み立てた resume 用 seed state を返してはならず、`get_state(...)` が返した post-run state を authoritative な `SessionState` として扱う。
     - `resume_graph(...)` 成功後の `get_state(...)` が `LookupError` または `RuntimeError` を送出した場合、`resume_session(...)` は raw 例外をそのまま公開せず `QuizSessionLifecycleError` に包んで送出し、cause chain で元例外を保持する。
     - `start_session(...) -> StartSessionResult`、`record_answer(...) -> None`、`complete_session(...) -> None` は既存の戻り値契約を維持し、この仕様では `get_state(...)` の公開返却対象に含めない。

# 境界条件

- ケース:
  - `get_state(...)` を、まだ `start_graph` / `resume_graph` / `retry_graph` を一度も実行していない `thread_id` に対して呼ぶ
  - 振る舞い:
    - `LookupError` を送出する
  - 理由:
    - checkpointer に返却可能な checkpoint/root state が存在しないため
- ケース:
  - 最新 checkpoint の `StateSnapshot.values` が空 mapping `{}` である
  - 振る舞い:
    - `get_state(...)` は `{}` を `SessionState` としてそのまま返し、`LookupError` にはしない
  - 理由:
    - `LookupError` 判定は checkpoint/root state の不在だけに限定し、mapping の空/非空とは切り分けるため
- ケース:
  - 最新 checkpoint が graph 完了ではなく interrupt 待機中の state を表している
  - 振る舞い:
    - `get_state(...)` はその interrupt 時点の `SessionState` を返す
  - 理由:
    - 呼び出し側が再開前の最新 state を確認できる必要があるため
- ケース:
  - `chat_response_text` と `explanation_text` のうち、今回の実行で更新されたのが片方だけである
  - 振る舞い:
    - 更新されたキーだけが今回の node 出力で上書きされ、未更新キーは checkpointer 上の最新 state に保存されている値をそのまま保持する
  - 理由:
    - この機能は state 取得と保存対象フィールド追加のみを扱い、自動クリア規則は定義しないため
- ルール間の相互作用:
  複数ルールが同時に適用されるケースを列挙し、優先順位と最終的な振る舞いを明記する
  `resume_graph(...)` 成功後に `chat_response` または `explanation_generation` が state を更新し、その直後に `resume_session(...)` が `get_state(...)` を実行する場合は、ルール 2 の「最新 checkpoint を読む」が最優先で適用される。その結果としてルール 4 の保存済みキーを含む最新 `SessionState` が返る。`resume_session(...)` はルール 5 に従って seed state ではなく post-run state を返す。
  `resume_graph(...)` は成功したが、その後の `get_state(...)` が `LookupError` または `RuntimeError` になった場合は、ルール 5 の公開例外契約が優先され、`resume_session(...)` の outward error は `QuizSessionLifecycleError` になる。

# 非機能・制約

- 性能:
  - `get_state(...)` は 1 回の checkpointer 読取だけで完結し、グラフ再実行や state history 全件走査を行わない
- 可観測性:
  - この機能自体では新しいログイベントやメトリクス名を必須化しない。障害時は送出例外の型で呼び出し側が判定できることを優先する
- 外部依存:
  - LangGraph の `CompiledStateGraph.get_state(config)` 相当の state 読取 API
  - checkpointer による `thread_id` ベースの checkpoint 永続化
- harness scope:
  - この機能の実装・テスト対象は `backend/quiz/application/**` と `backend/quiz/domain/**` を再帰的に含む必要がある。
  - top-level のみを対象にする `backend/quiz/*` では `backend/quiz/application/session_lifecycle.py`、`backend/quiz/application/session_lifecycle_types.py`、`backend/quiz/application/graph.py`、`backend/quiz/domain/session_state.py` を含められないため不足とする。
  - requirements 上の scope は `backend/quiz/application/**` と `backend/quiz/domain/**` を超えて広げない。

# モジュール構成

design 時に、各モジュールが概ね 200-300 行に収まるかを責務単位で概算し、実装の切り方を先に決める。
厳密な計算式は不要だが、例外型・データ構造・主要ルール・バリデーション・ログなどの構成要素を踏まえて判断する。
単一ファイルで十分な場合も、その判断を明記する。

- 構成方針:
  - `複数モジュールに分割する`
- 概算メモ:
  - `SessionState` への 2 フィールド追加は小変更だが、`GraphRunner` Protocol 変更、`QuizGraphRunner` の adapter 実装、必要であれば application 層呼び出し元の取得処理まで含むため 1 ファイルに責務を集約しない
  - 各モジュールは 200 行前後に収まり、既存責務の延長として実装できる見込み
- モジュール一覧:
  - モジュール名:
    - `backend/quiz/domain/session_state.py`
    - 責務:
      - `SessionState` TypedDict に `explanation_text` と `chat_response_text` を追加する
    - 含める要素:
      - 18 フィールドの state 型注釈
  - モジュール名:
    - `backend/quiz/application/session_lifecycle_types.py`
    - 責務:
      - `GraphRunner` Protocol に `get_state(self, *, thread_id: str) -> SessionState` を追加する
    - 含める要素:
      - Protocol メソッド定義
  - モジュール名:
    - `backend/quiz/application/graph.py`
    - 責務:
      - LangGraph の state snapshot を `SessionState` として返す `QuizGraphRunner.get_state(...)` の concrete 実装を提供する
    - 含める要素:
      - `thread_id` から config を組み立てる処理
      - latest state 取得
      - `ValueError` / `LookupError` / `RuntimeError` 契約に合わせた例外送出
  - モジュール名:
    - `backend/quiz/application/session_lifecycle.py`
    - 責務:
      - `resume_session(...)` で `resume_graph(...)` 成功後の authoritative state を `GraphRunner.get_state(...)` から取得して返す
    - 含める要素:
      - `resume_session(...)` に対する実行後取得タイミングの適用
      - `start_session(...)`、`record_answer(...)`、`complete_session(...)` の既存戻り値契約維持

# 技術判断

品質に直結する技術選定や実装方針がある場合は、その判断と理由を書く。

- 判断:
  - LangGraph 実行結果の取得元は `invoke(...)` の返り値ではなく checkpointer 上の latest state を単一の正とする
  - 理由:
    - LangGraph の公式ドキュメントでは、checkpointer を有効にした graph の最新 state は `thread_id` を指定した `get_state(...)` で取得する契約になっているため。実行完了・interrupt 待機・再試行後のいずれでも同じ取得経路に統一できる
- 判断:
  - `GraphRunner` の実行メソッドと state 取得メソッドを分離したまま維持する
  - 理由:
    - 既存の `start_graph` / `resume_graph` / `retry_graph` の副作用契約と依存注入面を壊さず、`get_state(self, *, thread_id: str)` だけを追加して実行後 state が必要な呼び出し元だけが追加 API を利用できるため
- 判断:
  - `explanation_text` と `chat_response_text` は partial `SessionState` の optional フィールドとして追加する
  - 理由:
    - どちらの node も毎回実行されるわけではなく、未実行フェーズの未設定を許容しないと既存の段階的 state 構築契約を壊すため

# スコープ外

この機能では扱わないこと、別 issue / 別機能で扱うことを明示する。

- 対応しないこと:
  - checkpoint history 一覧取得や `checkpoint_id` 指定取得
  - `chat_response_text` / `explanation_text` の自動クリア規則追加
  - `StateSnapshot.next` / `metadata` / `tasks` の外部公開
  - subgraph state の取得

# 受け入れ基準

検証可能な条件をチェックリスト形式で書く。実装手段ではなく、満たされるべき事実を書く。

- [ ] `GraphRunner` Protocol に `get_state(self, *, thread_id: str) -> SessionState` が追加され、既存 3 メソッドの呼び出し面と戻り値契約は維持されている
- [ ] `SessionState` に `explanation_text` と `chat_response_text` が追加され、既存 16 フィールドは維持されている
- [ ] `chat_response` 実行後に `get_state(...)` で `chat_response_text` を含む最新 `SessionState` を取得できる
- [ ] `explanation_generation` 実行後に `get_state(...)` で `explanation_text` を含む最新 `SessionState` を取得できる
- [ ] interrupt 待機中でも `get_state(...)` がその時点の最新 `SessionState` を返す
- [ ] checkpoint 未作成の `thread_id` に対する `get_state(...)` は `LookupError` を送出する
- [ ] `get_state(...)` は latest `StateSnapshot.values` が mapping の場合に `{}` を含めてそのまま返し、欠落キーや個別フィールド型不一致を理由に追加の runtime schema validation を行わない
- [ ] `LookupError` は対象 `thread_id` に返却可能な checkpoint/root state が存在しない場合にだけ送出され、`StateSnapshot.values` の空/非空では分岐しない
- [ ] `RuntimeError` は checkpointer 未設定、state snapshot 読み出し失敗、または latest `StateSnapshot.values` が non-mapping の場合にだけ送出する
- [ ] `resume_session(...)` は seed state ではなく `get_state(...)` で取得した post-run state を authoritative に返す
- [ ] `resume_session(...)` は `resume_graph(...)` 成功後の `get_state(...)` 失敗を raw `LookupError` / `RuntimeError` のまま公開せず、`QuizSessionLifecycleError` に包んで cause chain を保持する
- [ ] `start_session(...)`、`record_answer(...)`、`complete_session(...)` は既存の戻り値契約を維持する
- [ ] この機能の harness scope は `backend/quiz/application/**` と `backend/quiz/domain/**` を再帰的に含む

# テスト観点メモ

各主要ルールに対して最低1つ、各境界条件に対して最低1つの観点を列挙する。
受け入れ基準の各項目が少なくとも1つの観点でカバーされていることを確認する。

- 正常系:
  - `GraphRunner` Protocol 準拠テストで `get_state` が必須メソッドとして存在することを確認する
  - `GraphRunner.get_state` が keyword-only の `thread_id` を要求し、既存 3 メソッドの署名と戻り値契約が維持されることを確認する
  - `QuizGraphRunner.get_state(thread_id="sess_001")` が latest checkpoint の `values` を mapping である限り `SessionState` としてそのまま返すことを確認する
  - `chat_response` ノード通過後の state 取得で `chat_response_text` が保存値そのままで返ることを確認する
  - `explanation_generation` ノード通過後の state 取得で `explanation_text` が保存値そのままで返ることを確認する
  - `SessionState.__annotations__` に 18 キーがあり、新規 2 キーの型が `str` であることを確認する
  - `resume_session(...)` が `resume_graph(...)` 成功後に同じ `thread_id` で `get_state(...)` を呼び、その戻り値を返すことを確認する
- 境界系:
  - interrupt 待機で graph が未完了の thread でも `get_state(...)` が partial `SessionState` を返すことを確認する
  - `chat_response_text` のみ更新された thread で `explanation_text` が未設定または既存値維持のまま返ることを確認する
  - `explanation_text` のみ更新された thread で `chat_response_text` が未設定または既存値維持のまま返ることを確認する
  - latest `StateSnapshot.values` が空 mapping `{}` でも `get_state(...)` がそのまま返し、`LookupError` にしないことを確認する
  - latest `StateSnapshot.values` が mapping だが `SessionState` の一部キー欠落または個別フィールド型不一致を含んでいても、`get_state(...)` 自身はその理由だけでは失敗させないことを確認する
- 異常系:
  - `thread_id=""` で `get_state(...)` を呼ぶと `ValueError` になることを確認する
  - checkpoint 未作成の `thread_id` で `get_state(...)` を呼ぶと `LookupError` になることを確認する
  - checkpointer 未設定または state snapshot 読取失敗時に `RuntimeError` になることを確認する
  - latest `StateSnapshot.values` が non-mapping のときに `RuntimeError` になることを確認する
  - `resume_graph(...)` は成功したが `get_state(...)` が `LookupError` または `RuntimeError` を送出した場合、`resume_session(...)` が `QuizSessionLifecycleError` を送出し、cause に元例外を保持することを確認する
