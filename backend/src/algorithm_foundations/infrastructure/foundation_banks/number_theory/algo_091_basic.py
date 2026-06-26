from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('foundation')

UNIT_BANK = unit_bank(
    unit_id='algo-091-basic',
    title='オイラーのトーシェント関数 の基本',
    unit_kind='foundation',
    target_skill='オイラーのトーシェント関数 の基本',
    concept_overview='オイラーのトーシェント関数は、1 以上 N 以下で N と互いに素な整数の個数を数える知識です。素因数分解して掛け算の形に直す基本を学びます。',
    problem_bank=[
        problem(
            problem_id='algo-091-basic-p1',
            title='オイラーのトーシェント関数 の基本 / オイラーの φ 関数 φ(N) を求める',
            problem_statement='整数 N が与えられる。オイラーの φ 関数 φ(N) を求めよ。',
            input_format='1 行目に N。',
            output_format='φ(N) を出力する。',
            constraints='1 <= N <= 10^12',
            examples=[{'input': '12', 'output': '4'}],
            canonical_reference_solution="def solve() -> None:\n    n = int(input())\n    x = n\n    ans = n\n    p = 2\n    while p * p <= x:\n        if x % p == 0:\n            while x % p == 0:\n                x //= p\n            ans -= ans // p\n        p += 1\n    if x > 1:\n        ans -= ans // x\n    print(ans)\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
