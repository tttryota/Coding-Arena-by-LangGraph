from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('foundation')

UNIT_BANK = unit_bank(
    unit_id='algo-022-practice',
    title='ダイクストラ法 を素直に実装する',
    unit_kind='foundation',
    target_skill='ダイクストラ法 を素直に実装する',
    concept_overview='ダイクストラ法では、始点から各頂点への最短距離を 1 本の dist 配列に持って更新します。ここでは終点 1 個ではなく、全頂点の距離列を出します。',
    problem_bank=[
        problem(
            problem_id='algo-022-practice-p1',
            title='ダイクストラ法 を素直に実装する / 頂点 1 から全頂点への距離を出力する',
            problem_statement='N 頂点 M 辺の有向重み付きグラフが与えられる。頂点 1 から各頂点への最短距離をダイクストラ法で求めよ。到達できない頂点については -1 を出力する。',
            input_format='1 行目に N M。\n続く M 行に u v w。',
            output_format='dist[1], dist[2], ..., dist[N] を空白区切りで出力する。',
            constraints='1 <= N, M <= 2 * 10^5\n1 <= w <= 10^9',
            examples=[{'input': '5 5\n1 2 2\n1 3 7\n2 3 1\n2 4 4\n3 4 3', 'output': '0 2 3 6 -1'}],
            canonical_reference_solution="import heapq\n\n\ndef solve() -> None:\n    import sys\n    input = sys.stdin.readline\n    n, m = map(int, input().split())\n    graph = [[] for _ in range(n)]\n    for _ in range(m):\n        u, v, w = map(int, input().split())\n        graph[u - 1].append((v - 1, w))\n    inf = 10 ** 30\n    dist = [inf] * n\n    dist[0] = 0\n    heap = [(0, 0)]\n    while heap:\n        cost, node = heapq.heappop(heap)\n        if cost != dist[node]:\n            continue\n        for nxt, w in graph[node]:\n            nd = cost + w\n            if nd < dist[nxt]:\n                dist[nxt] = nd\n                heapq.heappush(heap, (nd, nxt))\n    print(*(-1 if value == inf else value for value in dist))\n\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
