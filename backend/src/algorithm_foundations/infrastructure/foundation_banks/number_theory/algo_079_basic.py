from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('foundation')

UNIT_BANK = unit_bank(
    unit_id='algo-079-basic',
    title='最大公約数・最小公倍数（GCD/LCM） の基本',
    unit_kind='foundation',
    target_skill='最大公約数・最小公倍数（GCD/LCM） の基本',
    concept_overview='最大公約数と最小公倍数は、整数の割り切れ方を使って共通するまとまりを扱う知識です。まずは 2 数の最大公約数を互除法で求める基本を学びます。',
    problem_bank=[
        problem(
            problem_id='algo-079-basic-p1',
            title='最大公約数・最小公倍数（GCD/LCM） の基本 / 2 つの整数の最大公約数を求める',
            problem_statement='2 つの正整数 A, B が与えられる。A と B の最大公約数を求めよ。',
            input_format='1 行目に A B。',
            output_format='最大公約数を出力する。',
            constraints='1 <= A, B <= 10^18',
            examples=[{'input': '18 30', 'output': '6'}],
            canonical_reference_solution="def gcd(a: int, b: int) -> int:\n    while b:\n        a, b = b, a % b\n    return a\n\n\ndef solve() -> None:\n    a, b = map(int, input().split())\n    print(gcd(a, b))\n\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
