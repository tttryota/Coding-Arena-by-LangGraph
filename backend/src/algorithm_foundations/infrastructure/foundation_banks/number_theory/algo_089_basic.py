from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('foundation')

UNIT_BANK = unit_bank(
    unit_id='algo-089-basic',
    title='行列累乗 の基本',
    unit_kind='foundation',
    target_skill='行列累乗 の基本',
    concept_overview='行列累乗は、入力の構造や候補を整理し、決まった手順で答えを作る知識です。まずは典型の使い方を自分の手で追える状態を目指します。',
    problem_bank=[
        problem(
            problem_id='algo-089-basic-p1',
            title='行列累乗 の基本 / 1 ケースをそのまま解く',
            problem_statement='整数 N が与えられる。フィボナッチ数列の N 項目 F_N を 10^9+7 で割った余りで求めよ。F_0=0, F_1=1 とする。',
            input_format='1 行目に N。',
            output_format='F_N mod 1000000007 を出力する。',
            constraints='0 <= N <= 10^18',
            examples=[
                {
                    'input': '10',
                    'output': '55',
                },
            ],
            canonical_reference_solution="MOD = 10 ** 9 + 7\n\ndef mul(a: list[list[int]], b: list[list[int]]) -> list[list[int]]:\n    return [\n        [\n            (a[i][0] * b[0][j] + a[i][1] * b[1][j]) % MOD\n            for j in range(2)\n        ]\n        for i in range(2)\n    ]\n\ndef solve() -> None:\n    n = int(input())\n    result = [[1, 0], [0, 1]]\n    base = [[1, 1], [1, 0]]\n    while n > 0:\n        if n & 1:\n            result = mul(result, base)\n        base = mul(base, base)\n        n >>= 1\n    print(result[0][1])\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
        problem(
            problem_id='algo-089-basic-p2',
            title='行列累乗 の基本 / 2 ケースを連続して解く',
            problem_statement='2 ケース分の入力が続けて与えられる。それぞれについて、整数 N が与えられる。フィボナッチ数列の N 項目 F_N を 10^9+7 で割った余りで求めよ。F_0=0, F_1=1 とする。',
            input_format='1 行目に 2。\n続く 2 ケースについて:\n1 行目に N。',
            output_format='各ケースの答えを順に出力する。',
            constraints='0 <= N <= 10^18\n2 ケースの合計でも同じ方針で処理すること。',
            examples=[
                {
                    'input': '2\n10\n10',
                    'output': '55\n55',
                },
            ],
            canonical_reference_solution="import io\nimport sys\nfrom contextlib import redirect_stdout\n\nMOD = 10 ** 9 + 7\n\ndef mul(a: list[list[int]], b: list[list[int]]) -> list[list[int]]:\n    return [\n        [\n            (a[i][0] * b[0][j] + a[i][1] * b[1][j]) % MOD\n            for j in range(2)\n        ]\n        for i in range(2)\n    ]\n\ndef solve_one() -> None:\n    n = int(input())\n    result = [[1, 0], [0, 1]]\n    base = [[1, 1], [1, 0]]\n    while n > 0:\n        if n & 1:\n            result = mul(result, base)\n        base = mul(base, base)\n        n >>= 1\n    print(result[0][1])\n\ndef solve() -> None:\n    t = 2\n    outputs = []\n    for _ in range(t):\n        buf = io.StringIO()\n        with redirect_stdout(buf):\n            solve_one()\n        outputs.append(buf.getvalue().rstrip('\\n'))\n    sys.stdout.write('\\n'.join(outputs))\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
        problem(
            problem_id='algo-089-basic-p3',
            title='行列累乗 の基本 / 3 ケースを連続して解く',
            problem_statement='3 ケース分の入力が続けて与えられる。それぞれについて、整数 N が与えられる。フィボナッチ数列の N 項目 F_N を 10^9+7 で割った余りで求めよ。F_0=0, F_1=1 とする。',
            input_format='1 行目に 3。\n続く 3 ケースについて:\n1 行目に N。',
            output_format='各ケースの答えを順に出力する。',
            constraints='0 <= N <= 10^18\n3 ケースの合計でも同じ方針で処理すること。',
            examples=[
                {
                    'input': '3\n10\n10\n10',
                    'output': '55\n55\n55',
                },
            ],
            canonical_reference_solution="import io\nimport sys\nfrom contextlib import redirect_stdout\n\nMOD = 10 ** 9 + 7\n\ndef mul(a: list[list[int]], b: list[list[int]]) -> list[list[int]]:\n    return [\n        [\n            (a[i][0] * b[0][j] + a[i][1] * b[1][j]) % MOD\n            for j in range(2)\n        ]\n        for i in range(2)\n    ]\n\ndef solve_one() -> None:\n    n = int(input())\n    result = [[1, 0], [0, 1]]\n    base = [[1, 1], [1, 0]]\n    while n > 0:\n        if n & 1:\n            result = mul(result, base)\n        base = mul(base, base)\n        n >>= 1\n    print(result[0][1])\n\ndef solve() -> None:\n    t = 3\n    outputs = []\n    for _ in range(t):\n        buf = io.StringIO()\n        with redirect_stdout(buf):\n            solve_one()\n        outputs.append(buf.getvalue().rstrip('\\n'))\n    sys.stdout.write('\\n'.join(outputs))\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
