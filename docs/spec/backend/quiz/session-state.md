---
feature: quiz/session-state
status: ready
---

# 概要

- LangGraph 上でクイズ機能を構成する全ノードが、同一のインメモリ共有ステートを安全に読み書きできるようにする。
- 既存の概要資料ではフィールド名と役割が要約されているため、本仕様では `backend/quiz/domain/session_state.py` に置く TypedDict 契約を、他資料なしで実装できる粒度まで具体化する。
- 利用者は `backend/quiz/application/` 配下の LangGraph ノード実装、グラフ組み立て処理、型検査を行うテストコードである。
- 前提条件:
  - 実装はドメイン層に置き、I/O・DB・LLM 呼び出しを含めない。
  - `SessionState` はグラフ実行中の状態のみを表し、永続化エンティティそのものは表さない。
  - `SessionState` は全ノードで共有されるが、各キーはノード進行に応じて段階的に設定される。
  - 本仕様の実装先は `backend/quiz/domain/session_state.py` のみとする。

# 入出力

- 入力:
  - LangGraph ランタイムが保持する `dict` オブジェクト。
  - 各ノードが読み書きする共有状態キー。
  - `confirmation_points` に格納する `ConfirmationPoint` レコード。
  - `answers` に格納する `QuizAnswerRecord` レコード。
- 出力:
  - `SessionState` TypedDict
    - 16 フィールドを定義する。
    - 各フィールドはキー名・値型・値集合を本仕様どおりに持つ。
    - 段階的初期化を許容するため、未設定フェーズのキーは未保持を許容する。
  - `ConfirmationPoint` TypedDict
    - 確認ポイント 1 件分の完全レコードを表す。
  - `QuizAnswerRecord` TypedDict
    - 問答記録 1 件分の完全レコードを表す。
- エラー:
  - なし: 本機能は型定義のみを提供し、独自例外を送出する生成関数・検証関数・変換関数は定義しない。

# 具体例

## 例1

- 入力:
  - `C2` 問題セット設計ノード終了直後の共有ステートを型で表現したい。
  - まだ `C3` 出題前なので、現在の問題文・回答形式・最新ユーザー入力は未設定。
- 期待される出力:
  - `SessionState` は以下のような部分状態を許容する。

```python
state: SessionState = {
    "session_id": "sess_001",
    "roadmap_item_id": "ri_generics_01",
    "roadmap_item_level": "middle",
    "roadmap_item_title": "TypeScript ジェネリクス",
    "roadmap_item_description": "型パラメータと推論の理解を確認する",
    "is_resumed": False,
    "confirmation_points": [
        {
            "id": "cp_001",
            "content": "ジェネリクスの必要性を説明できる",
            "format": "knowledge",
        },
        {
            "id": "cp_002",
            "content": "ジェネリック関数を実装できる",
            "format": "knowledge_and_practice",
        },
    ],
    "current_point_index": 0,
}
```

## 例2

- 入力:
  - `C4` 回答評価ノード終了直後の共有ステートを型で表現したい。
  - 1問目の回答を評価した結果、深掘りが必要と判断された。
- 期待される出力:
  - `SessionState` は既存の `confirmation_points` を保持したまま末尾追記を許容し、`answers` は追記済み、`next_action` は `"deepdive"` を保持する。
  - `current_point_index` は回答済みの `cp_001` を消化した次位置である `1` を指すため、次の `C3` は既存の `cp_002` を出題する。追記した `cp_002_deepdive_01` は既存の未消化ポイントを消化した後に出題される。
  - `input_source="form"` のため `input_classification` は経由しないが、`C4` 終了時点では `input_type="answer"` が確定している。
  - `total_questions_asked` は `1` であり 20問未満なので、この例では `deepdive` が downstream 契約上も有効である。

