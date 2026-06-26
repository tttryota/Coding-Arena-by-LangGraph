from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('foundation')

UNIT_BANK = unit_bank(
    unit_id='algo-085-practice',
    title='繰り返し二乗法（高速べき乗） を素直に実装する',
    unit_kind='foundation',
    target_skill='繰り返し二乗法（高速べき乗） を素直に実装する',
    concept_overview='繰り返し二乗法は、`a^(2^k)` を先に並べておくと、同じ底 a に対する複数の指数 query を高速に処理できます。ここでは平方を前計算して各指数の立っている bit だけを拾う形へ進みます。',
    problem_bank=[
        problem(
            problem_id='algo-085-practice-p1',
            title='繰り返し二乗法（高速べき乗） を素直に実装する / 固定された底 a に対する複数の指数 query を処理する',
            problem_statement='整数 a, m と Q 個の整数 b_i が与えられる。各問い合わせについて `a^(b_i) mod m` を求めよ。',
            input_format='1 行目に a m Q。\n続く Q 行に b_i。',
            output_format='各問い合わせの答えを 1 行ずつ出力する。',
            constraints='0 <= a <= 10^18\n1 <= m <= 10^9 + 7\n1 <= Q <= 2 * 10^5\n0 <= b_i <= 10^18',
            examples=[{'input': '2 1000 3\n10\n5\n0', 'output': '24\n32\n1'}],
            canonical_reference_solution="def solve() -> None:\n    import sys\n    input = sys.stdin.readline\n    a, m, q = map(int, input().split())\n    powers = []\n    cur = a % m\n    for _ in range(61):\n        powers.append(cur)\n        cur = cur * cur % m\n    out = []\n    for _ in range(q):\n        b = int(input())\n        ans = 1\n        bit = 0\n        while b > 0:\n            if b & 1:\n                ans = ans * powers[bit] % m\n            b >>= 1\n            bit += 1\n        out.append(str(ans))\n    sys.stdout.write('\\n'.join(out))\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
