from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('foundation')

UNIT_BANK = unit_bank(
    unit_id='algo-027-practice',
    title='トポロジカルソート を素直に実装する',
    unit_kind='foundation',
    target_skill='トポロジカルソート を素直に実装する',
    concept_overview='トポロジカルソートでは、順序を作れるかどうか自体が重要な情報になります。ここでは閉路がある場合に順序が作れないことも含めて判定します。',
    problem_bank=[
        problem(
            problem_id='algo-027-practice-p1',
            title='トポロジカルソート を素直に実装する / トポロジカル順序が存在するなら 1 つ出力し、存在しなければ -1 を出力する',
            problem_statement='N 頂点 M 辺の有向グラフが与えられる。トポロジカル順序が存在するなら 1 つ出力し、存在しなければ -1 を出力せよ。',
            input_format='1 行目に N M。\n続く M 行に辺 u v。',
            output_format='存在するならトポロジカル順序を空白区切りで出力し、存在しなければ -1 を出力する。',
            constraints='1 <= N <= 2 * 10^5\n0 <= M <= 2 * 10^5',
            examples=[{'input': '3 3\n1 2\n2 3\n3 1', 'output': '-1'}],
            canonical_reference_solution="from collections import deque\n\n\ndef solve() -> None:\n    import sys\n    input = sys.stdin.readline\n    n, m = map(int, input().split())\n    graph = [[] for _ in range(n)]\n    indeg = [0] * n\n    for _ in range(m):\n        u, v = map(int, input().split())\n        u -= 1\n        v -= 1\n        graph[u].append(v)\n        indeg[v] += 1\n    dq = deque(i for i, deg in enumerate(indeg) if deg == 0)\n    order = []\n    while dq:\n        node = dq.popleft()\n        order.append(node + 1)\n        for nxt in graph[node]:\n            indeg[nxt] -= 1\n            if indeg[nxt] == 0:\n                dq.append(nxt)\n    if len(order) != n:\n        print(-1)\n        return\n    print(*order)\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
