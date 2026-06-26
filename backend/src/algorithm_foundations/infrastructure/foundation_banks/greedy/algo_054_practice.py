from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('foundation')

UNIT_BANK = unit_bank(
    unit_id='algo-054-practice',
    title='分数ナップサック問題 を素直に実装する',
    unit_kind='foundation',
    target_skill='分数ナップサック問題 を素直に実装する',
    concept_overview='価値密度の高い品物から取る考え方は、重さ制約で価値を最大化するだけでなく、目標価値を満たすための最小重量を求めるときにも使えます。ここでは同じ密度順を逆向きの目的へ使います。',
    problem_bank=[
        problem(
            problem_id='algo-054-practice-p1',
            title='分数ナップサック問題 を素直に実装する / 価値 V 以上を得るための最小重量を求める',
            problem_statement='N 個の品物があり、i 番目の価値は V_i、重さは W_i である。品物は分割してよい。得られる価値の合計が X 以上になるように品物を選ぶとき、必要な重さの合計の最小値を求めよ。不可能なら -1 を出力せよ。',
            input_format='1 行目に N X。\n続く N 行に V_i W_i。',
            output_format='必要な重さの最小値を出力する。不可能なら -1 を出力する。絶対誤差または相対誤差 10^-6 まで許す。',
            constraints='1 <= N <= 2 * 10^5\n0 <= X <= 10^18\n1 <= V_i, W_i <= 10^9',
            examples=[{'input': '3 16\n10 2\n9 3\n8 4', 'output': '4.0'}],
            canonical_reference_solution="def solve() -> None:\n    import sys\n    input = sys.stdin.readline\n    n, target = map(int, input().split())\n    items = [tuple(map(int, input().split())) for _ in range(n)]\n    items.sort(key=lambda item: item[0] / item[1], reverse=True)\n    weight_sum = 0.0\n    for value, weight in items:\n        if target <= 0:\n            break\n        take_value = min(target, value)\n        weight_sum += weight * take_value / value\n        target -= take_value\n    print(weight_sum if target <= 0 else -1)\n\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
