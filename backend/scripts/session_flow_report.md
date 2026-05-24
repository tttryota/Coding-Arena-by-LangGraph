# セッションフロー検証レポート

topic: TypeScript ジェネリクス / level: detail / 20 turns

## 確認ポイント (初期 5件)

| # | content | format |
|---|---------|--------|
| CP-1 | ジェネリクスの基本構文(`<T>`)を説明し、`any` との違いを型安全性の観点から説明できる | knowledge |
| CP-2 | 関数にジェネリクスを適用し、引数と戻り値の型の対応関係を保ったまま再利用可能な関数を設計できる | knowledge_and_practice |
| CP-3 | 複数の型パラメータや`extends`による制約を使い、受け取れる型を限定したジェネリック関数を設計できる | knowledge_and_practice |
| CP-4 | ジェネリックなクラスやインターフェースを用いて、内部データとメソッドの型整合性を保つ設計ができる | knowledge_and_practice |
| CP-5 | 型推論が働くケースと、明示的に型引数を指定すべきケースを区別し、適切に選択できる | knowledge |

## Turn 一覧

### Turn 1 | CP 1/5 | textarea | score=30 | deepdive

**出題:** TypeScriptのジェネリクスについて説明してください。`<T>`の基本構文の意味、ジェネリクスを使った関数の例、`any`と比べた型安全性の違い。

**回答:** よくわからないけど、型パラメータを使って汎用的にする仕組みだと思います

**評価:** 方向性は合っているが、`<T>`の説明、関数例、`any`との違いが未説明。deepdive 2件追加。

**deepdive追加:** CP-6(`<T>`の意味と`any`との違いを整理, knowledge), CP-7(型情報を保てる理由の説明, knowledge)

---

### Turn 2 | CP 2/7 | code | score=20 | deepdive

**出題:** `firstOrDefault` をジェネリクスで実装。配列`items`とデフォルト値を受け取り、空なら`defaultValue`を返す。

**回答:** ジェネリクスは関数やクラスに型パラメータTを付けて...(テキスト説明)

**評価:** コード問題にテキストで回答。`firstOrDefault`の実装なし。deepdive 2件追加。

**deepdive追加:** CP-8(firstOrDefaultの実装, knowledge_and_practice), CP-9(mapArray<T,U>の実装, knowledge_and_practice)

---

### Turn 3 | CP 3/9 | code | score=8 | deepdive

**出題:** `getValue`関数(extends制約)とジェネリッククラスの実装。複数型パラメータと`extends`制約を使用。

**回答:** function identity\<T>(arg: T): T { return arg; }

**評価:** identity関数は成立しているが要件と全く異なる。deepdive 2件追加。

**deepdive追加:** CP-10(keyofとT[K]の関係理解, knowledge), CP-11(getValueの実装, knowledge_and_practice)

---

### Turn 4 | CP 4/11 | code | score=12 | deepdive

**出題:** ジェネリックなインターフェースとクラスで`Repository`を設計。

**回答:** extendsを使うとTに制約を付けられます...(テキスト説明)

**評価:** extends制約の説明は一部正しいが、Repositoryの実装なし。deepdive 2件追加。

**deepdive追加:** CP-12(Repository<T,Id>設計, knowledge_and_practice), CP-13(Identifiable制約の実装, knowledge_and_practice)

---

### Turn 5 | CP 5/13 | textarea | score=12 | deepdive

**出題:** 型推論に任せるケースと型引数を明示すべきケースを、コード例を通して説明。

**回答:** 型パラメータTは呼び出し側で具体型に置き換わるため...(一般論)

**評価:** 型推論 vs 明示の区別が説明されていない。deepdive 2件追加。

**deepdive追加:** CP-14(型推論と明示の比較, knowledge), CP-15(identity呼び出しパターン, knowledge_and_practice)

---

### Turn 6 | CP 6/15 | textarea | score=8 | deepdive

**出題:** `identity<T>`のコードを題材に、`<T>`の意味、`T`が引数/戻り値で果たす役割、`any`との違いの3点を説明。

**回答:** ジェネリック型を活用すると、配列操作やAPIレスポンスの型定義などで型安全性と再利用性を両立できます。

