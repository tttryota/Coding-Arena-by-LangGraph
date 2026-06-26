from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('foundation')

UNIT_BANK = unit_bank(
    unit_id='algo-001-basic',
    title='全探索（ブルートフォース） の基本',
    unit_kind='foundation',
    target_skill='全探索（ブルートフォース） の基本',
    concept_overview='全探索（ブルートフォース）は、候補を順番に全部試し、条件を満たすものを見つける解き方です。まずは連続部分列を二重ループで漏れなく調べる形を身につけます。',
    problem_bank=[
        problem(
            problem_id='algo-001-basic-p1',
            title='全探索（ブルートフォース） の基本 / 総和が S になる連続部分列があるか判定する',
            problem_statement='長さ N の正整数列 A と目標値 S が与えられる。総和がちょうど S になる連続部分列が存在するかを判定せよ。',
            input_format='1 行目に N S。\n2 行目に A1..AN。',
            output_format='条件を満たすなら Yes、そうでなければ No を出力する。',
            constraints='1 <= N <= 2000\n1 <= A_i, S <= 10^9',
            examples=[{'input': '4 11\n2 5 4 9', 'output': 'Yes'}],
            canonical_reference_solution="def solve() -> None:\n    n, s = map(int, input().split())\n    a = list(map(int, input().split()))\n    for left in range(n):\n        total = 0\n        for right in range(left, n):\n            total += a[right]\n            if total == s:\n                print('Yes')\n                return\n    print('No')\n\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