```python
state: SessionState = {
    "session_id": "sess_001",
    "roadmap_item_id": "ri_generics_01",
    "roadmap_item_level": "middle",
    "roadmap_item_title": "TypeScript ジェネリクス",
    "roadmap_item_description": "型パラメータと推論の理解を確認する",
    "is_resumed": False,
    "confirmation_points": [
        {
            "id": "cp_001",
            "content": "ジェネリクスの必要性を説明できる",
            "format": "knowledge",
        },
        {
            "id": "cp_002",
            "content": "ジェネリック関数を実装できる",
            "format": "knowledge_and_practice",
        },
        {
            "id": "cp_002_deepdive_01",
            "content": "型推論を使う利点を具体例で説明できる",
            "format": "knowledge",
        },
    ],
    "current_point_index": 1,
    "current_question_text": "なぜジェネリクスが必要なのか説明してください。",
    "current_answer_type": "textarea",
    "user_input": "いろいろな型で同じ関数を書けるからです。",
    "input_source": "form",
    "input_type": "answer",
    "next_action": "deepdive",
    "answers": [
        {
            "question_number": 1,
            "confirmation_point_id": "cp_001",
            "question_text": "なぜジェネリクスが必要なのか説明してください。",
            "answer_type": "textarea",
            "answer_text": "いろいろな型で同じ関数を書けるからです。",
            "score": 62,
            "feedback": "再利用性には触れられていますが、型安全性の説明が不足しています。",
        }
    ],
    "total_questions_asked": 1,
}
```

## 例3

- 入力:
  - 20問目の回答評価ノード終了直後の共有ステートを型で表現したい。
  - 既存の未消化確認ポイントは残っているが、20問到達済みなので追加 deepdive は許容しない。
- 期待される出力:
  - `SessionState` の deliverable 自体は partial TypedDict のままだが、workflow 契約として `next_action` は `"next"` または `"complete"` のみを有効状態とする。
  - 下記の例では `"next"` を保持し、`confirmation_points` への deepdive 用追記は行わない。
  - `SessionState` 単体は runtime validator を持たないため、この制約は `answer_evaluation` と downstream ノードの文書上の契約として扱う。

```python
state: SessionState = {
    "session_id": "sess_020",
    "confirmation_points": [
        {
            "id": "cp_020",
            "content": "型制約の使い分けを説明できる",
            "format": "knowledge",
        },
        {
            "id": "cp_021",
            "content": "複数の型引数を持つ関数を実装できる",
            "format": "knowledge_and_practice",
        },
    ],
    "current_point_index": 1,
    "input_source": "form",
    "input_type": "answer",
    "next_action": "next",
    "answers": [
        {
            "question_number": 20,
            "confirmation_point_id": "cp_020",
            "question_text": "型制約を使う場面を説明してください。",
            "answer_type": "textarea",
            "answer_text": "受け取る型に最低限必要な性質を絞りたいときです。",
            "score": 70,
            "feedback": "要点は押さえています。追加深掘りではなく既存の未消化ポイントへ進みます。",
        }
    ],
    "total_questions_asked": 20,
}
```

# 主要ルール

1. SessionState の公開契約:
   - 条件:
     - `backend/quiz/domain/session_state.py` に共有ステート型を定義する。
   - 振る舞い:
     - 公開する TypedDict は `SessionState`、`ConfirmationPoint`、`QuizAnswerRecord` の 3 つのみとする。
     - `SessionState` は全 LangGraph ノードが共通利用する状態型とする。
     - `SessionState` はちょうど 16 フィールドを定義し、キー名は以下に固定する。
       - `session_id`
       - `roadmap_item_id`
       - `roadmap_item_level`
       - `roadmap_item_title`
       - `roadmap_item_description`
       - `is_resumed`
       - `confirmation_points`
       - `current_point_index`
       - `current_question_text`
       - `current_answer_type`
       - `user_input`
       - `input_source`
       - `input_type`
       - `next_action`
       - `answers`
       - `total_questions_asked`

2. 段階的初期化:
   - 条件:
     - ステートは `C1` セッション開始、`C2` 問題セット設計、`C3` 出題、`input_source="chat"` では入力分類、`input_source="form"` ではそのまま `C4` 回答評価、の順で段階的に埋まる。
   - 振る舞い:
     - `SessionState` は初期フェーズで未設定のキーを持たない部分状態を許容する。
     - キーが未設定でよいのは、そのキーを書き込む責務を持つノードがまだ実行されていない間だけとする。
     - `ConfirmationPoint` と `QuizAnswerRecord` はリストへ追加される時点で全必須フィールドを埋めた完全レコードとする。

