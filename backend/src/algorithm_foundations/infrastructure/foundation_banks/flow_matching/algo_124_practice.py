from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('foundation')

UNIT_BANK = unit_bank(
    unit_id='algo-124-practice',
    title='最大フロー（Dinic法） を素直に実装する',
    unit_kind='foundation',
    target_skill='最大フロー（Dinic法） を素直に実装する',
    concept_overview='Dinic 法では、最大フロー値だけでなく、各元辺にどれだけ流れたかも残余容量から復元できます。ここでは残余辺を更新しながら、入力された各辺の実流量まで追いかけます。',
    problem_bank=[
        problem(
            problem_id='algo-124-practice-p1',
            title='最大フロー（Dinic法） を素直に実装する / 最大フロー後の各辺の流量を復元する',
            problem_statement='容量付き有向グラフが与えられる。頂点 1 から頂点 N への最大フローを流したあと、入力された各辺に実際に流れた量を入力順に出力せよ。',
            input_format='1 行目に N M。\n続く M 行に u v c。',
            output_format='M 行出力せよ。i 行目に i 番目の辺へ流れた量を出力する。',
            constraints='2 <= N <= 2 * 10^5\n1 <= M <= 2 * 10^5\n1 <= c <= 10^9',
            examples=[{'input': '4 5\n1 2 2\n1 3 1\n2 3 1\n2 4 1\n3 4 2', 'output': '2\n1\n1\n1\n2'}],
            canonical_reference_solution="from collections import deque\n\ndef solve() -> None:\n    import sys\n    sys.setrecursionlimit(10 ** 7)\n    input = sys.stdin.readline\n    n, m = map(int, input().split())\n    graph = [[] for _ in range(n)]\n    edge_refs = []\n\n    def add_edge(u: int, v: int, cap: int) -> None:\n        graph[u].append([v, cap, len(graph[v])])\n        graph[v].append([u, 0, len(graph[u]) - 1])\n        edge_refs.append((u, len(graph[u]) - 1, cap))\n\n    for _ in range(m):\n        u, v, c = map(int, input().split())\n        add_edge(u - 1, v - 1, c)\n\n    level = [0] * n\n    it = [0] * n\n\n    def bfs() -> bool:\n        level[:] = [-1] * n\n        dq = deque([0])\n        level[0] = 0\n        while dq:\n            node = dq.popleft()\n            for nxt, cap, _ in graph[node]:\n                if cap > 0 and level[nxt] == -1:\n                    level[nxt] = level[node] + 1\n                    dq.append(nxt)\n        return level[n - 1] != -1\n\n    def dfs(node: int, flow: int) -> int:\n        if node == n - 1:\n            return flow\n        while it[node] < len(graph[node]):\n            edge = graph[node][it[node]]\n            nxt, cap, rev = edge\n            if cap > 0 and level[node] + 1 == level[nxt]:\n                pushed = dfs(nxt, min(flow, cap))\n                if pushed:\n                    edge[1] -= pushed\n                    graph[nxt][rev][1] += pushed\n                    return pushed\n            it[node] += 1\n        return 0\n\n    while bfs():\n        it[:] = [0] * n\n        while True:\n            pushed = dfs(0, 10 ** 18)\n            if pushed == 0:\n                break\n\n    out = []\n    for u, idx, original_cap in edge_refs:\n        residual_cap = graph[u][idx][1]\n        out.append(str(original_cap - residual_cap))\n    sys.stdout.write('\\n'.join(out))\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
