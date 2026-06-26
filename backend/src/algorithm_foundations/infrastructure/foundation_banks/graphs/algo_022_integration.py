from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('integration')

UNIT_BANK = unit_bank(
    unit_id='algo-022-integration',
    title='ダイクストラ法 の総合演習',
    unit_kind='integration',
    target_skill='ダイクストラ法 の総合演習',
    concept_overview='ダイクストラ法は、始点を 1 つに限らず複数同時に置くこともできます。初期距離 0 の頂点をまとめて heap に入れると、「最も近い施設までの距離」を一度に求められます。',
    problem_bank=[
        problem(
            problem_id='algo-022-integration-p1',
            title='ダイクストラ法 の総合演習 / 最も近い施設までの距離を全頂点について求める',
            problem_statement='N 頂点 M 辺の有向重み付きグラフと、施設が置かれている K 個の頂点が与えられる。すべての辺重みは 0 以上である。各頂点 v について、v から到達できる施設のうち最短距離を求めよ。どの施設にも到達できない頂点は -1 を出力する。',
            input_format='1 行目に N M K。\n続く M 行に u v w。\n最後の 1 行に施設の頂点番号 f_1..f_K。',
            output_format='各頂点について答えを空白区切りで出力する。',
            constraints='1 <= N, M <= 2 * 10^5\n1 <= K <= N\n1 <= w <= 10^9',
            examples=[{'input': '5 5 2\n1 2 2\n2 3 3\n1 4 1\n4 3 1\n5 3 4\n3 5', 'output': '2 3 0 1 0'}],
            canonical_reference_solution="import heapq\n\n\ndef solve() -> None:\n    import sys\n    input = sys.stdin.readline\n    n, m, k = map(int, input().split())\n    rev = [[] for _ in range(n)]\n    for _ in range(m):\n        u, v, w = map(int, input().split())\n        rev[v - 1].append((u - 1, w))\n    facilities = [x - 1 for x in map(int, input().split())]\n    inf = 10 ** 30\n    dist = [inf] * n\n    heap = []\n    for node in facilities:\n        if dist[node] == 0:\n            continue\n        dist[node] = 0\n        heapq.heappush(heap, (0, node))\n    while heap:\n        cost, node = heapq.heappop(heap)\n        if cost != dist[node]:\n            continue\n        for nxt, w in rev[node]:\n            nd = cost + w\n            if nd < dist[nxt]:\n                dist[nxt] = nd\n                heapq.heappush(heap, (nd, nxt))\n    print(*(-1 if value == inf else value for value in dist))\n\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
