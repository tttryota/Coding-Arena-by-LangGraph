# ruff ルール解説

`backend/pyproject.toml` で有効化している ruff ルールの解説。
各ルールが何を検出し、なぜ必要かを記載する。

## 基本ルール

### E / W — pycodestyle
PEP 8 準拠のスタイルチェック。インデント、空白、改行などの基本フォーマット。
`ruff format` と重複する E501（行長）は ignore 設定で無効化済み。

### F — Pyflakes
未使用の import、未定義変数、到達不能コードなど、論理的なエラーの検出。

### I — isort
import 文の並び順を強制。標準ライブラリ → サードパーティ → ローカルの順。
auto-fix 可能。

### UP — pyupgrade
古い Python 構文を新しい書き方に自動変換。例: `dict()` → `{}`、`Optional[X]` → `X | None`。
Python 3.12 をターゲットに設定済み。auto-fix 可能。

### B — flake8-bugbear
バグになりやすいパターンの検出。例: ミュータブルなデフォルト引数 (`def f(x=[])`）、
`except Exception:` の後に `raise` なしの処理。

### A — flake8-builtins
`list`, `dict`, `id` など Python 組み込み名のシャドウイングを検出。
変数名やパラメータ名で組み込み名を上書きすると予期しない挙動の原因になる。

### RUF — Ruff 固有
Ruff 独自のルール。不要な `noqa` コメント、型変換の簡素化など。

### COM — flake8-commas
末尾カンマの強制。複数行のリスト・辞書・関数引数で末尾カンマがないと、
行追加時の diff が不必要に大きくなる。auto-fix 可能。

### PTH — flake8-use-pathlib
`os.path` の使用を検出し、`pathlib.Path` の使用を推奨。
Python 3.12 では pathlib が推奨される標準的なファイル操作 API。

## セキュリティ

### S — flake8-bandit
セキュリティ上の問題を検出。`eval()` の使用、ハードコードされたパスワード、
安全でないハッシュアルゴリズム、`subprocess` の shell=True など。
テストファイルでは S101（assert 使用）を除外済み。

## コード品質

### T20 — flake8-print
`print()` 文の検出。本番コードでは print ではなくロギングを使うべき。
デバッグ用の print 文の消し忘れ防止。

### N — pep8-naming
PEP 8 の命名規則を強制。クラス名は PascalCase、関数・変数名は snake_case、
定数は UPPER_SNAKE_CASE。テストファイルでは除外済み（テスト名に日本語やアンダースコアを使うため）。

### PLR0913 — 引数数制限（max-args=4）
関数の引数が 4 つを超えると検出。引数が多い関数は理解しにくく、
呼び出し時にミスが起きやすい。dataclass や TypedDict にまとめることを促す。
auto-fix 不可。

### PLR0915 — 文数制限（max-statements=20）
関数内の文（statement）が 20 を超えると検出。review-criteria の「30行以内」の近似。
行数ではなく文数ベースのため、複数行に渡る式は 1 文としてカウントされる。
auto-fix 不可。

### C901 — McCabe 複雑度（max-complexity=10）
関数の分岐数（if, for, while, except, and, or 等）を数え、複雑度が 10 を超えると検出。
複雑な関数は理解・テスト・保守が困難。分割のシグナルとして使用。
auto-fix 不可。

### BLE — flake8-blind-except
`except Exception:` や `except BaseException:` のような広すぎる例外キャッチを検出。
`KeyboardInterrupt` や `SystemExit` まで握り潰すリスクがある。
具体的な例外型を指定すべき。auto-fix 不可。

### EM — flake8-errmsg
例外コンストラクタに直接文字列リテラルを渡すパターンを検出。
`raise ValueError("message")` → トレースバックにメッセージが重複して表示される。
変数に格納してから渡すことを推奨。一部 auto-fix 可能。

### FLY — flynt
`.format()` や `%` 演算子による文字列フォーマットを検出し、f-string への変換を推奨。
f-string の方が読みやすく、パフォーマンスも良い。auto-fix 可能。

### RET — flake8-return
不要な return パターンを検出。例: `else` の後の不要な `return`、
変数に代入して直後に return する冗長なパターン。
RET504（return 直前の代入）はパイプライン処理で誤検出するため ignore 設定で無効化済み。

### ARG — flake8-unused-arguments
使われていない関数引数を検出。テストファイルでは除外済み（fixture の引数は使わない場合がある）。

### PT — flake8-pytest-style
pytest の慣例に沿ったテストコードの書き方を強制。
fixture の scope 指定、parametrize のスタイルなど。

### SIM — flake8-simplify
コードの簡素化を提案。例: `if x == True` → `if x`、
ネストした if の結合、三項演算子への変換など。一部 auto-fix 可能。

### C4 — flake8-comprehensions
リスト・辞書・集合の内包表記の最適化を提案。
`list(x for x in ...)` → `[x for x in ...]`、`dict([(k, v) ...])` → `{k: v ...}` 等。
不要な中間コンテナの生成を排除し、可読性とパフォーマンスを向上させる。auto-fix 可能。

### ISC — flake8-implicit-str-concat
暗黙の文字列結合を検出。`("hello" "world")` のように、
隣り合った文字列リテラルが暗黙に結合されるパターンはバグの元になる。
`+` による明示的な結合を要求する。

### PIE — flake8-pie
不要なコードパターンを検出。不要な `pass`（本体があるのに残っている）、
不要な `...`、dict の `**` スプレッドの冗長パターンなど。auto-fix 可能。

### TC — flake8-type-checking
`TYPE_CHECKING` ブロックに移動可能な import を検出。
型アノテーションにのみ使われている import はランタイムに不要であり、
`if TYPE_CHECKING:` ブロックに移すことでモジュールの起動速度が向上する。

## 無効化しているルール

| ルール | 理由 |
|--------|------|
| D (pydocstyle) | docstring 強制は過剰。必要な箇所のみ手動で書く |
| ANN (flake8-annotations) | mypy --strict が型チェックを担うため重複 |
| ERA (eradicate) | コメントアウトされたコードの検出。開発中は許容 |
| FIX (flake8-fixme) | TODO/FIXME の検出。開発中は許容 |
| TD (flake8-todos) | TODO の形式チェック。過剰 |
| E501 | 行長制限。ruff format が担うため重複 |
| RET504 | return 直前の代入。パイプライン処理（変数を段階的に加工）で誤検出 |

## テストファイルの除外ルール

`tests/**/*.py` では以下を除外:

| ルール | 理由 |
|--------|------|
| S101 | pytest では assert が標準的なアサーション手段 |
| N | テスト名に日本語やアンダースコア区切りを使うため |
| PLR0915 | テスト関数は setup + 実行 + assert で長くなりやすい |
| ARG | fixture の引数は宣言のみで直接参照しない場合がある |

## mypy 設定

| 設定 | 値 | 説明 |
|------|-----|------|
| strict | true | 全ての strict オプションを有効化 |
| warn_return_any | true | Any 型の return を警告 |
| warn_unused_configs | true | 未使用の設定を警告 |

mypy --strict により、型アノテーション必須・Any 型の暗黙使用禁止・未チェックの import 禁止等が強制される。
