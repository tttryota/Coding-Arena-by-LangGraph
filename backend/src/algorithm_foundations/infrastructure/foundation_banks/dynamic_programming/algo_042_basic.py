from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('foundation')

UNIT_BANK = unit_bank(
    unit_id='algo-042-basic',
    title='bitDP（集合に対するDP） の基本',
    unit_kind='foundation',
    target_skill='bitDP（集合に対するDP） の基本',
    concept_overview='bitDP では、どの要素を使い終えたかを bit 集合で表し、その集合から次に 1 つ足す遷移を回します。集合そのものを状態にする DP の基本を身につけます。',
    problem_bank=[
        problem(
            problem_id='algo-042-basic-p1',
            title='bitDP（集合に対するDP） の基本 / 集合状態で割り当てコストの最小値を求める',
            problem_statement='N 人の作業者と N 個の仕事があり、cost[i][j] は作業者 i を仕事 j に割り当てるコストである。全員に異なる仕事を 1 つずつ割り当てる最小総コストを求めよ。',
            input_format='1 行目に N。\n続く N 行に cost[i][1..N]。',
            output_format='最小総コストを出力する。',
            constraints='1 <= N <= 16\n0 <= cost[i][j] <= 10^9',
            examples=[{'input': '3\n4 1 3\n2 0 5\n3 2 2', 'output': '5'}],
            canonical_reference_solution="def solve() -> None:\n    n = int(input())\n    cost = [list(map(int, input().split())) for _ in range(n)]\n    inf = 10 ** 18\n    dp = [inf] * (1 << n)\n    dp[0] = 0\n    for mask in range(1 << n):\n        i = mask.bit_count()\n        if i == n:\n            continue\n        for job in range(n):\n            if mask >> job & 1:\n                continue\n            nxt = mask | (1 << job)\n            dp[nxt] = min(dp[nxt], dp[mask] + cost[i][job])\n    print(dp[-1])\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
