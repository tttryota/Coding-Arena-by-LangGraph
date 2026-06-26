from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('foundation')

UNIT_BANK = unit_bank(
    unit_id='algo-030-basic',
    title='最小共通祖先（LCA） の基本',
    unit_kind='foundation',
    target_skill='最小共通祖先（LCA） の基本',
    concept_overview='最小共通祖先は、木の 2 頂点に対して共通の祖先のうち最も深いものを求める考え方です。木の親子関係を前計算して質問に素早く答える形を学びます。',
    problem_bank=[
        problem(
            problem_id='algo-030-basic-p1',
            title='最小共通祖先（LCA） の基本 / 各問い合わせについて最小共通祖先を求める',
            problem_statement='根 1 の木と Q 個の問い合わせ u v が与えられる。各問い合わせについて最小共通祖先を求めよ。',
            input_format='1 行目に N Q。\n続く N-1 行に辺 u v。\n続く Q 行に u v。',
            output_format='各問い合わせの答えを 1 行ずつ出力する。',
            constraints='1 <= N, Q <= 2 * 10^5',
            examples=[{'input': '5 3\n1 2\n1 3\n3 4\n3 5\n2 4\n4 5\n2 5', 'output': '1\n3\n1'}],
            canonical_reference_solution="def solve() -> None:\n    import sys\n    sys.setrecursionlimit(10 ** 7)\n    input = sys.stdin.readline\n    n, q = map(int, input().split())\n    graph = [[] for _ in range(n)]\n    for _ in range(n - 1):\n        u, v = map(int, input().split())\n        u -= 1\n        v -= 1\n        graph[u].append(v)\n        graph[v].append(u)\n    log = n.bit_length()\n    parent = [[-1] * n for _ in range(log)]\n    depth = [0] * n\n\n    def dfs(node: int, par: int) -> None:\n        parent[0][node] = par\n        for nxt in graph[node]:\n            if nxt == par:\n                continue\n            depth[nxt] = depth[node] + 1\n            dfs(nxt, node)\n\n    dfs(0, -1)\n    for k in range(1, log):\n        for node in range(n):\n            prev = parent[k - 1][node]\n            parent[k][node] = -1 if prev == -1 else parent[k - 1][prev]\n\n    def lca(u: int, v: int) -> int:\n        if depth[u] < depth[v]:\n            u, v = v, u\n        diff = depth[u] - depth[v]\n        for k in range(log):\n            if diff >> k & 1:\n                u = parent[k][u]\n        if u == v:\n            return u\n        for k in range(log - 1, -1, -1):\n            if parent[k][u] != parent[k][v]:\n                u = parent[k][u]\n                v = parent[k][v]\n        return parent[0][u]\n\n    out = []\n    for _ in range(q):\n        u, v = map(int, input().split())\n        out.append(str(lca(u - 1, v - 1) + 1))\n    sys.stdout.write('\\n'.join(out))\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
