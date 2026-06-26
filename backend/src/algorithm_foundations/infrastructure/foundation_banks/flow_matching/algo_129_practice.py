from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('foundation')

UNIT_BANK = unit_bank(
    unit_id='algo-129-practice',
    title='重み付き二部マッチング（部分集合DP） を素直に実装する',
    unit_kind='foundation',
    target_skill='重み付き二部マッチング（部分集合DP） を素直に実装する',
    concept_overview='重み最大のマッチングを求められたら、次は「何本選ぶか」という条件も加えられます。ここでは部分集合 DP のまま、ちょうど K 本の辺を選ぶ最大重みマッチングへ拡張します。',
    problem_bank=[
        problem(
            problem_id='algo-129-practice-p1',
            title='重み付き二部マッチング（部分集合DP） を素直に実装する / ちょうど K 本選ぶ最大重みマッチングを求める',
            problem_statement='左側 N 頂点、右側 M 頂点の二部グラフがあり、各辺 `(u, v)` には重み `w` がある。辺を共有しないようにちょうど K 本の辺を選ぶとき、重み総和の最大値を求めよ。K 本選べないなら -1 を出力せよ。',
            input_format='1 行目に N M E K。\n続く E 行に u v w。',
            output_format='最大重み、K 本選べないなら -1 を出力する。',
            constraints='1 <= N, M <= 16\n0 <= E <= N * M\n0 <= w <= 10^9\n0 <= K <= min(N, M)',
            examples=[{'input': '3 3 7 2\n1 1 5\n1 2 2\n2 2 4\n2 3 6\n3 1 3\n3 2 4\n3 3 1', 'output': '11'}],
            canonical_reference_solution="def solve() -> None:\n    n, m, e, k = map(int, input().split())\n    graph = [[] for _ in range(n)]\n    for _ in range(e):\n        u, v, w = map(int, input().split())\n        graph[u - 1].append((v - 1, w))\n\n    neg_inf = -(10 ** 18)\n    dp = [neg_inf] * (1 << m)\n    dp[0] = 0\n    for left in range(n):\n        nxt_dp = dp[:]\n        for mask in range(1 << m):\n            if dp[mask] == neg_inf:\n                continue\n            for right, weight in graph[left]:\n                if mask >> right & 1:\n                    continue\n                nxt = mask | (1 << right)\n                cand = dp[mask] + weight\n                if cand > nxt_dp[nxt]:\n                    nxt_dp[nxt] = cand\n        dp = nxt_dp\n    ans = neg_inf\n    for mask, value in enumerate(dp):\n        if mask.bit_count() == k and value > ans:\n            ans = value\n    print(-1 if ans == neg_inf else ans)\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
