from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('foundation')

UNIT_BANK = unit_bank(
    unit_id='algo-127-basic',
    title='割当問題（部分集合DP） の基本',
    unit_kind='foundation',
    target_skill='割当問題（部分集合DP） の基本',
    concept_overview='割当問題では、各人に異なる仕事を 1 つずつ割り当てて総コストを最小化します。まずは小さい入力に絞り、使った仕事集合を状態にする部分集合 DP で最小総コストを求める基本を押さえます。',
    problem_bank=[
        problem(
            problem_id='algo-127-basic-p1',
            title='割当問題（部分集合DP） の基本 / 正方の割り当てで最小総コストを求める',
            problem_statement='N 人の作業者と N 個の仕事があり、コスト行列 C[i][j] が与えられる。各作業者にちょうど 1 つずつ異なる仕事を割り当てるとき、総コストの最小値を求めよ。',
            input_format='1 行目に N。\n続く N 行に C[i][1..N]。',
            output_format='最小総コストを出力する。',
            constraints='1 <= N <= 16\n0 <= C[i][j] <= 10^9',
            examples=[{'input': '3\n4 1 3\n2 0 5\n3 2 2', 'output': '5'}],
            canonical_reference_solution="def solve() -> None:\n    n = int(input())\n    cost = [list(map(int, input().split())) for _ in range(n)]\n    inf = 10 ** 18\n    dp = [inf] * (1 << n)\n    dp[0] = 0\n    for mask in range(1 << n):\n        i = mask.bit_count()\n        if i == n or dp[mask] == inf:\n            continue\n        for job in range(n):\n            if mask >> job & 1:\n                continue\n            nxt = mask | (1 << job)\n            cand = dp[mask] + cost[i][job]\n            if cand < dp[nxt]:\n                dp[nxt] = cand\n    print(dp[-1])\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
