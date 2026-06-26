from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('foundation')

UNIT_BANK = unit_bank(
    unit_id='algo-086-basic',
    title='二項係数（nCr mod p） の基本',
    unit_kind='foundation',
    target_skill='二項係数（nCr mod p） の基本',
    concept_overview='剰余は、値をある法で割ったあまりとして扱い、巨大な数でも性質を保ったまま計算する考え方です。足し算・掛け算・逆元の基本を押さえます。',
    problem_bank=[
        problem(
            problem_id='algo-086-basic-p1',
            title='二項係数（nCr mod p） の基本 / p を法として nCr mod p を求める',
            problem_statement='整数 n, r, p が与えられる。p を法として nCr mod p を求めよ。p は素数とする。',
            input_format='1 行目に n r p。',
            output_format='nCr mod p を出力する。',
            constraints='0 <= r <= n <= 2 * 10^5\n2 <= p <= 10^9 + 7\np は素数',
            examples=[{'input': '5 2 1000000007', 'output': '10'}],
            canonical_reference_solution="def mod_pow(a: int, e: int, mod: int) -> int:\n    ans = 1\n    while e > 0:\n        if e & 1:\n            ans = ans * a % mod\n        a = a * a % mod\n        e >>= 1\n    return ans\n\ndef solve() -> None:\n    n, r, mod = map(int, input().split())\n    if r < 0 or r > n:\n        print(0)\n        return\n    fact = [1] * (n + 1)\n    for i in range(1, n + 1):\n        fact[i] = fact[i - 1] * i % mod\n    inv_r = mod_pow(fact[r], mod - 2, mod)\n    inv_nr = mod_pow(fact[n - r], mod - 2, mod)\n    print(fact[n] * inv_r % mod * inv_nr % mod)\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
