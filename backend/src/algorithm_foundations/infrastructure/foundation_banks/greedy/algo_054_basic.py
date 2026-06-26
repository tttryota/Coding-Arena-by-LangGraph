from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('foundation')

UNIT_BANK = unit_bank(
    unit_id='algo-054-basic',
    title='分数ナップサック問題 の基本',
    unit_kind='foundation',
    target_skill='分数ナップサック問題 の基本',
    concept_overview='分数ナップサック問題は、価値密度の高い品物から先に取ると最適になる知識です。品物を分割できる条件の下で、価値/重さの比で貪欲に選ぶ基本を学びます。',
    problem_bank=[
        problem(
            problem_id='algo-054-basic-p1',
            title='分数ナップサック問題 の基本 / 品物は分割してよいとき、得られる価値の最大値を求める',
            problem_statement='N 個の品物があり、i 番目の価値は Vi、重さは Wi である。重さの合計が C 以下になるように品物を選ぶ。品物は分割してよいとき、得られる価値の最大値を求めよ。',
            input_format='1 行目に N C。\n続く N 行に Vi Wi。',
            output_format='最大価値を出力する。',
            constraints='1 <= N <= 2 * 10^5\n1 <= Vi, Wi <= 10^9',
            examples=[{'input': '3 6\n10 2\n9 3\n8 4', 'output': '21.0'}],
            canonical_reference_solution="def solve() -> None:\n    import sys\n    input = sys.stdin.readline\n    n, capacity = map(int, input().split())\n    items = [tuple(map(int, input().split())) for _ in range(n)]\n    items.sort(key=lambda item: item[0] / item[1], reverse=True)\n    total = 0.0\n    for value, weight in items:\n        if capacity == 0:\n            break\n        take = min(capacity, weight)\n        total += value * take / weight\n        capacity -= take\n    print(total)\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
