from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('foundation')

UNIT_BANK = unit_bank(
    unit_id='algo-023-practice',
    title='ベルマンフォード法 を素直に実装する',
    unit_kind='foundation',
    target_skill='ベルマンフォード法 で負閉路を検出する',
    concept_overview='ベルマンフォード法では、N-1 回の緩和で最短距離が定まり、その後も更新できるなら始点から到達可能な負閉路があると分かります。ここでは最短距離計算と一体になった負閉路検出を実装します。',
    problem_bank=[
        problem(
            problem_id='algo-023-practice-p1',
            title='ベルマンフォード法 で負閉路を検出する / 始点から届く負閉路があるか判定する',
            problem_statement='N 頂点 M 辺の有向重み付きグラフが与えられる。重みは負でもよい。頂点 1 から到達可能な負閉路が存在するなら Yes、存在しないなら No を出力せよ。',
            input_format='1 行目に N M。\n続く M 行に u v w。',
            output_format='Yes または No を出力する。',
            constraints='1 <= N <= 500\n1 <= M <= 10000\n-10^9 <= w <= 10^9',
            examples=[{'input': '4 4\n1 2 1\n2 3 -2\n3 2 -2\n3 4 5', 'output': 'Yes'}],
            canonical_reference_solution="def solve() -> None:\n    import sys\n    input = sys.stdin.readline\n    n, m = map(int, input().split())\n    edges = [tuple(map(int, input().split())) for _ in range(m)]\n    inf = 10 ** 18\n    dist = [inf] * n\n    dist[0] = 0\n    for step in range(n):\n        updated = False\n        for u, v, w in edges:\n            if dist[u - 1] == inf:\n                continue\n            nd = dist[u - 1] + w\n            if nd < dist[v - 1]:\n                dist[v - 1] = nd\n                updated = True\n                if step == n - 1:\n                    print('Yes')\n                    return\n        if not updated:\n            break\n    print('No')\n\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
