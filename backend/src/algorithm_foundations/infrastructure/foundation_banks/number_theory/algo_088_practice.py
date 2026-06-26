from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('foundation')

UNIT_BANK = unit_bank(
    unit_id='algo-088-practice',
    title='中国剰余定理（CRT） を素直に実装する',
    unit_kind='foundation',
    target_skill='中国剰余定理（CRT） を素直に実装する',
    concept_overview='2 本の合同式が解けたら、答えを次の合同式と順にマージしていくことで複数条件にも広げられます。ここでは合同式を左から畳み込んで 1 本にまとめます。',
    problem_bank=[
        problem(
            problem_id='algo-088-practice-p1',
            title='中国剰余定理（CRT） を素直に実装する / 複数の合同式を同時に満たす最小の非負整数を求める',
            problem_statement='N 本の合同式 `x ≡ a_i (mod m_i)` が与えられる。すべてを同時に満たす最小の非負整数 x を求めよ。存在しない場合は -1 を出力せよ。',
            input_format='1 行目に N。\n続く N 行に a_i m_i。',
            output_format='解があれば最小の非負整数 x、なければ -1 を出力する。',
            constraints='1 <= N <= 2 * 10^5\n0 <= a_i < m_i <= 10^18',
            examples=[{'input': '3\n2 3\n3 5\n2 7', 'output': '23'}],
            canonical_reference_solution="def extgcd(a: int, b: int) -> tuple[int, int, int]:\n    if b == 0:\n        return a, 1, 0\n    g, x1, y1 = extgcd(b, a % b)\n    return g, y1, x1 - (a // b) * y1\n\n\ndef merge(a: int, m: int, b: int, n: int) -> tuple[int, int] | None:\n    g, x, _ = extgcd(m, n)\n    diff = b - a\n    if diff % g != 0:\n        return None\n    mod = n // g\n    t = (diff // g * x) % mod\n    lcm = m // g * n\n    value = (a + m * t) % lcm\n    return value, lcm\n\n\ndef solve() -> None:\n    import sys\n\n    input = sys.stdin.readline\n    count = int(input())\n    a, m = map(int, input().split())\n    for _ in range(count - 1):\n        b, n = map(int, input().split())\n        merged = merge(a, m, b, n)\n        if merged is None:\n            print(-1)\n            return\n        a, m = merged\n    print(a)\n\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
