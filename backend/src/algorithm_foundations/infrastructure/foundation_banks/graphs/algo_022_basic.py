from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('foundation')

UNIT_BANK = unit_bank(
    unit_id='algo-022-basic',
    title='ダイクストラ法 の基本',
    unit_kind='foundation',
    target_skill='ダイクストラ法 の基本',
    concept_overview='ダイクストラ法の核は、「未確定の中で最短距離が最小の頂点を 1 つ確定する」を繰り返すことです。まずは小さめの制約で、優先度付きキューを使わない基本形を学びます。',
    problem_bank=[
        problem(
            problem_id='algo-022-basic-p1',
            title='ダイクストラ法 の基本 / 小さいグラフで 1 から N の最短距離を求める',
            problem_statement='N 頂点 M 辺の有向重み付きグラフが与えられる。すべての辺重みは 0 以上である。頂点 1 から頂点 N への最短距離をダイクストラ法で求め、到達できないなら -1 を出力せよ。ここでは優先度付きキューを使わず、毎回もっとも距離の小さい未確定頂点を選ぶ実装でよい。',
            input_format='1 行目に N M。\n続く M 行に u v w。',
            output_format='頂点 1 から頂点 N までの最短距離を出力する。',
            constraints='1 <= N <= 500\n1 <= M <= 5000\n0 <= w <= 10^9',
            examples=[{'input': '4 4\n1 2 3\n2 4 5\n1 3 10\n3 4 1', 'output': '8'}],
            canonical_reference_solution="def solve() -> None:\n    import sys\n    input = sys.stdin.readline\n    n, m = map(int, input().split())\n    graph = [[] for _ in range(n)]\n    for _ in range(m):\n        u, v, w = map(int, input().split())\n        graph[u - 1].append((v - 1, w))\n    inf = 10 ** 30\n    dist = [inf] * n\n    used = [False] * n\n    dist[0] = 0\n    for _ in range(n):\n        node = -1\n        best = inf\n        for v in range(n):\n            if not used[v] and dist[v] < best:\n                best = dist[v]\n                node = v\n        if node == -1:\n            break\n        used[node] = True\n        for nxt, w in graph[node]:\n            nd = dist[node] + w\n            if nd < dist[nxt]:\n                dist[nxt] = nd\n    print(-1 if dist[-1] == inf else dist[-1])\n\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
