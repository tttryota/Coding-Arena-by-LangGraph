from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('foundation')

UNIT_BANK = unit_bank(
    unit_id='algo-035-practice',
    title='関節点・橋の検出 を素直に実装する',
    unit_kind='foundation',
    target_skill='関節点・橋の検出 を素直に実装する',
    concept_overview='橋の検出では、DFS 木の子側から返る low 値を見て、その辺を戻り辺で飛び越えられるかを判定します。親辺を除外しながら order と low を更新する実装の流れを確かめます。',
    problem_bank=[
        problem(
            problem_id='algo-035-practice-p1',
            title='関節点・橋の検出 を素直に実装する / 橋になっている辺を列挙する',
            problem_statement='無向グラフが与えられる。橋になっている辺の入力番号を昇順で列挙せよ。',
            input_format='1 行目に N M。\n続く M 行に辺 u v。',
            output_format='1 行目に橋の本数 K。2 行目に橋の入力番号を昇順で出力する。橋がなければ 2 行目は空でよい。',
            constraints='1 <= N <= 2 * 10^5\n0 <= M <= 2 * 10^5',
            examples=[{'input': '5 5\n1 2\n2 3\n3 1\n3 4\n4 5', 'output': '2\n4 5'}],
            canonical_reference_solution="def solve() -> None:\n    import sys\n    sys.setrecursionlimit(10 ** 7)\n    input = sys.stdin.readline\n    n, m = map(int, input().split())\n    graph = [[] for _ in range(n)]\n    for idx in range(m):\n        u, v = map(int, input().split())\n        u -= 1\n        v -= 1\n        graph[u].append((v, idx + 1))\n        graph[v].append((u, idx + 1))\n    order = [-1] * n\n    low = [0] * n\n    timer = 0\n    bridges = []\n\n    def dfs(node: int, parent_edge: int) -> None:\n        nonlocal timer\n        order[node] = low[node] = timer\n        timer += 1\n        for nxt, edge_id in graph[node]:\n            if edge_id == parent_edge:\n                continue\n            if order[nxt] == -1:\n                dfs(nxt, edge_id)\n                low[node] = min(low[node], low[nxt])\n                if order[node] < low[nxt]:\n                    bridges.append(edge_id)\n            else:\n                low[node] = min(low[node], order[nxt])\n\n    for node in range(n):\n        if order[node] == -1:\n            dfs(node, -1)\n    bridges.sort()\n    print(len(bridges))\n    print(*bridges)\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
