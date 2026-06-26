from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('foundation')

UNIT_BANK = unit_bank(
    unit_id='algo-084-practice',
    title='モジュラ逆元（mod上の逆数） を素直に実装する',
    unit_kind='foundation',
    target_skill='モジュラ逆元（mod上の逆数） を素直に実装する',
    concept_overview='逆元が分かると、`a x ≡ b (mod m)` のような式も `x ≡ b * a^{-1}` として解けます。逆元を見つけて式変形に使う流れを確かめます。',
    problem_bank=[
        problem(
            problem_id='algo-084-practice-p1',
            title='モジュラ逆元（mod上の逆数） を素直に実装する / ax ≡ b (mod m) を満たす最小の非負整数 x を求める',
            problem_statement='整数 a, b, m が与えられる。`a x ≡ b (mod m)` を満たす最小の非負整数 x が存在すれば出力し、存在しなければ -1 を出力せよ。',
            input_format='1 行目に a b m。',
            output_format='x、存在しなければ -1 を出力する。',
            constraints='1 <= a, b, m <= 10^18',
            examples=[{'input': '3 5 11', 'output': '9'}],
            canonical_reference_solution="def extgcd(a: int, b: int) -> tuple[int, int, int]:\n    if b == 0:\n        return a, 1, 0\n    g, x1, y1 = extgcd(b, a % b)\n    return g, y1, x1 - (a // b) * y1\n\ndef solve() -> None:\n    a, b, m = map(int, input().split())\n    g, x, _ = extgcd(a, m)\n    if b % g != 0:\n        print(-1)\n        return\n    a //= g\n    b //= g\n    m //= g\n    _, inv, _ = extgcd(a, m)\n    print((b * inv) % m)\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
