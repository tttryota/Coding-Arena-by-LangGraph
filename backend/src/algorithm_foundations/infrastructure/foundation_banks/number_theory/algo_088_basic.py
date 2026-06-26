from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('foundation')

UNIT_BANK = unit_bank(
    unit_id='algo-088-basic',
    title='中国剰余定理（CRT） の基本',
    unit_kind='foundation',
    target_skill='中国剰余定理（CRT） の基本',
    concept_overview='中国剰余定理は、複数の合同式を 1 本の合同式へまとめる知識です。まずは 2 本の条件を両方満たす最小の非負整数を 1 回の merge で求める基本を学びます。',
    problem_bank=[
        problem(
            problem_id='algo-088-basic-p1',
            title='中国剰余定理（CRT） の基本 / 2 本の合同式を同時に満たす最小の非負整数を求める',
            problem_statement='整数 a, m, b, n が与えられる。`x ≡ a (mod m)` かつ `x ≡ b (mod n)` を満たす最小の非負整数 x を求めよ。 存在しない場合は -1 を出力せよ。',
            input_format='1 行目に a m b n。',
            output_format='解があれば最小の非負整数 x、なければ -1 を出力する。',
            constraints='0 <= a < m <= 10^18\n0 <= b < n <= 10^18',
            examples=[{'input': '2 3 3 5', 'output': '8'}],
            canonical_reference_solution="def extgcd(a: int, b: int) -> tuple[int, int, int]:\n    if b == 0:\n        return a, 1, 0\n    g, x1, y1 = extgcd(b, a % b)\n    return g, y1, x1 - (a // b) * y1\n\ndef solve() -> None:\n    a, m, b, n = map(int, input().split())\n    g, x, _ = extgcd(m, n)\n    diff = b - a\n    if diff % g != 0:\n        print(-1)\n        return\n    mod = n // g\n    t = (diff // g * x) % mod\n    lcm = m // g * n\n    ans = (a + m * t) % lcm\n    print(ans)\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
