---
status: ready
---

# テストケース一覧

# 検証焦点

| テストの種類 | 検証焦点 |
|---|---|
| Phase 1（型構造） | `SessionState` 16フィールドの名称・型一致、`ConfirmationPoint` 3フィールド、`QuizAnswerRecord` 7フィールド、Literal値集合 |
| Phase 2（partial/complete） | `SessionState` が partial TypedDict、`ConfirmationPoint` / `QuizAnswerRecord` が complete record、段階的初期化の許容 |
| Phase 3（境界状態の表現） | 空answers、未設定キー、完了境界index、出題直後のquestions_asked/answers差分 |

## Phase 1: 型構造

| ID | 観点 | 前提 | 入力 | 期待結果 | 備考 |
|---|---|---|---|---|---|
| TC-01 | `SessionState` の公開契約と16フィールドの名称を検証する | `quiz.domain.session_state` を import できる | `SessionState.__annotations__` を取得する | `SessionState` の `__annotations__` にちょうど16個のキーが存在する。キー名は `session_id`, `roadmap_item_id`, `roadmap_item_level`, `roadmap_item_title`, `roadmap_item_description`, `is_resumed`, `confirmation_points`, `current_point_index`, `current_question_text`, `current_answer_type`, `user_input`, `input_source`, `input_type`, `next_action`, `answers`, `total_questions_asked` と完全一致する | `__module__` が `quiz.domain.session_state` であることも確認する |
| TC-02 | `ConfirmationPoint` の3フィールドと `QuizAnswerRecord` の7フィールドを検証する | `quiz.domain.session_state` を import できる | 各 TypedDict の `__annotations__` を取得する | `ConfirmationPoint` の `__annotations__` にちょうど3個のキーが存在し、`id`(str), `content`(str), `format`(Literal) と一致する。`QuizAnswerRecord` の `__annotations__` にちょうど7個のキーが存在し、`question_number`(int), `confirmation_point_id`(str), `question_text`(str), `answer_type`(Literal), `answer_text`(str), `score`(int), `feedback`(str) と一致する | 両TypedDictの `__module__` も確認する |
| TC-03 | Literal値集合が仕様と完全一致することを検証する | `typing.get_args()` で Literal 引数を取得できる | 6つのLiteralフィールドの型引数を取得する | `roadmap_item_level`: `("detail", "middle", "major")`。`current_answer_type`: `("textarea", "code")`。`input_source`: `("form", "chat")`。`input_type`: `("answer", "question", "explanation_request")`。`next_action`: `("next", "deepdive", "complete")`。`ConfirmationPoint.format`: `("knowledge", "knowledge_and_practice")`。`QuizAnswerRecord.answer_type`: `("textarea", "code")`。各Literalの値集合は順序不問でセット一致とする | 仕様外の値（例: `"practice"`, `"abandoned"`）が含まれていないことも確認する |

## Phase 2: partial/complete TypedDict

| ID | 観点 | 前提 | 入力 | 期待結果 | 備考 |
|---|---|---|---|---|---|
| TC-10 | `SessionState` が partial TypedDict（`total=False`）であることを検証する | `typing.get_type_hints()` を使用できる | `SessionState.__required_keys__` と `SessionState.__optional_keys__` を取得する | `SessionState.__required_keys__` が空集合 `frozenset()` であり、`SessionState.__optional_keys__` がちょうど16個のキーを含む。つまり全フィールドがオプショナルである | `total=False` の TypedDict は全キーが `__optional_keys__` に入る |
| TC-11 | C2時点の部分状態（8フィールドのみ）が有効な `SessionState` として構築できる | テストコード内で部分的な dict を作成する | 仕様書 例1 のデータ（`session_id`, `roadmap_item_id`, `roadmap_item_level`, `roadmap_item_title`, `roadmap_item_description`, `is_resumed`, `confirmation_points`, `current_point_index` の8フィールドのみ）を `SessionState` 型の変数に代入する | 代入が成功し、各フィールドの値が入力と一致する。`current_question_text` 等の未設定キーは dict に含まれない | partial TypedDict なので mypy も通る |
| TC-12 | `ConfirmationPoint` が complete record（`total=True`）であることを検証する | `ConfirmationPoint.__required_keys__` を取得できる | `ConfirmationPoint.__required_keys__` と `ConfirmationPoint.__optional_keys__` を取得する | `ConfirmationPoint.__required_keys__` がちょうど3個のキー（`id`, `content`, `format`）を含み、`__optional_keys__` が空集合である | リスト追加時に全フィールド必須を保証する |
| TC-13 | `QuizAnswerRecord` が complete record（`total=True`）であることを検証する | `QuizAnswerRecord.__required_keys__` を取得できる | `QuizAnswerRecord.__required_keys__` と `QuizAnswerRecord.__optional_keys__` を取得する | `QuizAnswerRecord.__required_keys__` がちょうど7個のキー（`question_number`, `confirmation_point_id`, `question_text`, `answer_type`, `answer_text`, `score`, `feedback`）を含み、`__optional_keys__` が空集合である | リスト追加時に全フィールド必須を保証する |