3. フィールド型の厳密性:
   - 条件:
     - 各キーの型注釈を定義する。
   - 振る舞い:
     - 以下の型契約を厳守する。

| フィールド | 型 |
|---|---|
| `session_id` | `str` |
| `roadmap_item_id` | `str` |
| `roadmap_item_level` | `Literal["detail", "middle", "major"]` |
| `roadmap_item_title` | `str` |
| `roadmap_item_description` | `str` |
| `is_resumed` | `bool` |
| `confirmation_points` | `list[ConfirmationPoint]` |
| `current_point_index` | `int` |
| `current_question_text` | `str` |
| `current_answer_type` | `Literal["textarea", "code"]` |
| `user_input` | `str` |
| `input_source` | `Literal["form", "chat"]` |
| `input_type` | `Literal["answer", "question", "explanation_request"]` |
| `next_action` | `Literal["next", "deepdive", "complete"]` |
| `answers` | `list[QuizAnswerRecord]` |
| `total_questions_asked` | `int` |

4. サブ型の構造:
   - 条件:
     - `confirmation_points` と `answers` の要素型を定義する。
   - 振る舞い:
     - `ConfirmationPoint` は以下 3 フィールドの完全レコードとする。

| フィールド | 型 |
|---|---|
| `id` | `str` |
| `content` | `str` |
| `format` | `Literal["knowledge", "knowledge_and_practice"]` |

     - `QuizAnswerRecord` は以下 7 フィールドの完全レコードとする。

| フィールド | 型 |
|---|---|
| `question_number` | `int` |
| `confirmation_point_id` | `str` |
| `question_text` | `str` |
| `answer_type` | `Literal["textarea", "code"]` |
| `answer_text` | `str` |
| `score` | `int` |
| `feedback` | `str` |

5. ノードごとの書き込み責務:
   - 条件:
     - 複数ノードが同一ステートを共有する。
   - 振る舞い:
     - 各キーの初回設定責務は以下に固定する。

| キー | 初回設定責務 |
|---|---|
| `session_id` | `C1` セッション開始 |
| `roadmap_item_id` | `C1` セッション開始 |
| `roadmap_item_level` | `C1` セッション開始 |
| `roadmap_item_title` | `C1` セッション開始 |
| `roadmap_item_description` | `C1` セッション開始 |
| `is_resumed` | `C1` セッション開始 |
| `confirmation_points` | `C2` 問題セット設計 |
| `current_point_index` | `C2` 問題セット設計 |
| `current_question_text` | `C3` 出題 |
| `current_answer_type` | `C3` 出題 |
| `user_input` | 外部入力受付 |
| `input_source` | 外部入力受付 |
| `input_type` | 入力分類（`chat`） / `C4` 回答評価（`form` で `"answer"` を正規化） |
| `next_action` | `C4` 回答評価 |
| `answers` | `C4` 回答評価 |
| `total_questions_asked` | `C3` 出題 |

     - 追記・更新の扱いは以下に固定する。
       - `answers` は追記のみとし、既存要素の上書き・削除は行わない。
       - `confirmation_points` は `C2` の初期設定後、`C4` が深掘り時に末尾追記のみ行える。
       - `total_questions_asked` は `C3` が出題のたびに増やす。

6. 条件付き状態組み合わせの責務境界:
   - 条件:
     - deliverable は `SessionState` という single partial TypedDict と、`ConfirmationPoint` / `QuizAnswerRecord` という complete record のみである。
   - 振る舞い:
     - `SessionState` が型として表すのは、キー名、各キーの値型、partial / complete の区別までとする。
     - `input_source` / `input_type` / `next_action` / `current_point_index` / `confirmation_points` の条件付き組み合わせは、TypedDict 単体で自動検証する対象ではなく、downstream ノードの文書上の契約として扱う。
     - 本モジュールは phase別 TypedDict、Union、runtime validator、生成ヘルパーを提供しない。

