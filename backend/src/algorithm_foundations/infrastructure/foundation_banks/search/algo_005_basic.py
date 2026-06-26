from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('foundation')

UNIT_BANK = unit_bank(
    unit_id='algo-005-basic',
    title='幅優先探索（BFS） の基本',
    unit_kind='foundation',
    target_skill='幅優先探索（BFS） の基本',
    concept_overview='幅優先探索は、近い状態から順に広げていく解き方です。キューを使って層ごとに進むことで、最短手数や到達可否を素直に求めます。',
    problem_bank=[
        problem(
            problem_id='algo-005-basic-p1',
            title='幅優先探索（BFS） の基本 / 頂点 1 から頂点 N までの最短辺数を求める',
            problem_statement='N 頂点 M 辺の無向グラフが与えられる。幅優先探索を用いて、頂点 1 から頂点 N までの最短辺数を求めよ。到達できなければ -1 を出力せよ。',
            input_format='1 行目に N M。\n続く M 行に辺 u v。',
            output_format='最短辺数、到達できなければ -1 を出力する。',
            constraints='1 <= N <= 2 * 10^5\n0 <= M <= 2 * 10^5',
            examples=[{'input': '5 4\n1 2\n2 3\n3 4\n4 5', 'output': '4'}],
            canonical_reference_solution="from collections import deque\n\ndef solve() -> None:\n    import sys\n    input = sys.stdin.readline\n    n, m = map(int, input().split())\n    graph = [[] for _ in range(n)]\n    for _ in range(m):\n        u, v = map(int, input().split())\n        u -= 1\n        v -= 1\n        graph[u].append(v)\n        graph[v].append(u)\n    dist = [-1] * n\n    dist[0] = 0\n    dq = deque([0])\n    while dq:\n        node = dq.popleft()\n        for nxt in graph[node]:\n            if dist[nxt] != -1:\n                continue\n            dist[nxt] = dist[node] + 1\n            dq.append(nxt)\n    print(dist[n - 1])\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
