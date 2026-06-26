from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('integration')

UNIT_BANK = unit_bank(
    unit_id='algo-024-integration',
    title='ワーシャルフロイド法 の総合演習',
    unit_kind='integration',
    target_skill='ワーシャルフロイド法 の総合演習',
    concept_overview='全点対の最短距離が辺数で分かると、「どの頂点を拠点にすると最悪でも何歩で届くか」の集約もできます。ここでは重みなしグラフの中心を求めます。',
    problem_bank=[
        problem(
            problem_id='algo-024-integration-p1',
            title='ワーシャルフロイド法 の総合演習 / 最も遠い頂点までの辺数が最小の拠点を選ぶ',
            problem_statement='N 頂点 M 辺の無向グラフが与えられる。各頂点 v について、v から他のすべての頂点への最短距離の最大値を eccentricity(v) とする。距離は通る辺数で測る。eccentricity が最小の頂点番号とその値を求めよ。複数あるときは頂点番号が最小のものを選ぶ。グラフが連結でないなら -1 を出力する。',
            input_format='1 行目に N M。\n続く M 行に u v。',
            output_format='条件を満たす頂点番号と eccentricity を空白区切りで出力する。連結でないなら -1 を出力する。',
            constraints='1 <= N <= 300\n1 <= M <= 2 * 10^5',
            examples=[{'input': '4 3\n1 2\n2 3\n2 4', 'output': '2 1'}],
            canonical_reference_solution="def solve() -> None:\n    import sys\n    input = sys.stdin.readline\n    n, m = map(int, input().split())\n    inf = 10 ** 18\n    dist = [[inf] * n for _ in range(n)]\n    for i in range(n):\n        dist[i][i] = 0\n    for _ in range(m):\n        u, v = map(int, input().split())\n        u -= 1\n        v -= 1\n        dist[u][v] = 1\n        dist[v][u] = 1\n    for k in range(n):\n        for i in range(n):\n            dik = dist[i][k]\n            if dik == inf:\n                continue\n            row_i = dist[i]\n            row_k = dist[k]\n            for j in range(n):\n                nd = dik + row_k[j]\n                if nd < row_i[j]:\n                    row_i[j] = nd\n    best_vertex = -1\n    best_value = inf\n    for i in range(n):\n        farthest = max(dist[i])\n        if farthest == inf:\n            print(-1)\n            return\n        if farthest < best_value:\n            best_value = farthest\n            best_vertex = i + 1\n    print(best_vertex, best_value)\n\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
