from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('foundation')

UNIT_BANK = unit_bank(
    unit_id='algo-044-basic',
    title='部分和問題 の基本',
    unit_kind='foundation',
    target_skill='部分和問題 の基本',
    concept_overview='部分和問題では、何個目まで見たかと合計をいくつ作れるかを更新し、作れる和を少しずつ広げます。選ぶ・選ばないの二択を和の到達可能性として管理する基本を身につけます。',
    problem_bank=[
        problem(
            problem_id='algo-044-basic-p1',
            title='部分和問題 の基本 / いくつかを選んで合計をちょうど S にできるなら Yes、できなければ No を求める',
            problem_statement='N 個の正整数 A と目標値 S が与えられる。 いくつかを選んで合計をちょうど S にできるなら Yes、できなければ No を出力せよ。',
            input_format='1 行目に N S。\n2 行目に A1..AN。',
            output_format='Yes / No を出力する。',
            constraints='1 <= N <= 200\n1 <= S <= 2 * 10^5',
            examples=[{'input': '4 11\n2 5 9 4', 'output': 'Yes'}],
            canonical_reference_solution="def solve() -> None:\n    import sys\n    input = sys.stdin.readline\n    n, s = map(int, input().split())\n    a = list(map(int, input().split()))\n    possible = [False] * (s + 1)\n    possible[0] = True\n    for value in a:\n        for cur in range(s, value - 1, -1):\n            if possible[cur - value]:\n                possible[cur] = True\n    print('Yes' if possible[s] else 'No')\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
