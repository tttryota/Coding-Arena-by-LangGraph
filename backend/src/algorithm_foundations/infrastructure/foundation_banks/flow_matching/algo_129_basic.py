from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('foundation')

UNIT_BANK = unit_bank(
    unit_id='algo-129-basic',
    title='重み付き二部マッチング（部分集合DP） の基本',
    unit_kind='foundation',
    target_skill='重み付き二部マッチング（部分集合DP） の基本',
    concept_overview='重み付き二部マッチングでは、左側と右側を重ならないように結び、選んだ辺の重み総和を最大化します。まずは小さい入力に絞り、右側で使った頂点集合を状態にする部分集合 DP で最大重みを求める基本を押さえます。',
    problem_bank=[
        problem(
            problem_id='algo-129-basic-p1',
            title='重み付き二部マッチング（部分集合DP） の基本 / 重み総和が最大のマッチングを求める',
            problem_statement='左側 N 頂点、右側 M 頂点の二部グラフがあり、各辺 `(u, v)` には重み `w` がある。辺を共有しないようにいくつかの辺を選ぶとき、重み総和の最大値を求めよ。頂点は使わなくてもよい。',
            input_format='1 行目に N M E。\n続く E 行に u v w。',
            output_format='最大重みを出力する。',
            constraints='1 <= N, M <= 16\n0 <= E <= N * M\n0 <= w <= 10^9',
            examples=[{'input': '3 3 7\n1 1 5\n1 2 2\n2 2 4\n2 3 6\n3 1 3\n3 2 4\n3 3 1', 'output': '15'}],
            canonical_reference_solution="def solve() -> None:\n    n, m, e = map(int, input().split())\n    graph = [[] for _ in range(n)]\n    for _ in range(e):\n        u, v, w = map(int, input().split())\n        graph[u - 1].append((v - 1, w))\n\n    neg_inf = -(10 ** 18)\n    dp = [neg_inf] * (1 << m)\n    dp[0] = 0\n    for left in range(n):\n        nxt_dp = dp[:]\n        for mask in range(1 << m):\n            if dp[mask] == neg_inf:\n                continue\n            for right, weight in graph[left]:\n                if mask >> right & 1:\n                    continue\n                nxt = mask | (1 << right)\n                cand = dp[mask] + weight\n                if cand > nxt_dp[nxt]:\n                    nxt_dp[nxt] = cand\n        dp = nxt_dp\n    print(max(dp))\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
