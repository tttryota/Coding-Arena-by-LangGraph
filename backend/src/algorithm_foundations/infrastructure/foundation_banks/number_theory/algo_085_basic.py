from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('foundation')

UNIT_BANK = unit_bank(
    unit_id='algo-085-basic',
    title='繰り返し二乗法（高速べき乗） の基本',
    unit_kind='foundation',
    target_skill='繰り返し二乗法（高速べき乗） の基本',
    concept_overview='繰り返し二乗法（高速べき乗）は、指数 b を 2 進数として見て、必要な桁だけ現在の底を掛ける知識です。底を毎回二乗しながら指数を半分にすることで、a^b を高速に求める基本を学びます。',
    problem_bank=[
        problem(
            problem_id='algo-085-basic-p1',
            title='繰り返し二乗法（高速べき乗） の基本 / a^b mod m を求める',
            problem_statement='整数 a, b, m が与えられる。a^b mod m を求めよ。',
            input_format='1 行目に a b m。',
            output_format='a^b mod m を出力する。',
            constraints='0 <= a, b <= 10^18\n1 <= m <= 10^9 + 7',
            examples=[{'input': '2 10 1000', 'output': '24'}],
            canonical_reference_solution="def solve() -> None:\n    a, b, m = map(int, input().split())\n    ans = 1\n    a %= m\n    while b > 0:\n        if b & 1:\n            ans = ans * a % m\n        a = a * a % m\n        b >>= 1\n    print(ans)\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
