from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('foundation')

UNIT_BANK = unit_bank(
    unit_id='algo-025-basic',
    title='プリム法（最小全域木） の基本',
    unit_kind='foundation',
    target_skill='プリム法（最小全域木） の基本',
    concept_overview='最小全域木は、全頂点をつなぎつつ重み合計を最小にする辺集合を作る考え方です。どの辺を採用すると無駄なくつながるかを順に決める基本を学びます。',
    problem_bank=[
        problem(
            problem_id='algo-025-basic-p1',
            title='プリム法（最小全域木） の基本 / プリム法で最小全域木の重みを求める',
            problem_statement='重み付き無向連結グラフが与えられる。プリム法で最小全域木の重みを求めよ。',
            input_format='1 行目に N M。\n続く M 行に u v w。',
            output_format='最小全域木の重みを出力する。',
            constraints='1 <= N <= 2 * 10^5\nN-1 <= M <= 2 * 10^5',
            examples=[{'input': '4 5\n1 2 1\n1 3 4\n2 3 2\n2 4 5\n3 4 1', 'output': '4'}],
            canonical_reference_solution="import heapq\n\ndef solve() -> None:\n    import sys\n    input = sys.stdin.readline\n    n, m = map(int, input().split())\n    graph = [[] for _ in range(n)]\n    for _ in range(m):\n        u, v, w = map(int, input().split())\n        u -= 1\n        v -= 1\n        graph[u].append((w, v))\n        graph[v].append((w, u))\n    used = [False] * n\n    pq = [(0, 0)]\n    total = 0\n    while pq:\n        cost, node = heapq.heappop(pq)\n        if used[node]:\n            continue\n        used[node] = True\n        total += cost\n        for edge_cost, nxt in graph[node]:\n            if not used[nxt]:\n                heapq.heappush(pq, (edge_cost, nxt))\n    print(total)\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
