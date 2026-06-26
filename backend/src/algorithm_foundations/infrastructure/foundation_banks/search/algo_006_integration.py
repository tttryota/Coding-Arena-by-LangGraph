from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('integration')

UNIT_BANK = unit_bank(
    unit_id='algo-006-integration',
    title='bit全探索 の総合演習',
    unit_kind='integration',
    target_skill='bit全探索 の総合演習',
    concept_overview='bit 全探索では、部分集合を 1 つ選ぶだけでなく、「選んだ側と選ばなかった側」を 2 グループとして比較することもできます。ここでは二分割したときの和の差を最小化します。',
    problem_bank=[
        problem(
            problem_id='algo-006-integration-p1',
            title='bit全探索 の総合演習 / 2 グループに分けた和の差を最小化する',
            problem_statement='長さ N の非負整数列 A が与えられる。要素を 2 グループに分けるとき、2 グループの総和の差の絶対値の最小値を求めよ。',
            input_format='1 行目に N。\n2 行目に A1..AN。',
            output_format='差の絶対値の最小値を出力する。',
            constraints='1 <= N <= 20\n0 <= A_i <= 10^9',
            examples=[{'input': '4\n1 6 11 5', 'output': '1'}],
            canonical_reference_solution="def solve() -> None:\n    n = int(input())\n    a = list(map(int, input().split()))\n    total_sum = sum(a)\n    ans = 10 ** 18\n    for mask in range(1 << n):\n        group_sum = 0\n        for i in range(n):\n            if mask >> i & 1:\n                group_sum += a[i]\n        diff = abs(total_sum - 2 * group_sum)\n        if diff < ans:\n            ans = diff\n    print(ans)\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
