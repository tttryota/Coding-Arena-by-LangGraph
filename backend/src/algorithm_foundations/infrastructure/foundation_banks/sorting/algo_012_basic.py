from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('foundation')

UNIT_BANK = unit_bank(
    unit_id='algo-012-basic',
    title='選択ソート の基本',
    unit_kind='foundation',
    target_skill='選択ソート の基本',
    concept_overview='選択ソートは、未確定部分の最小値を見つけて先頭と交換し、左から順に確定させていく知識です。まずは「最小を選んで前へ置く」基本を学びます。',
    problem_bank=[
        problem(
            problem_id='algo-012-basic-p1',
            title='選択ソート の基本 / 先頭に置く最小値を 1 回だけ選んで交換する',
            problem_statement='長さ N の整数列 A が与えられる。配列全体の最小値を探し、その値と先頭要素を 1 回だけ交換したあとの列を出力せよ。',
            input_format='1 行目に N。\n2 行目に A1..AN。',
            output_format='交換後の列を空白区切りで出力する。',
            constraints='1 <= N <= 2000',
            examples=[{'input': '5\n4 1 5 2 3', 'output': '1 4 5 2 3'}],
            canonical_reference_solution="def solve() -> None:\n    n = int(input())\n    a = list(map(int, input().split()))\n    best = 0\n    for j in range(1, n):\n        if a[j] < a[best]:\n            best = j\n    a[0], a[best] = a[best], a[0]\n    print(*a)\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
