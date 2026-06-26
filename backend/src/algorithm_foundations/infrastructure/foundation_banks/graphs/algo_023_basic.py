from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('foundation')

UNIT_BANK = unit_bank(
    unit_id='algo-023-basic',
    title='ベルマンフォード法 の基本',
    unit_kind='foundation',
    target_skill='ベルマンフォード法 の基本',
    concept_overview='ベルマンフォード法は、全辺の緩和を何回も繰り返して負辺ありの最短距離を求める方法です。まずは始点 1 から終点 N までの距離を安定させる基本形を押さえます。',
    problem_bank=[
        problem(
            problem_id='algo-023-basic-p1',
            title='ベルマンフォード法 の基本 / 負辺ありで 1 から N の最短距離を求める',
            problem_statement='N 頂点 M 辺の有向重み付きグラフが与えられる。重みは負でもよい。頂点 1 から頂点 N への最短距離をベルマンフォード法で求めよ。始点から到達できる負閉路は存在しないものとする。到達できなければ -1 を出力する。',
            input_format='1 行目に N M。\n続く M 行に u v w。',
            output_format='頂点 1 から頂点 N までの最短距離を出力する。',
            constraints='1 <= N <= 500\n1 <= M <= 10000\n-10^9 <= w <= 10^9',
            examples=[{'input': '4 5\n1 2 3\n2 3 -2\n3 4 4\n1 3 10\n2 4 8', 'output': '5'}],
            canonical_reference_solution="def solve() -> None:\n    import sys\n    input = sys.stdin.readline\n    n, m = map(int, input().split())\n    edges = [tuple(map(int, input().split())) for _ in range(m)]\n    INF = 10 ** 18\n    dist = [INF] * n\n    dist[0] = 0\n    for _ in range(n - 1):\n        updated = False\n        for u, v, w in edges:\n            if dist[u - 1] == INF:\n                continue\n            nd = dist[u - 1] + w\n            if nd < dist[v - 1]:\n                dist[v - 1] = nd\n                updated = True\n        if not updated:\n            break\n    print(-1 if dist[-1] == INF else dist[-1])\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
