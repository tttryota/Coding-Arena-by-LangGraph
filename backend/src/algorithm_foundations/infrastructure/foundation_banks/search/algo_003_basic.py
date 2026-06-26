from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('foundation')

UNIT_BANK = unit_bank(
    unit_id='algo-003-basic',
    title='三分探索 の基本',
    unit_kind='foundation',
    target_skill='三分探索 の基本',
    concept_overview='三分探索は、値が谷型や山型に変化するとき、比べる位置を 2 つ置いて不要な側を捨てていく解き方です。まずは谷型の数列から最小値を見つける基本形を押さえます。',
    problem_bank=[
        problem(
            problem_id='algo-003-basic-p1',
            title='三分探索 の基本 / 谷型の数列から最小値を探す',
            problem_statement='長さ N の整数列 A が与えられる。A は、ある位置 p を境に狭義単調減少のあと狭義単調増加する谷型数列である。三分探索を用いて A の最小値を求めよ。',
            input_format='1 行目に N。\n2 行目に A1..AN。',
            output_format='最小値を出力する。',
            constraints='3 <= N <= 2 * 10^5\nA は谷型',
            examples=[{'input': '7\n9 6 4 2 3 5 8', 'output': '2'}],
            canonical_reference_solution="def solve() -> None:\n    n = int(input())\n    a = list(map(int, input().split()))\n    left, right = 0, n - 1\n    while right - left > 3:\n        m1 = left + (right - left) // 3\n        m2 = right - (right - left) // 3\n        if a[m1] <= a[m2]:\n            right = m2 - 1\n        else:\n            left = m1 + 1\n    print(min(a[left:right + 1]))\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
