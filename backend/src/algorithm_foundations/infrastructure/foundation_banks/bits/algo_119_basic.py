from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('foundation')

UNIT_BANK = unit_bank(
    unit_id='algo-119-basic',
    title='部分集合の列挙（ビット演算） の基本',
    unit_kind='foundation',
    target_skill='部分集合の列挙（ビット演算） の基本',
    concept_overview='部分集合の列挙（ビット演算）は、0 から 2^N-1 までの整数を「選ぶ・選ばない」のパターンとみなす知識です。まずは各 mask が表す部分集合の和を全て作り、列挙結果そのものを観察する基本を学びます。',
    problem_bank=[
        problem(
            problem_id='algo-119-basic-p1',
            title='部分集合の列挙（ビット演算） の基本 / 全部分集合の和を小さい順に出力せよ',
            problem_statement='長さ N の整数列 A が与えられる。全部分集合の和を小さい順に出力せよ。',
            input_format='1 行目に N。\n2 行目に A1..AN。',
            output_format='部分集合和を空白区切りで出力する。',
            constraints='1 <= N <= 20\n0 <= Ai <= 10^9',
            examples=[{'input': '2\n1 3', 'output': '0 1 3 4'}],
            canonical_reference_solution="def solve() -> None:\n    n = int(input())\n    a = list(map(int, input().split()))\n    sums = []\n    for mask in range(1 << n):\n        total = 0\n        for i in range(n):\n            if mask >> i & 1:\n                total += a[i]\n        sums.append(total)\n    sums.sort()\n    print(*sums)\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
