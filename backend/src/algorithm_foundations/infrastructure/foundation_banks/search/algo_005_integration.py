from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('integration')

UNIT_BANK = unit_bank(
    unit_id='algo-005-integration',
    title='幅優先探索（BFS） の総合演習',
    unit_kind='integration',
    target_skill='幅優先探索（BFS） の総合演習',
    concept_overview='BFS は始点を複数まとめてキューへ入れても使えます。ここでは複数の避難所から最も近い場所までの距離を一度に求めます。',
    problem_bank=[
        problem(
            problem_id='algo-005-integration-p1',
            title='幅優先探索（BFS） の総合演習 / 最も近い避難所までの距離を全頂点について求める',
            problem_statement='N 頂点 M 辺の無向グラフと、避難所がある K 個の頂点が与えられる。各頂点 v について、最も近い避難所までの辺数を求めよ。どの避難所にも到達できない頂点は -1 とする。',
            input_format='1 行目に N M K。\n続く M 行に辺 u v。\n最後の 1 行に避難所の頂点番号 s_1..s_K。',
            output_format='各頂点の答えを空白区切りで出力する。',
            constraints='1 <= N <= 2 * 10^5\n0 <= M <= 2 * 10^5\n1 <= K <= N',
            examples=[{'input': '6 4 2\n1 2\n2 3\n4 5\n5 6\n2 6', 'output': '1 0 1 2 1 0'}],
            canonical_reference_solution="from collections import deque\n\n\ndef solve() -> None:\n    import sys\n    input = sys.stdin.readline\n    n, m, k = map(int, input().split())\n    graph = [[] for _ in range(n)]\n    for _ in range(m):\n        u, v = map(int, input().split())\n        u -= 1\n        v -= 1\n        graph[u].append(v)\n        graph[v].append(u)\n    sources = [x - 1 for x in map(int, input().split())]\n    dist = [-1] * n\n    dq = deque()\n    for src in sources:\n        if dist[src] != -1:\n            continue\n        dist[src] = 0\n        dq.append(src)\n    while dq:\n        node = dq.popleft()\n        for nxt in graph[node]:\n            if dist[nxt] != -1:\n                continue\n            dist[nxt] = dist[node] + 1\n            dq.append(nxt)\n    print(*dist)\n\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
