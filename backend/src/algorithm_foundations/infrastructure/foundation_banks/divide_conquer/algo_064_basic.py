from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('foundation')
MOD = 998244353

UNIT_BANK = unit_bank(
    unit_id='algo-064-basic',
    title='逆元を用いた多項式補間 の基本',
    unit_kind='foundation',
    target_skill='逆元を用いた多項式補間 の基本',
    concept_overview='等間隔な点での多項式の値が分かっているとき、逆元を使って別の 1 点の値を補間できます。各点の寄与を掛け合わせて集める基本を学びます。',
    problem_bank=[
        problem(
            problem_id='algo-064-basic-p1',
            title='逆元を用いた多項式補間 の基本 / 多項式の 1 点評価を復元する',
            problem_statement='法 998244353 上の次数 N 未満の多項式 P(x) について、P(0), P(1), ..., P(N-1) の値が与えられる。整数 X に対する P(X) を 998244353 で割った余りで求めよ。',
            input_format='1 行目に N X。\n2 行目に P(0), P(1), ..., P(N-1)。',
            output_format='P(X) mod 998244353 を出力する。',
            constraints='1 <= N <= 2 * 10^5\n0 <= X <= 10^9\n0 <= P(i) < 998244353',
            examples=[{'input': '4 5\n1 2 5 10', 'output': '26'}],
            canonical_reference_solution="MOD = 998244353\n\n\ndef solve() -> None:\n    import sys\n    input = sys.stdin.readline\n    n, x = map(int, input().split())\n    y = list(map(int, input().split()))\n    if x < n:\n        print(y[x])\n        return\n    fact = [1] * (n + 1)\n    for i in range(1, n + 1):\n        fact[i] = fact[i - 1] * i % MOD\n    inv_fact = [1] * (n + 1)\n    inv_fact[n] = pow(fact[n], MOD - 2, MOD)\n    for i in range(n, 0, -1):\n        inv_fact[i - 1] = inv_fact[i] * i % MOD\n    prefix = [1] * (n + 1)\n    for i in range(n):\n        prefix[i + 1] = prefix[i] * (x - i) % MOD\n    suffix = [1] * (n + 1)\n    for i in range(n - 1, -1, -1):\n        suffix[i] = suffix[i + 1] * (x - i) % MOD\n    ans = 0\n    for i in range(n):\n        numer = prefix[i] * suffix[i + 1] % MOD\n        denom = inv_fact[i] * inv_fact[n - 1 - i] % MOD\n        if (n - 1 - i) % 2 == 1:\n            denom = (-denom) % MOD\n        ans = (ans + y[i] * numer % MOD * denom) % MOD\n    print(ans)\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
