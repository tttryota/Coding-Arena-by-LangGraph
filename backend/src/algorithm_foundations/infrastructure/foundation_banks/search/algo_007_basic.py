from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('foundation')

UNIT_BANK = unit_bank(
    unit_id='algo-007-basic',
    title='順列全探索 の基本',
    unit_kind='foundation',
    target_skill='順列全探索 の基本',
    concept_overview='順列全探索は、並べ方をすべて試し、その中から条件を満たすものを見つける解き方です。まずは順番を作り、その順にコストを合計する基本形を押さえます。',
    problem_bank=[
        problem(
            problem_id='algo-007-basic-p1',
            title='順列全探索 の基本 / 頂点 1 から始めて残りを 1 回ずつ訪れる順列の中で、移動コスト合計の最小値を求める',
            problem_statement='N 頂点の完全グラフの重み行列が与えられる。 頂点 1 から始めて残りを 1 回ずつ訪れる順列の中で、移動コスト合計の最小値を求めよ。',
            input_format='1 行目に N。\n続く N 行に重み行列。',
            output_format='最小コストを出力する。',
            constraints='2 <= N <= 8\n0 <= cost[i][j] <= 10^9',
            examples=[{'input': '3\n0 2 5\n2 0 4\n5 4 0', 'output': '6'}],
            canonical_reference_solution="from itertools import permutations\n\ndef solve() -> None:\n    n = int(input())\n    cost = [list(map(int, input().split())) for _ in range(n)]\n    ans = 10 ** 18\n    for order in permutations(range(1, n)):\n        total = 0\n        prev = 0\n        for nxt in order:\n            total += cost[prev][nxt]\n            prev = nxt\n        ans = min(ans, total)\n    print(ans)\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
