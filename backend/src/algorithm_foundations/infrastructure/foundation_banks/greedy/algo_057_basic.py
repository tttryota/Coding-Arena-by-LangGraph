from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('foundation')

UNIT_BANK = unit_bank(
    unit_id='algo-057-basic',
    title='最小コスト巡回（貪欲近似） の基本',
    unit_kind='foundation',
    target_skill='最小コスト巡回（貪欲近似） の基本',
    concept_overview='最小コスト巡回の貪欲近似では、現在地から最も近い未訪問頂点へ進む最近傍法を使います。まずは始点を 1 に固定し、「その場で最も近いものを選ぶ」とどんな巡回になるかを学びます。',
    problem_bank=[
        problem(
            problem_id='algo-057-basic-p1',
            title='最小コスト巡回（貪欲近似） の基本 / 移動距離の合計を求める',
            problem_statement='N 頂点の完全グラフの距離行列 D が与えられる。頂点 1 から出発し、毎回「まだ訪れていない頂点のうち最も距離が短いもの」へ進み、最後に 1 へ戻る最近傍法を行う。移動距離の合計を求めよ。距離が同じなら番号が小さい頂点を選べ。',
            input_format='1 行目に N。\n続く N 行に距離行列 D。',
            output_format='最近傍法で得られる巡回の長さを出力する。',
            constraints='2 <= N <= 400\n0 <= Dij <= 10^9\nDii = 0',
            examples=[{'input': '4\n0 2 9 10\n1 0 6 4\n15 7 0 8\n6 3 12 0', 'output': '33'}],
            canonical_reference_solution="def solve() -> None:\n    n = int(input())\n    d = [list(map(int, input().split())) for _ in range(n)]\n    used = [False] * n\n    cur = 0\n    used[cur] = True\n    total = 0\n    for _ in range(n - 1):\n        nxt = -1\n        best = 10 ** 18\n        for v in range(n):\n            if used[v]:\n                continue\n            if d[cur][v] < best or (d[cur][v] == best and (nxt == -1 or v < nxt)):\n                best = d[cur][v]\n                nxt = v\n        total += best\n        cur = nxt\n        used[cur] = True\n    total += d[cur][0]\n    print(total)\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
