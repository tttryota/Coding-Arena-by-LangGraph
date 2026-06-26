from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('integration')

UNIT_BANK = unit_bank(
    unit_id='algo-003-integration',
    title='三分探索 の総合演習',
    unit_kind='integration',
    target_skill='三分探索 の総合演習',
    concept_overview='三分探索では、比較の向きを変えるだけで谷型の最小値探索から山型の最大値探索へ広げられます。形に応じてどちら側を捨てるかを切り替える練習です。',
    problem_bank=[
        problem(
            problem_id='algo-003-integration-p1',
            title='三分探索 の総合演習 / 山型の数列から最大値を探す',
            problem_statement='長さ N の整数列 A が与えられる。A は、ある位置 p を境に狭義単調増加のあと狭義単調減少する山型数列である。三分探索を用いて A の最大値を求めよ。',
            input_format='1 行目に N。\n2 行目に A1..AN。',
            output_format='最大値を出力する。',
            constraints='3 <= N <= 2 * 10^5\nA は山型',
            examples=[{'input': '6\n1 4 7 9 6 3', 'output': '9'}],
            canonical_reference_solution="def solve() -> None:\n    n = int(input())\n    a = list(map(int, input().split()))\n    left, right = 0, n - 1\n    while right - left > 3:\n        m1 = left + (right - left) // 3\n        m2 = right - (right - left) // 3\n        if a[m1] >= a[m2]:\n            right = m2 - 1\n        else:\n            left = m1 + 1\n    print(max(a[left:right + 1]))\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
