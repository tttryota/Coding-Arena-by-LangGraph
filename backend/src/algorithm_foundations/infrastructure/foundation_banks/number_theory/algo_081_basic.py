from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('foundation')

UNIT_BANK = unit_bank(
    unit_id='algo-081-basic',
    title='エラトステネスの篩 の基本',
    unit_kind='foundation',
    target_skill='エラトステネスの篩 の基本',
    concept_overview='エラトステネスの篩は、1 から N までの素数をまとめて前計算する方法です。まずは素数を列挙する基本形を押さえます。',
    problem_bank=[
        problem(
            problem_id='algo-081-basic-p1',
            title='エラトステネスの篩 の基本 / 1 以上 N 以下の素数をすべて列挙する',
            problem_statement='整数 N が与えられる。1 以上 N 以下の素数を小さい順にすべて出力せよ。',
            input_format='1 行目に N。',
            output_format='素数を空白区切りで出力する。',
            constraints='2 <= N <= 10^7',
            examples=[{'input': '10', 'output': '2 3 5 7'}],
            canonical_reference_solution="def solve() -> None:\n    import sys\n    n = int(input())\n    is_prime = bytearray(b'\\x01') * (n + 1)\n    if n >= 0:\n        is_prime[0] = 0\n    if n >= 1:\n        is_prime[1] = 0\n    p = 2\n    while p * p <= n:\n        if is_prime[p]:\n            for multiple in range(p * p, n + 1, p):\n                is_prime[multiple] = 0\n        p += 1\n    first = True\n    for i in range(2, n + 1):\n        if not is_prime[i]:\n            continue\n        if not first:\n            sys.stdout.write(' ')\n        sys.stdout.write(str(i))\n        first = False\n    sys.stdout.write('\\n')\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
