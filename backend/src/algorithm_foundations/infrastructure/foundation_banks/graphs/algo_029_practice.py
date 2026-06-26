from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('foundation')

UNIT_BANK = unit_bank(
    unit_id='algo-029-practice',
    title='木の直径 を素直に実装する',
    unit_kind='foundation',
    target_skill='木の直径 を素直に実装する',
    concept_overview='木の直径では、長さだけでなく端点も求められます。2 回探索で最も遠い 2 頂点を特定し、長さに加えて端点の組も出力する形を確かめます。',
    problem_bank=[
        problem(
            problem_id='algo-029-practice-p1',
            title='木の直径 を素直に実装する / 直径の両端点の 1 組と長さを求める',
            problem_statement='重みのない木が与えられる。木の直径の両端点の 1 組と、その長さを求めよ。端点は小さい順に出力せよ。',
            input_format='1 行目に N。\n続く N-1 行に辺 u v。',
            output_format='1 行に `u v d` を出力する。',
            constraints='1 <= N <= 2 * 10^5',
            examples=[{'input': '5\n1 2\n2 3\n2 4\n4 5', 'output': '1 5 3'}],
            canonical_reference_solution="from collections import deque\n\ndef farthest(start: int, graph: list[list[int]]) -> tuple[int, int, list[int]]:\n    dist = [-1] * len(graph)\n    parent = [-1] * len(graph)\n    dist[start] = 0\n    dq = deque([start])\n    while dq:\n        node = dq.popleft()\n        for nxt in graph[node]:\n            if dist[nxt] != -1:\n                continue\n            dist[nxt] = dist[node] + 1\n            parent[nxt] = node\n            dq.append(nxt)\n    best = max(range(len(graph)), key=lambda idx: dist[idx])\n    return best, dist[best], parent\n\ndef solve() -> None:\n    import sys\n    input = sys.stdin.readline\n    n = int(input())\n    graph = [[] for _ in range(n)]\n    for _ in range(n - 1):\n        u, v = map(int, input().split())\n        u -= 1\n        v -= 1\n        graph[u].append(v)\n        graph[v].append(u)\n    s, _, _ = farthest(0, graph)\n    t, diameter, _ = farthest(s, graph)\n    u, v = sorted((s + 1, t + 1))\n    print(u, v, diameter)\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
