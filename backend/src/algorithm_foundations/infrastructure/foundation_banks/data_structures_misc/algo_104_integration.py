from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('integration')

UNIT_BANK = unit_bank(
    unit_id='algo-104-integration',
    title='単調スタック の総合演習',
    unit_kind='integration',
    target_skill='単調スタック の総合演習',
    concept_overview='単調スタックで左の直前小要素と右の次小要素が分かると、その値より小さい要素に挟まれた最大区間を復元できます。ここでは basic/practice で見た 2 つの境界計算をそのまま組み合わせます。',
    problem_bank=[
        problem(
            problem_id='algo-104-integration-p1',
            title='単調スタック の総合演習 / A_i が最小値になれる最大連続区間の長さを各 i について求める',
            problem_statement='長さ N の整数列 A が与えられる。各 i について、i を含む連続部分列のうち `A_i` がその区間の最小値の 1 つであるようなものの長さの最大値を求めよ。',
            input_format='1 行目に N。\n2 行目に A1..AN。',
            output_format='N 個の答えを空白区切りで出力する。',
            constraints='1 <= N <= 2 * 10^5',
            examples=[{'input': '7\n2 4 3 3 5 1 2', 'output': '5 1 4 4 1 7 1'}],
            canonical_reference_solution="def solve() -> None:\n    input()\n    a = list(map(int, input().split()))\n    n = len(a)\n\n    left = [-1] * n\n    stack = []\n    for i, value in enumerate(a):\n        while stack and a[stack[-1]] >= value:\n            stack.pop()\n        left[i] = stack[-1] if stack else -1\n        stack.append(i)\n\n    right = [n] * n\n    stack = []\n    for i, value in enumerate(a):\n        while stack and a[stack[-1]] > value:\n            idx = stack.pop()\n            right[idx] = i\n        stack.append(i)\n\n    ans = [right[i] - left[i] - 1 for i in range(n)]\n    print(*ans)\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
