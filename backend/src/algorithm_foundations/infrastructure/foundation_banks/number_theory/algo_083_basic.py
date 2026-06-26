from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('foundation')

UNIT_BANK = unit_bank(
    unit_id='algo-083-basic',
    title='拡張ユークリッドの互除法 の基本',
    unit_kind='foundation',
    target_skill='拡張ユークリッドの互除法 の基本',
    concept_overview='拡張ユークリッドの互除法は、gcd(a, b) を求めるだけでなく、ax + by = gcd(a, b) を満たす係数も同時に求める知識です。互除法の戻りがけで係数を復元する基本を学びます。',
    problem_bank=[
        problem(
            problem_id='algo-083-basic-p1',
            title='拡張ユークリッドの互除法 の基本 / ax + by = gcd(a, b) を満たす整数 x, y の一組と gcd(a, b) を求める',
            problem_statement='整数 a, b が与えられる。`ax + by = gcd(a, b)` を満たす整数 x, y の一組と `gcd(a, b)` を出力せよ。',
            input_format='1 行目に a b。',
            output_format='1 行に `g x y` を出力する。',
            constraints='1 <= a, b <= 10^18',
            examples=[{'input': '30 18', 'output': '6 -1 2'}],
            canonical_reference_solution="def extgcd(a: int, b: int) -> tuple[int, int, int]:\n    if b == 0:\n        return a, 1, 0\n    g, x1, y1 = extgcd(b, a % b)\n    x = y1\n    y = x1 - (a // b) * y1\n    return g, x, y\n\ndef solve() -> None:\n    a, b = map(int, input().split())\n    g, x, y = extgcd(a, b)\n    print(g, x, y)\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
