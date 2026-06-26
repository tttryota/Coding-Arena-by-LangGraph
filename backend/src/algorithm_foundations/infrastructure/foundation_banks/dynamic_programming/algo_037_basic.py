from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('foundation')

UNIT_BANK = unit_bank(
    unit_id='algo-037-basic',
    title='最長増加部分列（LIS） の基本',
    unit_kind='foundation',
    target_skill='最長増加部分列（LIS） の基本',
    concept_overview='LIS では、列を左から見ながら長さごとの末尾の最小値を保つと、増加を壊さずに最長長さを追えます。部分列そのものではなく、伸ばしやすい末尾を管理する見方を身につけます。',
    problem_bank=[
        problem(
            problem_id='algo-037-basic-p1',
            title='最長増加部分列（LIS） の基本 / 最長増加部分列の長さを求める',
            problem_statement='長さ N の整数列 A が与えられる。最長増加部分列の長さを求めよ。',
            input_format='1 行目に N。\n2 行目に A1..AN。',
            output_format='LIS の長さを出力する。',
            constraints='1 <= N <= 2 * 10^5',
            examples=[{'input': '6\n3 1 4 1 5 9', 'output': '4'}],
            canonical_reference_solution="from bisect import bisect_left\n\ndef solve() -> None:\n    import sys\n    input = sys.stdin.readline\n    _ = int(input())\n    a = list(map(int, input().split()))\n    dp = []\n    for value in a:\n        i = bisect_left(dp, value)\n        if i == len(dp):\n            dp.append(value)\n        else:\n            dp[i] = value\n    print(len(dp))\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