**評価:** 一般論のみ。3つの必須ポイント未回答。deepdive 2件追加。

**deepdive追加:** CP-16(identity<T>の各部分の説明, knowledge), CP-17(any版との比較, knowledge)

---

### Turn 7 | CP 7/17 | textarea | score=9 | deepdive

**出題:** identityGenericとidentityAnyの2つの関数を比較して、`<T>`の意味、型安全性の具体的な違い、呼び出し後の型の差を説明。

**回答:** Promise\<T>やArray\<T>のように、標準ライブラリもジェネリクスで設計されており...

**評価:** 標準ライブラリの言及はあるが、必須3点未回答。deepdive 2件追加。

**deepdive追加:** CP-18(identityGenericのT説明, knowledge), CP-19(呼び出し後の型安全性比較, code)

---

### Turn 8 | CP 8/19 | code | score=4 | deepdive(budget制限で追加0件→next)

**出題:** `firstOrDefault`のジェネリック関数実装。

**回答:** 型パラメータに複数の制約を付ける場合はintersection型を使い...

**評価:** firstOrDefaultの実装なし。budget残り少→deepdive追加なしでnextにフォールバック。

---

### Turn 9-19 | CP 9-19/20 | 各種 | score=4-12 | 全て next

Turn 9以降は定型回答の繰り返し(「まとめると、ジェネリクスは型の抽象化手段であり...」)。全問低スコアだが、budget制限により deepdive は発動せず、`next` で順にCPを消化。

| Turn | CP | format | score | action |
|------|-----|--------|-------|--------|
| 9 | 9/20 | code | 10 | next |
| 10 | 10/20 | textarea | 12 | next |
| 11 | 11/20 | code | 6 | next |
| 12 | 12/20 | textarea | 10 | next |
| 13 | 13/20 | code | 8 | next |
| 14 | 14/20 | textarea | 10 | next |
| 15 | 15/20 | code | 8 | next |
| 16 | 16/20 | textarea | 12 | next |
| 17 | 17/20 | textarea | 10 | next |
| 18 | 18/20 | textarea | 12 | next |
| 19 | 19/20 | code | 7 | next |
| 20 | 20/20 | code | ? | complete |

### Turn 20 | CP 20/20 | code | complete

**出題:** ジェネリクスを使わない関数2つを書き、そのあとジェネリクスに置き換えて`firstOrDefault`を設計。

**回答:** まとめると、ジェネリクスは型の抽象化手段であり...

**結果:** `complete` 判定 → `progress_update` ノードに遷移。

初回実行ではスタブ不備(`update_roadmap_item_progress`メソッド未定義)でエラー終了。
スタブ修正後の再実行では LLM タイムアウト(一過性)で Turn 5-6 付近で停止(課題 C の事例)。
complete 判定自体は v4 実行で正常動作を確認済み。

## 確認ポイント最終状態

初期5件 + deepdive追加15件 = 合計20件。全て出題・消化された。

## 観察

### 良い点

1. **deepdive 爆発が制御された** — 各 turn 最大 2 件に制限、budget で上限到達後は追加なし
2. **重複なし** — 同一 (content, format) のポイントは追加されなかった
3. **complete に到達** — Turn 20 で全 CP 消化後、正しく complete に遷移
4. **answer_type_mismatch エラーなし** — format ルール改善が効いている
5. **フィードバック品質が高い** — 各 turn で具体的な不足点を指摘

### 課題

1. **テストの定型回答が全く問題に噛み合っていない** — code 問題にテキスト回答、問題内容と無関係な回答を繰り返すため全体的に低スコア
2. **Turn 8 の budget フォールバック** — deepdive 判定だが budget=0 で追加できず next に変換。仕様通りの動作だが、ユーザーには「deepdive したかったのに進んだ」と見える可能性
3. **progress_update のスタブ不備** — 検証スクリプトの `StubProgressStore` のメソッド名が実装と不一致 → **修正済み**
4. **一過性 LLM エラーでセッション喪失** — スタブ修正後の再実行で codex app-server タイムアウトが発生し Turn 5-6 で停止。課題 C の実例。現在の設計ではリトライ不可
