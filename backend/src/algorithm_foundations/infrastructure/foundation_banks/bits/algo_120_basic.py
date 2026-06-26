from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('foundation')

UNIT_BANK = unit_bank(
    unit_id='algo-120-basic',
    title='ビットシフトによる高速化 の基本',
    unit_kind='foundation',
    target_skill='ビットシフトによる高速化 の基本',
    concept_overview='ビットシフトによる高速化は、2 の累乗倍や 2 の累乗での整数除算をシフト演算へ置き換える知識です。まずは左シフト・右シフトで 1 つの値をそのまま更新する基本を学びます。',
    problem_bank=[
        problem(
            problem_id='algo-120-basic-p1',
            title='ビットシフトによる高速化 の基本 / 最後の X を求める',
            problem_statement='整数 X と Q 個の操作が与えられる。`1 k` は `X *= 2^k`、`2 k` は `X //= 2^k` とする。最後の X を出力せよ。',
            input_format='1 行目に X Q。\n続く Q 行に操作。',
            output_format='最終的な X を出力する。',
            constraints='0 <= X < 2^60\n1 <= Q <= 2 * 10^5\n0 <= k <= 60',
            examples=[{'input': '3 3\n1 2\n2 1\n1 1', 'output': '12'}],
            canonical_reference_solution="def solve() -> None:\n    x, q = map(int, input().split())\n    for _ in range(q):\n        t, k = map(int, input().split())\n        if t == 1:\n            x <<= k\n        else:\n            x >>= k\n    print(x)\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
