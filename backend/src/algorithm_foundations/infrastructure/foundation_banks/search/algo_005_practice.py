from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('foundation')

UNIT_BANK = unit_bank(
    unit_id='algo-005-practice',
    title='幅優先探索（BFS） を素直に実装する',
    unit_kind='foundation',
    target_skill='幅優先探索（BFS） を素直に実装する',
    concept_overview='BFS を 1 回回すと、終点 1 個だけでなく始点から全頂点への最短距離がまとめて得られます。ここでは dist 配列全体を出力します。',
    problem_bank=[
        problem(
            problem_id='algo-005-practice-p1',
            title='幅優先探索（BFS） を素直に実装する / 頂点 1 から全頂点への最短辺数を出力する',
            problem_statement='N 頂点 M 辺の無向グラフが与えられる。幅優先探索を用いて、頂点 1 から各頂点への最短辺数を求めよ。到達できない頂点は -1 とする。',
            input_format='1 行目に N M。\n続く M 行に辺 u v。',
            output_format='dist[1], dist[2], ..., dist[N] を空白区切りで出力する。',
            constraints='1 <= N <= 2 * 10^5\n0 <= M <= 2 * 10^5',
            examples=[{'input': '5 3\n1 2\n2 3\n4 5', 'output': '0 1 2 -1 -1'}],
            canonical_reference_solution="from collections import deque\n\n\ndef solve() -> None:\n    import sys\n    input = sys.stdin.readline\n    n, m = map(int, input().split())\n    graph = [[] for _ in range(n)]\n    for _ in range(m):\n        u, v = map(int, input().split())\n        u -= 1\n        v -= 1\n        graph[u].append(v)\n        graph[v].append(u)\n    dist = [-1] * n\n    dist[0] = 0\n    dq = deque([0])\n    while dq:\n        node = dq.popleft()\n        for nxt in graph[node]:\n            if dist[nxt] != -1:\n                continue\n            dist[nxt] = dist[node] + 1\n            dq.append(nxt)\n    print(*dist)\n\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
