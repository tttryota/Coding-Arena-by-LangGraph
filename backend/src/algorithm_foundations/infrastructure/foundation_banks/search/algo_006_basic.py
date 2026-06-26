from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('foundation')

UNIT_BANK = unit_bank(
    unit_id='algo-006-basic',
    title='bit全探索 の基本',
    unit_kind='foundation',
    target_skill='bit全探索 の基本',
    concept_overview='bit 全探索は、各要素を選ぶ・選ばないをビットで表し、部分集合をすべて試す解き方です。まずは「条件を満たす部分集合があるか」の存在判定から始めます。',
    problem_bank=[
        problem(
            problem_id='algo-006-basic-p1',
            title='bit全探索 の基本 / 部分集合の和が S になるものがあるか判定する',
            problem_statement='長さ N の非負整数列 A と目標値 S が与えられる。bit 全探索を用いて、部分集合の和がちょうど S になるものが存在するか判定せよ。',
            input_format='1 行目に N S。\n2 行目に A1..AN。',
            output_format='Yes / No を出力する。',
            constraints='1 <= N <= 20\n0 <= A_i <= 10^9\n0 <= S <= 10^18',
            examples=[{'input': '4 11\n2 5 9 4', 'output': 'Yes'}],
            canonical_reference_solution="def solve() -> None:\n    n, s = map(int, input().split())\n    a = list(map(int, input().split()))\n    for mask in range(1 << n):\n        total = 0\n        for i in range(n):\n            if mask >> i & 1:\n                total += a[i]\n        if total == s:\n            print('Yes')\n            return\n    print('No')\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
