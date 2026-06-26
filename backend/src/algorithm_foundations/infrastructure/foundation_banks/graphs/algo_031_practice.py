from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('foundation')

UNIT_BANK = unit_bank(
    unit_id='algo-031-practice',
    title='強連結成分分解（SCC） を素直に実装する',
    unit_kind='foundation',
    target_skill='強連結成分分解（SCC） を素直に実装する',
    concept_overview='SCC 分解では、個数だけでなく各頂点がどの成分に属するか、成分の大きさがいくつかも復元できます。逆辺 DFS で塊を実際に塗る流れを確かめます。',
    problem_bank=[
        problem(
            problem_id='algo-031-practice-p1',
            title='強連結成分分解（SCC） を素直に実装する / 各頂点が属する強連結成分の大きさを求める',
            problem_statement='有向グラフが与えられる。各頂点について、その頂点が属する強連結成分の大きさを求めよ。',
            input_format='1 行目に N M。\n続く M 行に辺 u v。',
            output_format='1 行に N 個、各頂点が属する強連結成分の大きさを出力する。',
            constraints='1 <= N <= 2 * 10^5\n0 <= M <= 2 * 10^5',
            examples=[{'input': '5 6\n1 2\n2 1\n2 3\n3 4\n4 3\n4 5', 'output': '2 2 2 2 1'}],
            canonical_reference_solution="def solve() -> None:\n    import sys\n    sys.setrecursionlimit(10 ** 7)\n    input = sys.stdin.readline\n    n, m = map(int, input().split())\n    graph = [[] for _ in range(n)]\n    rev = [[] for _ in range(n)]\n    for _ in range(m):\n        u, v = map(int, input().split())\n        u -= 1\n        v -= 1\n        graph[u].append(v)\n        rev[v].append(u)\n    order = []\n    seen = [False] * n\n\n    def dfs(node: int) -> None:\n        seen[node] = True\n        for nxt in graph[node]:\n            if not seen[nxt]:\n                dfs(nxt)\n        order.append(node)\n\n    component = [-1] * n\n    sizes = []\n\n    def rdfs(node: int, cid: int) -> int:\n        component[node] = cid\n        size = 1\n        for nxt in rev[node]:\n            if component[nxt] == -1:\n                size += rdfs(nxt, cid)\n        return size\n\n    for node in range(n):\n        if not seen[node]:\n            dfs(node)\n    cid = 0\n    for node in reversed(order):\n        if component[node] != -1:\n            continue\n        sizes.append(rdfs(node, cid))\n        cid += 1\n    print(*[sizes[component[i]] for i in range(n)])\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