7. downstream ノードの状態組み合わせ契約:
   - 条件:
     - `SessionState` を読む `C3`、`input_classification`、`answer_evaluation`、およびその downstream ノードが同じ共有状態を解釈する。
   - 振る舞い:
     - `input_type` は `input_source="chat"` では入力分類ノードが `answer` / `question` / `explanation_request` のいずれかを初回設定する。`input_source="form"` では `C4` 開始時点の未設定を許容するが、`C4` 終了時には必ず `"answer"` を保持する。
     - `input_source="form"` かつ `input_type` が `"question"` または `"explanation_request"` の評価完了状態は有効状態として扱わない。
     - `current_point_index` は次に出題する未消化確認ポイント位置を表し、`C4` は現在問を消化したうえで `next_action` に応じて更新する。
     - `next_action="next"` のとき、`current_point_index` は 1 進む。
     - `next_action="deepdive"` のとき、生成した deepdive 確認ポイントを `confirmation_points` の末尾へ追記し、`current_point_index` は 1 進む。したがって既存の未消化確認ポイントが残っていればそれを先に出題し、残っていなければ末尾追記した deepdive ポイントが次問になる。
     - `next_action="complete"` のとき、`current_point_index == len(confirmation_points)` を満たす完了境界へ更新する。
     - `total_questions_asked == 20` に到達した評価完了状態では、`next_action` は `"next"` または `"complete"` に限る。`"deepdive"` を有効状態として扱わず、その評価で deepdive 用 `confirmation_points` を新規追記しない。

8. スコープ境界:
   - 条件:
     - セッション永続化や外部応答が別責務として存在する。
   - 振る舞い:
     - `SessionState` には DB エンティティオブジェクト、RAG 検索結果、LLM レスポンス全文、レスポンス DTO を保持しない。
     - `QuizSession` や `QuizAnswer` の永続化はインフラ層の責務であり、本モジュールには永続化用フィールドを追加しない。

# 境界条件

- ケース:
  - `answers` が未設定、または空リストのまま `C3` が初回出題を行う。
  - 振る舞い:
    - 有効な状態として扱う。
    - `answers` が存在する場合、その値は `[]` を許容する。
  - 理由:
    - 初回出題前には回答履歴が存在しないため。
- ケース:
  - `current_question_text`、`current_answer_type`、`total_questions_asked` が `C3` 実行前で未設定である。
  - 振る舞い:
    - 有効な部分状態として扱う。
  - 理由:
    - 出題前にダミー値を強制すると、ステート契約が実行順序と乖離するため。
- ケース:
  - `current_point_index` が `len(confirmation_points)` と等しく、次に出題する確認ポイントが存在しない。
  - 振る舞い:
    - 完了境界の有効状態として扱う。
    - この状態では `C3` が追加出題前提で直接参照してはならず、完了遷移判断が優先される。
  - 理由:
    - 全確認ポイント消化後に完了へ進む境界を表現するため。
- ケース:
  - `next_action="deepdive"` の直後に、次の `C3` がどの確認ポイントを出題するかを判定したい。
  - 振る舞い:
    - `current_point_index` が指す要素を次問とする。
    - deepdive 確認ポイントは `confirmation_points` の末尾へ追記されるため、`current_point_index` が既存要素を指していれば既存ポイントを先に出題し、末尾を指していれば追記済み deepdive ポイントを出題する。
  - 理由:
    - `confirmation_points` と `current_point_index` だけで次問決定を一意にするため。
- ケース:
  - `total_questions_asked` が `len(answers)` より 1 大きい。
  - 振る舞い:
    - 有効な状態として扱う。
  - 理由:
    - `C3` が新しい問題を出した直後は、出題数だけ先に増え、回答履歴はまだ追記されていないため。
