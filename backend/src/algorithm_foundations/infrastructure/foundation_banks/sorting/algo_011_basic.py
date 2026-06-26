from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('foundation')

UNIT_BANK = unit_bank(
    unit_id='algo-011-basic',
    title='バブルソート の基本',
    unit_kind='foundation',
    target_skill='バブルソート の基本',
    concept_overview='バブルソートは、隣り合う 2 要素を比べて逆順なら交換し、大きい要素を右端へ押し出していく知識です。まずは隣接交換を繰り返して昇順を作る基本を学びます。',
    problem_bank=[
        problem(
            problem_id='algo-011-basic-p1',
            title='バブルソート の基本 / 左から右へ 1 回だけ走査したあとの列を求める',
            problem_statement='長さ N の整数列 A が与えられる。左から右へ 1 回だけ見て、隣り合う 2 要素が逆順ならその場で交換する操作を順に行ったあとの列を出力せよ。',
            input_format='1 行目に N。\n2 行目に A1..AN。',
            output_format='操作後の列を空白区切りで出力する。',
            constraints='1 <= N <= 2000',
            examples=[{'input': '5\n4 1 5 2 3', 'output': '1 4 2 3 5'}],
            canonical_reference_solution="def solve() -> None:\n    n = int(input())\n    a = list(map(int, input().split()))\n    for j in range(n - 1):\n        if a[j] > a[j + 1]:\n            a[j], a[j + 1] = a[j + 1], a[j]\n    print(*a)\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
