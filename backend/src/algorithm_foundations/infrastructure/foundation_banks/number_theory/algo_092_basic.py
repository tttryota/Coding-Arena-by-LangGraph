from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('foundation')

UNIT_BANK = unit_bank(
    unit_id='algo-092-basic',
    title='メビウス関数 μ(N) の基本',
    unit_kind='foundation',
    target_skill='メビウス関数 μ(N) の基本',
    concept_overview='メビウス関数 μ(N) は、素因数分解を使って「同じ素因数を 2 回以上持つか」と「異なる素因数の個数の偶奇」を調べる知識です。まずは μ(N) の値が 0, 1, -1 のどれになるかを基本から押さえます。',
    problem_bank=[
        problem(
            problem_id='algo-092-basic-p1',
            title='メビウス関数 μ(N) の基本 / メビウス関数 μ(N) を求める',
            problem_statement='整数 N が与えられる。メビウス関数 μ(N) を求めよ。',
            input_format='1 行目に N。',
            output_format='μ(N) を出力する。',
            constraints='1 <= N <= 10^12',
            examples=[{'input': '30', 'output': '-1'}],
            canonical_reference_solution="def solve() -> None:\n    n = int(input())\n    x = n\n    cnt = 0\n    p = 2\n    while p * p <= x:\n        if x % p == 0:\n            exp = 0\n            while x % p == 0:\n                x //= p\n                exp += 1\n            if exp >= 2:\n                print(0)\n                return\n            cnt += 1\n        p += 1\n    if x > 1:\n        cnt += 1\n    print(-1 if cnt % 2 else 1)\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
