from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('foundation')

UNIT_BANK = unit_bank(
    unit_id='algo-125-practice',
    title='最小カット を素直に実装する',
    unit_kind='foundation',
    target_skill='最小カット を素直に実装する',
    concept_overview='source 側頂点集合が分かると、そこから sink 側へ出ていく元辺のうち容量が cut を構成する辺も列挙できます。ここでは最小カットに含まれる辺番号まで復元します。',
    problem_bank=[
        problem(
            problem_id='algo-125-practice-p1',
            title='最小カット を素直に実装する / ある最小カットを構成する辺番号を列挙する',
            problem_statement='容量付き有向グラフが与えられる。頂点 1 から頂点 N への最小カットを 1 つ取り、その cut をまたぐ元辺の入力番号を昇順で出力せよ。',
            input_format='1 行目に N M。\n続く M 行に u v c。',
            output_format='1 行目に cut 辺数 K、2 行目にその入力番号を昇順で出力する。存在しなければ 2 行目は空でよい。',
            constraints='2 <= N <= 2 * 10^5\n1 <= M <= 2 * 10^5\n1 <= c <= 10^9',
            examples=[{'input': '4 5\n1 2 2\n1 3 1\n2 3 1\n2 4 1\n3 4 2', 'output': '2\n1 2'}],
            canonical_reference_solution="from collections import deque\n\ndef solve() -> None:\n    import sys\n    sys.setrecursionlimit(10 ** 7)\n    input = sys.stdin.readline\n    n, m = map(int, input().split())\n    graph = [[] for _ in range(n)]\n    original_edges = []\n\n    def add_edge(u: int, v: int, cap: int) -> None:\n        graph[u].append([v, cap, len(graph[v])])\n        graph[v].append([u, 0, len(graph[u]) - 1])\n        original_edges.append((u, v))\n\n    for _ in range(m):\n        u, v, c = map(int, input().split())\n        add_edge(u - 1, v - 1, c)\n\n    level = [0] * n\n    it = [0] * n\n\n    def bfs() -> bool:\n        level[:] = [-1] * n\n        dq = deque([0])\n        level[0] = 0\n        while dq:\n            node = dq.popleft()\n            for nxt, cap, _ in graph[node]:\n                if cap > 0 and level[nxt] == -1:\n                    level[nxt] = level[node] + 1\n                    dq.append(nxt)\n        return level[n - 1] != -1\n\n    def dfs(node: int, flow: int) -> int:\n        if node == n - 1:\n            return flow\n        while it[node] < len(graph[node]):\n            edge = graph[node][it[node]]\n            nxt, cap, rev = edge\n            if cap > 0 and level[node] + 1 == level[nxt]:\n                pushed = dfs(nxt, min(flow, cap))\n                if pushed:\n                    edge[1] -= pushed\n                    graph[nxt][rev][1] += pushed\n                    return pushed\n            it[node] += 1\n        return 0\n\n    while bfs():\n        it[:] = [0] * n\n        while True:\n            pushed = dfs(0, 10 ** 18)\n            if pushed == 0:\n                break\n\n    seen = [False] * n\n    dq = deque([0])\n    seen[0] = True\n    while dq:\n        node = dq.popleft()\n        for nxt, cap, _ in graph[node]:\n            if cap > 0 and not seen[nxt]:\n                seen[nxt] = True\n                dq.append(nxt)\n\n    ans = []\n    for idx, (u, v) in enumerate(original_edges, start=1):\n        if seen[u] and not seen[v]:\n            ans.append(idx)\n    print(len(ans))\n    print(*ans)\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