- ケース:
  - `input_source` が `"form"` のとき、`input_type` の有無を downstream が判断したい。
  - 振る舞い:
    - 外部入力受付直後から `C4` 開始前までは、`input_type` 未設定を有効な部分状態として扱う。
    - `C4` 実行中の `form` 経路は回答専用入力として評価され、`C4` 終了時には `input_type="answer"` を必須とする。
    - `input_source="form"` かつ `input_type` が `"question"` または `"explanation_request"` の評価完了状態は有効状態として扱わない。
  - 理由:
    - `form` は入力分類を経由しない一方、評価完了後の共有ステートでは回答として正規化された状態を downstream が前提にできる必要があるため。
- ケース:
  - `total_questions_asked` が `20` に到達した直後の評価完了状態を downstream が判断したい。
  - 振る舞い:
    - 有効状態として扱う `next_action` は `"next"` または `"complete"` のみとする。
    - その評価で deepdive 用 `confirmation_points` を新規追記した状態は有効状態として扱わない。
  - 理由:
    - `quiz-overview.md` の 20問収束ルールに従い、20問到達後は追加 deepdive ではなく既存ポイント消化または完了へ収束させる必要があるため。
- ルール間の相互作用:
  複数ルールが同時に適用される場合は、`段階的初期化` を最優先とする。つまり、未実行ノードが責務を持つキーは未設定でよい。一方で、いったん `confirmation_points` や `answers` に追加される要素は `サブ型の構造` ルールに従い完全レコードでなければならない。`input_source="form"` の `input_type` は `C4` 完了まで未設定を許容するが、`next_action` や `answers` が更新された評価完了状態では `"answer"` を保持する。完了境界では `current_point_index == len(confirmation_points)` を許容するが、その時点でも既に設定済みの `answers` や `total_questions_asked` は保持される。`total_questions_asked == 20` の評価完了状態では、上記よりも 20問収束ルールを優先し、`deepdive` と deepdive 用追記を有効状態として扱わない。

# 非機能・制約

- 性能:
  - 型定義のみを扱うため、実行時計算量を増やす処理を持たない。
  - ノード間で大きなオブジェクト複製を前提としない。
- 可観測性:
  - 本モジュール自身はログ出力を持たない。
  - 監視対象は型契約の一貫性であり、検証はテストと静的型検査で行う。
- 外部依存:
  - Python の `typing` / `typing_extensions` 相当の型機能。
  - LangGraph の共有 state として `dict` 互換オブジェクトを受け取る呼び出し規約。
  - 他コンポーネントへの依存はインターフェース参照のみとし、具体実装への import を増やさない。

# モジュール構成

- 構成方針:
  - `単一ファイルで実装する`
- 概算メモ:
  - 構成要素は TypedDict 3 件、Literal 型エイリアス、公開名整理のみである。
  - ランタイム検証・例外型・ログ・I/O を含めないため、100 行未満に収まる見込みである。
  - 200-300 行を超える責務分割要因が存在しないため、分割は不要である。
- モジュール一覧:
  - `backend/quiz/domain/session_state.py`
    - 責務:
      - `SessionState`、`ConfirmationPoint`、`QuizAnswerRecord` の公開型定義を提供する。
    - 含める要素:
      - `Literal` による値集合定義
      - `TypedDict` 3 件
      - 必要に応じた `TypeAlias` または `__all__`

# 技術判断

- 判断:
  - `SessionState` は段階的構築を表せる partial TypedDict とする。
  - 理由:
    - `C1` から `C4` まで各ノードで設定タイミングが異なり、全キー必須の total TypedDict では初期ノードにダミー値が必要になるため。
- 判断:
  - `ConfirmationPoint` と `QuizAnswerRecord` は complete record とする。
  - 理由:
    - リスト要素として追加された時点で、後続ノードが欠損なく参照できる必要があるため。
- 判断:
  - 値集合は `Enum` ではなく `Literal` を優先する。
  - 理由:
    - LangGraph state、LLM プロンプト、フロントエンドとの文字列契約をそのまま表現でき、変換層を増やさずに済むため。
- 判断:
  - バリデーション関数や生成ヘルパーを同モジュールに追加しない。
  - 理由:
    - 本機能の責務は共有ステート型の定義に限定されており、ロジックを混ぜるとドメイン層の責務境界が曖昧になるため。
