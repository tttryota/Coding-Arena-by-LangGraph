from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('foundation')

UNIT_BANK = unit_bank(
    unit_id='algo-015-basic',
    title='クイックソート の基本',
    unit_kind='foundation',
    target_skill='クイックソート の基本',
    concept_overview='クイックソートは、pivot を基準に小さい側と大きい側へ分け、その両側を再帰的に整列する知識です。まずは partition による分割の基本を学びます。',
    problem_bank=[
        problem(
            problem_id='algo-015-basic-p1',
            title='クイックソート の基本 / 先頭要素を pivot にして 3 つの区画へ分ける',
            problem_statement='長さ N の整数列 A が与えられる。先頭要素 `A_1` を pivot とし、`pivot より小さい値`、`pivot と等しい値`、`pivot より大きい値` の順に並べ替えた列を出力せよ。同じ区画の中では元の順序を保つこと。',
            input_format='1 行目に N。\n2 行目に A1..AN。',
            output_format='並べ替えた列を空白区切りで出力する。',
            constraints='1 <= N <= 2 * 10^5',
            examples=[{'input': '5\n3 1 5 2 4', 'output': '1 2 3 5 4'}],
            canonical_reference_solution="def solve() -> None:\n    input()\n    a = list(map(int, input().split()))\n    pivot = a[0]\n    left = [x for x in a if x < pivot]\n    mid = [x for x in a if x == pivot]\n    right = [x for x in a if x > pivot]\n    print(*(left + mid + right))\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
