from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('foundation')

UNIT_BANK = unit_bank(
    unit_id='algo-127-practice',
    title='割当問題（部分集合DP） を素直に実装する',
    unit_kind='foundation',
    target_skill='割当問題（部分集合DP） を素直に実装する',
    concept_overview='正方の割り当てを解けたら、候補となる仕事のほうが多い長方形の割り当てにも同じ部分集合 DP を広げられます。ここでは「全仕事を使い切る」のではなく、「ちょうど N 個の仕事を選んだ状態」の最良値を拾う実装へ進めます。',
    problem_bank=[
        problem(
            problem_id='algo-127-practice-p1',
            title='割当問題（部分集合DP） を素直に実装する / 仕事が余ってもよい最小コスト割り当てを求める',
            problem_statement='N 人の作業者と M 個の仕事があり、コスト行列 C[i][j] が与えられる。各作業者にちょうど 1 つずつ異なる仕事を割り当てる。仕事は余ってもよい。このとき総コストの最小値を求めよ。',
            input_format='1 行目に N M。\n続く N 行に C[i][1..M]。',
            output_format='最小総コストを出力する。',
            constraints='1 <= N <= M <= 18\n0 <= C[i][j] <= 10^9',
            examples=[{'input': '3 4\n4 1 3 2\n2 0 5 3\n3 2 2 4', 'output': '4'}],
            canonical_reference_solution="def solve() -> None:\n    n, m = map(int, input().split())\n    cost = [list(map(int, input().split())) for _ in range(n)]\n    inf = 10 ** 18\n    dp = [inf] * (1 << m)\n    dp[0] = 0\n    for mask in range(1 << m):\n        i = mask.bit_count()\n        if i >= n or dp[mask] == inf:\n            continue\n        for job in range(m):\n            if mask >> job & 1:\n                continue\n            nxt = mask | (1 << job)\n            cand = dp[mask] + cost[i][job]\n            if cand < dp[nxt]:\n                dp[nxt] = cand\n    ans = inf\n    for mask in range(1 << m):\n        if mask.bit_count() == n and dp[mask] < ans:\n            ans = dp[mask]\n    print(ans)\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
