from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('foundation')

UNIT_BANK = unit_bank(
    unit_id='algo-027-basic',
    title='トポロジカルソート の基本',
    unit_kind='foundation',
    target_skill='トポロジカルソート の基本',
    concept_overview='トポロジカルソートは、依存関係を壊さない順番に頂点を並べる考え方です。まずは DAG に対して 1 つ順序を作る基本形を押さえます。',
    problem_bank=[
        problem(
            problem_id='algo-027-basic-p1',
            title='トポロジカルソート の基本 / トポロジカル順序を 1 つ出力する',
            problem_statement='N 頂点 M 辺の有向非巡回グラフが与えられる。トポロジカル順序を 1 つ出力せよ。',
            input_format='1 行目に N M。\n続く M 行に辺 u v。',
            output_format='トポロジカル順序を空白区切りで出力する。',
            constraints='1 <= N <= 2 * 10^5\n0 <= M <= 2 * 10^5',
            examples=[{'input': '4 3\n1 2\n1 3\n3 4', 'output': '1 2 3 4'}],
            canonical_reference_solution="from collections import deque\n\n\ndef solve() -> None:\n    import sys\n    input = sys.stdin.readline\n    n, m = map(int, input().split())\n    graph = [[] for _ in range(n)]\n    indeg = [0] * n\n    for _ in range(m):\n        u, v = map(int, input().split())\n        u -= 1\n        v -= 1\n        graph[u].append(v)\n        indeg[v] += 1\n    dq = deque(i for i, deg in enumerate(indeg) if deg == 0)\n    order = []\n    while dq:\n        node = dq.popleft()\n        order.append(node + 1)\n        for nxt in graph[node]:\n            indeg[nxt] -= 1\n            if indeg[nxt] == 0:\n                dq.append(nxt)\n    print(*order)\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
