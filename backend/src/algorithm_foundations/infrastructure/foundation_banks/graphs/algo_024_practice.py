from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('foundation')

UNIT_BANK = unit_bank(
    unit_id='algo-024-practice',
    title='ワーシャルフロイド法 を素直に実装する',
    unit_kind='foundation',
    target_skill='ワーシャルフロイド法 を素直に実装する',
    concept_overview='到達可能性の次は、「到達できる」だけでなく最短で何本の辺を通るかまで持たせます。ここでは重みなしグラフで、全点対の最短距離を辺数として求めます。',
    problem_bank=[
        problem(
            problem_id='algo-024-practice-p1',
            title='ワーシャルフロイド法 を素直に実装する / 重みなし有向グラフの全点対最短距離を辺数で出力する',
            problem_statement='N 頂点 M 辺の有向グラフが与えられる。ワーシャルフロイド法で全点対間の最短距離を求め、dist 行列を出力せよ。距離は通る辺数で測る。到達できない組は INF とする。',
            input_format='1 行目に N M。\n続く M 行に u v。',
            output_format='N 行出力する。i 行目には dist[i][1], dist[i][2], ..., dist[i][N] を空白区切りで出力し、到達できない値は INF とする。',
            constraints='1 <= N <= 300\n1 <= M <= 2 * 10^5',
            examples=[{'input': '4 4\n1 2\n2 3\n1 4\n4 3', 'output': '0 1 2 1\nINF 0 1 INF\nINF INF 0 INF\nINF INF 1 0'}],
            canonical_reference_solution="def solve() -> None:\n    import sys\n    input = sys.stdin.readline\n    n, m = map(int, input().split())\n    inf = 10 ** 18\n    dist = [[inf] * n for _ in range(n)]\n    for i in range(n):\n        dist[i][i] = 0\n    for _ in range(m):\n        u, v = map(int, input().split())\n        u -= 1\n        v -= 1\n        dist[u][v] = 1\n    for k in range(n):\n        for i in range(n):\n            dik = dist[i][k]\n            if dik == inf:\n                continue\n            row_i = dist[i]\n            row_k = dist[k]\n            for j in range(n):\n                nd = dik + row_k[j]\n                if nd < row_i[j]:\n                    row_i[j] = nd\n    rows = []\n    for row in dist:\n        rows.append(' '.join(str(value) if value != inf else 'INF' for value in row))\n    print('\\n'.join(rows))\n\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
