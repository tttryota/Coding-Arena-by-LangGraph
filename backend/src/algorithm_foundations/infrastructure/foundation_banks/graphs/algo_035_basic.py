from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('foundation')

UNIT_BANK = unit_bank(
    unit_id='algo-035-basic',
    title='関節点・橋の検出 の基本',
    unit_kind='foundation',
    target_skill='関節点・橋の検出 の基本',
    concept_overview='関節点・橋の検出は、DFS の訪問順と lowlink を使って「そこを外すとつながりが切れる辺や頂点」を見つける知識です。まずは橋判定に必要な order と low の意味を基本から押さえます。',
    problem_bank=[
        problem(
            problem_id='algo-035-basic-p1',
            title='関節点・橋の検出 の基本 / 橋の本数を求める',
            problem_statement='無向グラフが与えられる。橋の本数を求めよ。',
            input_format='1 行目に N M。\n続く M 行に辺 u v。',
            output_format='橋の本数を出力する。',
            constraints='1 <= N <= 2 * 10^5\n0 <= M <= 2 * 10^5',
            examples=[{'input': '5 5\n1 2\n2 3\n3 1\n3 4\n4 5', 'output': '2'}],
            canonical_reference_solution="def solve() -> None:\n    import sys\n    sys.setrecursionlimit(10 ** 7)\n    input = sys.stdin.readline\n    n, m = map(int, input().split())\n    graph = [[] for _ in range(n)]\n    for idx in range(m):\n        u, v = map(int, input().split())\n        u -= 1\n        v -= 1\n        graph[u].append((v, idx))\n        graph[v].append((u, idx))\n    order = [-1] * n\n    low = [0] * n\n    timer = 0\n    bridges = 0\n\n    def dfs(node: int, parent_edge: int) -> None:\n        nonlocal timer, bridges\n        order[node] = low[node] = timer\n        timer += 1\n        for nxt, edge_id in graph[node]:\n            if edge_id == parent_edge:\n                continue\n            if order[nxt] == -1:\n                dfs(nxt, edge_id)\n                low[node] = min(low[node], low[nxt])\n                if order[node] < low[nxt]:\n                    bridges += 1\n            else:\n                low[node] = min(low[node], order[nxt])\n\n    for node in range(n):\n        if order[node] == -1:\n            dfs(node, -1)\n    print(bridges)\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
