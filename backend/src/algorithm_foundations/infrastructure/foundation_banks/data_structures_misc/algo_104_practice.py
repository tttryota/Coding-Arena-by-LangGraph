from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('foundation')

UNIT_BANK = unit_bank(
    unit_id='algo-104-practice',
    title='単調スタック を素直に実装する',
    unit_kind='foundation',
    target_skill='単調スタック を素直に実装する',
    concept_overview='単調スタックは、左側の候補を参照するだけでなく、右から現れた値で「今まで未確定だった答え」を確定させる使い方もできます。ここでは pop された要素に対して答えを書く流れを練習します。',
    problem_bank=[
        problem(
            problem_id='algo-104-practice-p1',
            title='単調スタック を素直に実装する / i より右で A_j < A_i を満たす最も近い位置 j を求める',
            problem_statement='長さ N の整数列 A が与えられる。各 i について、i より右で `A_j < A_i` を満たす最も近い位置 j を求め、存在しなければ -1 を出力せよ。',
            input_format='1 行目に N。\n2 行目に A1..AN。',
            output_format='N 個の答えを空白区切りで出力する。',
            constraints='1 <= N <= 2 * 10^5',
            examples=[{'input': '6\n5 3 3 6 2 4', 'output': '2 5 5 5 -1 -1'}],
            canonical_reference_solution="def solve() -> None:\n    input()\n    a = list(map(int, input().split()))\n    stack = []\n    ans = [-1] * len(a)\n    for i, value in enumerate(a, start=1):\n        while stack and stack[-1][0] > value:\n            _, idx = stack.pop()\n            ans[idx - 1] = i\n        stack.append((value, i))\n    print(*ans)\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
