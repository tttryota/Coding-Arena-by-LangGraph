from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('integration')

UNIT_BANK = unit_bank(
    unit_id='algo-007-integration',
    title='順列全探索 の総合演習',
    unit_kind='integration',
    target_skill='順列全探索 の総合演習',
    concept_overview='順列全探索では、順路コストを計算するだけでなく、「この順番で通ってよいか」という条件も一緒に判定できます。ここでは訪問順の先後制約を満たす巡回順路の最小コストを求めます。',
    problem_bank=[
        problem(
            problem_id='algo-007-integration-p1',
            title='順列全探索 の総合演習 / 先後制約を満たす巡回順路の最小コストを求める',
            problem_statement='N 頂点の完全グラフの重み行列と Q 個の先後制約 `(u, v)` が与えられる。頂点 1 から出発し、残りの頂点を 1 回ずつ訪れて最後に頂点 1 に戻る順路のうち、各制約で「u を v より先に訪れる」を満たすものの最小コストを求めよ。存在しなければ -1 を出力せよ。',
            input_format='1 行目に N Q。\n続く N 行に重み行列。\n続く Q 行に u v。',
            output_format='最小コスト、存在しなければ -1 を出力する。',
            constraints='2 <= N <= 8\n0 <= Q <= N * N\n0 <= cost[i][j] <= 10^9',
            examples=[{'input': '4 1\n0 2 1 9\n1 0 2 9\n9 9 0 1\n2 1 9 0\n2 3', 'output': '7'}],
            canonical_reference_solution="from itertools import permutations\n\ndef solve() -> None:\n    n, q = map(int, input().split())\n    cost = [list(map(int, input().split())) for _ in range(n)]\n    constraints = [tuple(map(int, input().split())) for _ in range(q)]\n    ans = 10 ** 18\n    for order in permutations(range(1, n)):\n        position = {1: 0}\n        for idx, vertex in enumerate(order, start=1):\n            position[vertex + 1] = idx\n        ok = True\n        for u, v in constraints:\n            if position[u] >= position[v]:\n                ok = False\n                break\n        if not ok:\n            continue\n        total = 0\n        prev = 0\n        for nxt in order:\n            total += cost[prev][nxt]\n            prev = nxt\n        total += cost[prev][0]\n        if total < ans:\n            ans = total\n    print(-1 if ans == 10 ** 18 else ans)\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
