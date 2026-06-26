from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('foundation')

UNIT_BANK = unit_bank(
    unit_id='algo-007-practice',
    title='順列全探索 を素直に実装する',
    unit_kind='foundation',
    target_skill='順列全探索 を素直に実装する',
    concept_overview='順列全探索では、同じ順番生成でも評価の仕方を少し変えるだけで別の問題を扱えます。ここでは最後に始点へ戻るコストまで含めます。',
    problem_bank=[
        problem(
            problem_id='algo-007-practice-p1',
            title='順列全探索 を素直に実装する / 頂点 1 に戻る巡回順路の最小コストを求める',
            problem_statement='N 頂点の完全グラフの重み行列が与えられる。頂点 1 から出発し、残りの頂点を 1 回ずつ訪れて最後に頂点 1 に戻る順路のうち、移動コスト合計の最小値を求めよ。',
            input_format='1 行目に N。\n続く N 行に重み行列。',
            output_format='最小コストを出力する。',
            constraints='2 <= N <= 8\n0 <= cost[i][j] <= 10^9',
            examples=[{'input': '3\n0 2 5\n2 0 4\n5 4 0', 'output': '11'}],
            canonical_reference_solution="from itertools import permutations\n\ndef solve() -> None:\n    n = int(input())\n    cost = [list(map(int, input().split())) for _ in range(n)]\n    ans = 10 ** 18\n    for order in permutations(range(1, n)):\n        total = 0\n        prev = 0\n        for nxt in order:\n            total += cost[prev][nxt]\n            prev = nxt\n        total += cost[prev][0]\n        ans = min(ans, total)\n    print(ans)\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
