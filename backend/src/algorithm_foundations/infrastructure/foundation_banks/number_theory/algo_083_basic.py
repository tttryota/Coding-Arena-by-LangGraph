from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('foundation')

UNIT_BANK = unit_bank(
    unit_id='algo-083-basic',
    title='拡張ユークリッドの互除法 の基本',
    unit_kind='foundation',
    target_skill='拡張ユークリッドの互除法 の基本',
    concept_overview='拡張ユークリッドの互除法は、入力の構造や候補を整理し、決まった手順で答えを作る知識です。まずは典型の使い方を自分の手で追える状態を目指します。',
    problem_bank=[
        problem(
            problem_id='algo-083-basic-p1',
            title='拡張ユークリッドの互除法 の基本 / 1 ケースをそのまま解く',
            problem_statement='整数 a, b が与えられる。`ax + by = gcd(a, b)` を満たす整数 x, y の一組と `gcd(a, b)` を出力せよ。',
            input_format='1 行目に a b。',
            output_format='1 行に `g x y` を出力する。',
            constraints='1 <= a, b <= 10^18',
            examples=[
                {
                    'input': '30 18',
                    'output': '6 -1 2',
                },
            ],
            canonical_reference_solution="def extgcd(a: int, b: int) -> tuple[int, int, int]:\n    if b == 0:\n        return a, 1, 0\n    g, x1, y1 = extgcd(b, a % b)\n    x = y1\n    y = x1 - (a // b) * y1\n    return g, x, y\n\ndef solve() -> None:\n    a, b = map(int, input().split())\n    g, x, y = extgcd(a, b)\n    print(g, x, y)\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
        problem(
            problem_id='algo-083-basic-p2',
            title='拡張ユークリッドの互除法 の基本 / 2 ケースを連続して解く',
            problem_statement='2 ケース分の入力が続けて与えられる。それぞれについて、整数 a, b が与えられる。`ax + by = gcd(a, b)` を満たす整数 x, y の一組と `gcd(a, b)` を出力せよ。',
            input_format='1 行目に 2。\n続く 2 ケースについて:\n1 行目に a b。',
            output_format='各ケースの答えを順に出力する。',
            constraints='1 <= a, b <= 10^18\n2 ケースの合計でも同じ方針で処理すること。',
            examples=[
                {
                    'input': '2\n30 18\n30 18',
                    'output': '6 -1 2\n6 -1 2',
                },
            ],
            canonical_reference_solution="import io\nimport sys\nfrom contextlib import redirect_stdout\n\ndef extgcd(a: int, b: int) -> tuple[int, int, int]:\n    if b == 0:\n        return a, 1, 0\n    g, x1, y1 = extgcd(b, a % b)\n    x = y1\n    y = x1 - (a // b) * y1\n    return g, x, y\n\ndef solve_one() -> None:\n    a, b = map(int, input().split())\n    g, x, y = extgcd(a, b)\n    print(g, x, y)\n\ndef solve() -> None:\n    t = 2\n    outputs = []\n    for _ in range(t):\n        buf = io.StringIO()\n        with redirect_stdout(buf):\n            solve_one()\n        outputs.append(buf.getvalue().rstrip('\\n'))\n    sys.stdout.write('\\n'.join(outputs))\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
        problem(
            problem_id='algo-083-basic-p3',
            title='拡張ユークリッドの互除法 の基本 / 3 ケースを連続して解く',
            problem_statement='3 ケース分の入力が続けて与えられる。それぞれについて、整数 a, b が与えられる。`ax + by = gcd(a, b)` を満たす整数 x, y の一組と `gcd(a, b)` を出力せよ。',
            input_format='1 行目に 3。\n続く 3 ケースについて:\n1 行目に a b。',
            output_format='各ケースの答えを順に出力する。',
            constraints='1 <= a, b <= 10^18\n3 ケースの合計でも同じ方針で処理すること。',
            examples=[
                {
                    'input': '3\n30 18\n30 18\n30 18',
                    'output': '6 -1 2\n6 -1 2\n6 -1 2',
                },
            ],
            canonical_reference_solution="import io\nimport sys\nfrom contextlib import redirect_stdout\n\ndef extgcd(a: int, b: int) -> tuple[int, int, int]:\n    if b == 0:\n        return a, 1, 0\n    g, x1, y1 = extgcd(b, a % b)\n    x = y1\n    y = x1 - (a // b) * y1\n    return g, x, y\n\ndef solve_one() -> None:\n    a, b = map(int, input().split())\n    g, x, y = extgcd(a, b)\n    print(g, x, y)\n\ndef solve() -> None:\n    t = 3\n    outputs = []\n    for _ in range(t):\n        buf = io.StringIO()\n        with redirect_stdout(buf):\n            solve_one()\n        outputs.append(buf.getvalue().rstrip('\\n'))\n    sys.stdout.write('\\n'.join(outputs))\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