- 判断:
  - `input_source="form"` 時の正規化、`next_action` ごとの `current_point_index` 更新、20問収束などの条件付きルールは型注釈ではなく文書上の workflow 契約として扱う。
  - 理由:
    - deliverable を single partial TypedDict と complete record 2件に限定しつつ、downstream が有効 / 無効な状態組み合わせを一意に判断できるようにするため。

# スコープ外

- 対応しないこと:
  - LangGraph ノード実装そのもの
  - セッション開始・再開・完了のアプリケーションロジック
  - `SessionState` のランタイム検証関数
  - DB への保存形式や ORM モデル定義
  - フロントエンド向けレスポンス DTO の設計

# 受け入れ基準

- [ ] `backend/quiz/domain/session_state.py` に `SessionState`、`ConfirmationPoint`、`QuizAnswerRecord` が定義されている
- [ ] `SessionState` が 16 個のフィールドを持ち、キー名が本仕様と完全一致している
- [ ] `roadmap_item_level`、`current_answer_type`、`input_source`、`input_type`、`next_action`、`ConfirmationPoint.format` の値集合が本仕様の Literal と一致している
- [ ] `SessionState` が段階的初期化を許容する契約になっている
- [ ] `ConfirmationPoint` と `QuizAnswerRecord` が完全レコードとして定義されている
- [ ] `answers` が追記のみ、`confirmation_points` が初期設定後は深掘り追記のみという責務境界が仕様化されている
- [ ] 条件付き状態組み合わせが downstream ノードの文書契約であり、本モジュールが phase別 TypedDict、Union、runtime validator、生成ヘルパーを提供しないことが明記されている
- [ ] `input_source="form"` 時の `input_type` 正規化、`next_action` ごとの `current_point_index` 更新、20問収束ルールが型受け入れ基準ではなく文書契約として整合している
- [ ] 永続化専用フィールドや I/O 依存オブジェクトが `SessionState` に含まれていない
- [ ] 主要ルールが満たされる
- [ ] 境界条件が期待どおりに定義されている
- [ ] 具体例から期待結果を一意に判断できる

# テスト観点メモ

各主要ルールに対して最低1つ、各境界条件に対して最低1つの観点を列挙する。
受け入れ基準の各項目が少なくとも1つの観点でカバーされていることを確認する。

- 正常系:
  - `SessionState` の `__annotations__` に 16 キーが存在し、名称が一致することを確認する。
  - `ConfirmationPoint` の 3 フィールドと `QuizAnswerRecord` の 7 フィールドが一致することを確認する。
  - `roadmap_item_level` などの Literal 値集合が仕様どおりであることを確認する。
  - `SessionState` を `C2` 時点の部分状態で型利用できることを確認する。
  - `SessionState` を `C4` 時点の完全に近い状態で型利用できることを確認する。
  - `SessionState` を `C4` 時点の全キー設定済み状態で型利用できることを確認する。
- 境界系:
  - `answers=[]` を持つ初回出題前後の状態が許容されることを確認する。
  - `current_question_text` 未設定の `C2` 直後状態が許容されることを確認する。
  - `current_point_index == len(confirmation_points)` の完了境界状態を表現できることを確認する。
  - `total_questions_asked == len(answers) + 1` の出題直後状態を表現できることを確認する。
  - `input_source="form"` かつ `input_type` 未設定の外部入力直後状態を表現できることを確認する。
  - `input_source="form"` かつ `input_type` 未設定の状態を partial TypedDict として表現できることを確認する。
- 異常系:
  - `roadmap_item_level="micro"` のような仕様外文字列を静的型検査で拒否できることを確認する。
  - `ConfirmationPoint.format="practice_only"` のような仕様外文字列を静的型検査で拒否できることを確認する。
  - `QuizAnswerRecord` に `feedback` 欠損がある場合を完全レコード違反として検出できることを確認する。
  - `SessionState` のフィールド数が正確に 16 であることを確認する。
