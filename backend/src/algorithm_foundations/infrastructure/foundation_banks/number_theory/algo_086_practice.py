from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('foundation')

UNIT_BANK = unit_bank(
    unit_id='algo-086-practice',
    title='二項係数（nCr mod p） を素直に実装する',
    unit_kind='foundation',
    target_skill='二項係数（nCr mod p） を素直に実装する',
    concept_overview='1 回の二項係数が求められたら、同じ法で複数回問い合わせるときは factorial と逆 factorial を前計算して使い回せます。ここでは同じ p に対する複数 query をまとめて処理します。',
    problem_bank=[
        problem(
            problem_id='algo-086-practice-p1',
            title='二項係数（nCr mod p） を素直に実装する / 同じ法で複数の nCr を求める',
            problem_statement='素数 p と Q 個の問い合わせが与えられる。各問い合わせでは n, r が与えられるので、p を法として nCr mod p を求めよ。',
            input_format='1 行目に p Q。\n続く Q 行に n r。',
            output_format='各問い合わせの答えを 1 行ずつ出力する。',
            constraints='2 <= p <= 10^9 + 7\n1 <= Q <= 2 * 10^5\n0 <= r <= n <= 2 * 10^5\np は素数',
            examples=[{'input': '1000000007 3\n5 2\n6 0\n6 3', 'output': '10\n1\n20'}],
            canonical_reference_solution="def mod_pow(a: int, e: int, mod: int) -> int:\n    ans = 1\n    while e > 0:\n        if e & 1:\n            ans = ans * a % mod\n        a = a * a % mod\n        e >>= 1\n    return ans\n\n\ndef solve() -> None:\n    import sys\n\n    input = sys.stdin.readline\n    mod, q = map(int, input().split())\n    queries = [tuple(map(int, input().split())) for _ in range(q)]\n    max_n = max(n for n, _ in queries)\n    fact = [1] * (max_n + 1)\n    for i in range(1, max_n + 1):\n        fact[i] = fact[i - 1] * i % mod\n    inv_fact = [1] * (max_n + 1)\n    inv_fact[max_n] = mod_pow(fact[max_n], mod - 2, mod)\n    for i in range(max_n, 0, -1):\n        inv_fact[i - 1] = inv_fact[i] * i % mod\n    out = []\n    for n, r in queries:\n        out.append(str(fact[n] * inv_fact[r] % mod * inv_fact[n - r] % mod))\n    sys.stdout.write('\\n'.join(out))\n\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