## Phase 3: 境界状態の表現

| ID | 観点 | 前提 | 入力 | 期待結果 | 備考 |
|---|---|---|---|---|---|
| TC-20 | `answers=[]` の初回出題前状態が構築できる | partial TypedDict で部分状態を作成する | 仕様書 例1 の8フィールド（`session_id="sess_001"`, `roadmap_item_id="ri_generics_01"`, `roadmap_item_level="middle"`, `roadmap_item_title="TypeScript ジェネリクス"`, `roadmap_item_description="型パラメータと推論の理解を確認する"`, `is_resumed=False`, `confirmation_points=[{id="cp_001", content="ジェネリクスの必要性を説明できる", format="knowledge"}, {id="cp_002", content="ジェネリック関数を実装できる", format="knowledge_and_practice"}]`, `current_point_index=0`）に `answers=[]` を追加した9フィールドの dict を `SessionState` 型変数に代入する | 代入が成功する。`state["answers"]` が空リスト `[]` であり `len(state["answers"]) == 0` が `True` である。dict のキー数は9である | 初回出題前に回答履歴が存在しないケース |
| TC-21 | `current_point_index == len(confirmation_points)` の完了境界が表現できる | partial TypedDict で完了直前状態を作成する | `confirmation_points=[{id="cp_001", content="ジェネリクスの必要性を説明できる", format="knowledge"}, {id="cp_002", content="ジェネリック関数を実装できる", format="knowledge_and_practice"}]`, `current_point_index=2` を含む dict を `SessionState` 型変数に代入する | 代入が成功する。`state["current_point_index"] == len(state["confirmation_points"])` が `True` であり、値は `2 == 2` である | 全確認ポイント消化後の完了境界 |
| TC-22 | `total_questions_asked == len(answers) + 1` の出題直後状態が表現できる | partial TypedDict で C3 出題直後状態を作成する | `answers=[{question_number=1, confirmation_point_id="cp_001", question_text="なぜジェネリクスが必要なのか説明してください。", answer_type="textarea", answer_text="いろいろな型で同じ関数を書けるからです。", score=62, feedback="再利用性には触れられていますが、型安全性の説明が不足しています。"}]`, `total_questions_asked=2`, `current_question_text="ジェネリック関数を1つ実装してください。"`, `current_answer_type="code"` を含む dict を `SessionState` 型変数に代入する | 代入が成功する。`state["total_questions_asked"] == len(state["answers"]) + 1` が `True` であり、値は `2 == 1 + 1` である | C3出題直後は出題数が回答数より1大きい |
| TC-23 | C4完了時点の全キー設定済み状態が構築できる | 仕様書 例2 のデータを使用する | 仕様書 例2 の全16フィールド（`session_id="sess_001"`, `roadmap_item_id="ri_generics_01"`, `roadmap_item_level="middle"`, `roadmap_item_title="TypeScript ジェネリクス"`, `roadmap_item_description="型パラメータと推論の理解を確認する"`, `is_resumed=False`, `confirmation_points`=3件, `current_point_index=1`, `current_question_text="なぜジェネリクスが必要なのか説明してください。"`, `current_answer_type="textarea"`, `user_input="いろいろな型で同じ関数を書けるからです。"`, `input_source="form"`, `input_type="answer"`, `next_action="deepdive"`, `answers`=1件, `total_questions_asked=1`）を持つ dict を `SessionState` 型変数に代入する | 代入が成功し、dict のキー数が16である。全フィールドの値が仕様書 例2 と完全一致する | 最大状態の表現確認 |

# 網羅性チェック

| 受け入れ基準 | 対応テストケース |
|---|---|
| `backend/quiz/domain/session_state.py` に `SessionState`、`ConfirmationPoint`、`QuizAnswerRecord` が定義されている | TC-01, TC-02 |
| `SessionState` が 16 個のフィールドを持ち、キー名が本仕様と完全一致している | TC-01 |
| `roadmap_item_level`、`current_answer_type`、`input_source`、`input_type`、`next_action`、`ConfirmationPoint.format` の値集合が本仕様の Literal と一致している | TC-03 |
| `SessionState` が段階的初期化を許容する契約になっている | TC-10, TC-11 |
| `ConfirmationPoint` と `QuizAnswerRecord` が完全レコードとして定義されている | TC-12, TC-13 |
| `answers` が追記のみ、`confirmation_points` が初期設定後は深掘り追記のみという責務境界が仕様化されている | TC-20, TC-21 |
| 条件付き状態組み合わせが downstream ノードの文書契約であり、本モジュールが phase別 TypedDict、Union、runtime validator、生成ヘルパーを提供しないことが明記されている | TC-10（partial TypedDict の検証で間接確認） |
| 永続化専用フィールドや I/O 依存オブジェクトが `SessionState` に含まれていない | TC-01（フィールド数が正確に16であることで間接確認） |
| 具体例から期待結果を一意に判断できる | TC-11, TC-23 |
