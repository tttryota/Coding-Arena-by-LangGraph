from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('foundation')

UNIT_BANK = unit_bank(
    unit_id='algo-104-basic',
    title='単調スタック の基本',
    unit_kind='foundation',
    target_skill='単調スタック の基本',
    concept_overview='単調スタックは、条件を壊す候補を後ろから捨てて「まだ使える候補」だけを残す知識です。まずは最も基本の形として、左から 1 回見るだけで直前の小さい要素を取り出す流れを押さえます。',
    problem_bank=[
        problem(
            problem_id='algo-104-basic-p1',
            title='単調スタック の基本 / i より左で A_j < A_i を満たす最も近い位置 j を求め',
            problem_statement='長さ N の整数列 A が与えられる。各 i について、i より左で `A_j < A_i` を満たす最も近い位置 j を求め、 存在しなければ -1 を出力せよ。',
            input_format='1 行目に N。\n2 行目に A1..AN。',
            output_format='N 個の答えを空白区切りで出力する。',
            constraints='1 <= N <= 2 * 10^5',
            examples=[{'input': '6\n5 3 3 6 2 4', 'output': '-1 -1 -1 3 -1 5'}],
            canonical_reference_solution="def solve() -> None:\n    input()\n    a = list(map(int, input().split()))\n    stack = []\n    ans = []\n    for i, value in enumerate(a, start=1):\n        while stack and stack[-1][0] >= value:\n            stack.pop()\n        ans.append(stack[-1][1] if stack else -1)\n        stack.append((value, i))\n    print(*ans)\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
