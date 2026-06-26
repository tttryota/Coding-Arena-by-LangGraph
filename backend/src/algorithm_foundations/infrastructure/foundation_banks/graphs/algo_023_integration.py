from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('integration')

UNIT_BANK = unit_bank(
    unit_id='algo-023-integration',
    title='ベルマンフォード法 の総合演習',
    unit_kind='integration',
    target_skill='ベルマンフォード法 の総合演習',
    concept_overview='ベルマンフォード法では、最短距離計算と負閉路検出を組み合わせて「距離を返せるのか、それとも負閉路で壊れるのか」をまとめて判断できます。ここでは全頂点距離を出す前に負閉路の有無を確認します。',
    problem_bank=[
        problem(
            problem_id='algo-023-integration-p1',
            title='ベルマンフォード法 の総合演習 / 負閉路がなければ 1 から各頂点への最短距離を出力する',
            problem_statement='N 頂点 M 辺の有向重み付きグラフが与えられる。重みは負でもよい。頂点 1 から到達できる負閉路が存在するなら `NEGATIVE CYCLE` を出力せよ。存在しないなら、頂点 1 から各頂点への最短距離を頂点番号順に出力せよ。到達できない頂点の距離は -1 とする。',
            input_format='1 行目に N M。\n続く M 行に u v w。',
            output_format='負閉路があるなら 1 行に `NEGATIVE CYCLE` を出力する。ないなら N 個の最短距離を空白区切りで出力する。',
            constraints='1 <= N <= 500\n1 <= M <= 10000\n-10^9 <= w <= 10^9',
            examples=[{'input': '4 5\n1 2 3\n2 3 -2\n3 4 4\n1 3 10\n2 4 8', 'output': '0 3 1 5'}],
            canonical_reference_solution="def solve() -> None:\n    import sys\n    input = sys.stdin.readline\n    n, m = map(int, input().split())\n    edges = []\n    inf = 10 ** 18\n    dist = [inf] * n\n    dist[0] = 0\n    for _ in range(m):\n        u, v, w = map(int, input().split())\n        edges.append((u - 1, v - 1, w))\n    for step in range(n):\n        updated = False\n        for u, v, w in edges:\n            if dist[u] == inf:\n                continue\n            nd = dist[u] + w\n            if nd < dist[v]:\n                dist[v] = nd\n                updated = True\n                if step == n - 1:\n                    print('NEGATIVE CYCLE')\n                    return\n        if not updated:\n            break\n    print(*(-1 if d == inf else d for d in dist))\n\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
