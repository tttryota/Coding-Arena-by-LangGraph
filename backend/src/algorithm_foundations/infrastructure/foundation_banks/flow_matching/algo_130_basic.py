from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('foundation')

UNIT_BANK = unit_bank(
    unit_id='algo-130-basic',
    title='Hopcroft-Karp法 の基本',
    unit_kind='foundation',
    target_skill='Hopcroft-Karp法 の基本',
    concept_overview='Hopcroft-Karp 法は、二部グラフ最大マッチングを最短増加道の束で高速化する手法です。まずは大規模グラフで最大マッチング数を求める基本を学びます。',
    problem_bank=[
        problem(
            problem_id='algo-130-basic-p1',
            title='Hopcroft-Karp法 の基本 / 二部グラフの最大マッチング数を求める',
            problem_statement='左側 N 頂点、右側 M 頂点の二部グラフが与えられる。最大マッチング数を求めよ。',
            input_format='1 行目に N M E。\n続く E 行に u v。',
            output_format='最大マッチング数を出力する。',
            constraints='1 <= N, M <= 2 * 10^5\n1 <= E <= 5 * 10^5\n1 <= u <= N\n1 <= v <= M',
            examples=[{'input': '3 3 4\n1 1\n1 2\n2 2\n3 3', 'output': '3'}],
            canonical_reference_solution="from collections import deque\n\n\ndef solve() -> None:\n    import sys\n    sys.setrecursionlimit(1_000_000)\n    input = sys.stdin.readline\n    n, m, e = map(int, input().split())\n    graph = [[] for _ in range(n)]\n    for _ in range(e):\n        u, v = map(int, input().split())\n        graph[u - 1].append(v - 1)\n    match_l = [-1] * n\n    match_r = [-1] * m\n    dist = [0] * n\n\n    def bfs() -> bool:\n        dq = deque()\n        found = False\n        for v in range(n):\n            if match_l[v] == -1:\n                dist[v] = 0\n                dq.append(v)\n            else:\n                dist[v] = -1\n        while dq:\n            v = dq.popleft()\n            for to in graph[v]:\n                mate = match_r[to]\n                if mate == -1:\n                    found = True\n                elif dist[mate] == -1:\n                    dist[mate] = dist[v] + 1\n                    dq.append(mate)\n        return found\n\n    def dfs(v: int) -> bool:\n        for to in graph[v]:\n            mate = match_r[to]\n            if mate == -1 or (dist[mate] == dist[v] + 1 and dfs(mate)):\n                match_l[v] = to\n                match_r[to] = v\n                return True\n        dist[v] = -1\n        return False\n\n    ans = 0\n    while bfs():\n        for v in range(n):\n            if match_l[v] == -1 and dfs(v):\n                ans += 1\n    print(ans)\n\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
