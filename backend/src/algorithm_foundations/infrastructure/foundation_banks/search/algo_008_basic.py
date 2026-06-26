from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('foundation')

UNIT_BANK = unit_bank(
    unit_id='algo-008-basic',
    title='半分全列挙（meet in the middle） の基本',
    unit_kind='foundation',
    target_skill='半分全列挙（meet in the middle） の基本',
    concept_overview='半分全列挙は、候補が 40 個前後あるときに 2^N 通りをそのまま試さず、前半 2^(N/2) 通りと後半 2^(N/2) 通りへ分けて組み合わせる考え方です。まずは「和がちょうど S になるか」の存在判定で基本形を押さえます。',
    problem_bank=[
        problem(
            problem_id='algo-008-basic-p1',
            title='半分全列挙（meet in the middle） の基本 / N が 40 ある部分集合和で、ちょうど S を作れるか判定する',
            problem_statement='長さ N の非負整数列 A と目標値 S が与えられる。N は最大 40 なので、全 2^N 個の部分集合をそのまま調べる方法では間に合わない。部分集合の和がちょうど S になるものが存在するか判定せよ。',
            input_format='1 行目に N S。\n2 行目に A1..AN。',
            output_format='Yes / No を出力する。',
            constraints='30 <= N <= 40\n0 <= A_i <= 10^9\n0 <= S <= 10^18',
            examples=[{'input': '40 24\n8 3 11 7 5 13 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0', 'output': 'Yes'}],
            canonical_reference_solution="from bisect import bisect_left\n\n\ndef subset_sums(values: list[int]) -> list[int]:\n    out = [0]\n    for value in values:\n        out += [cur + value for cur in out]\n    return out\n\n\ndef solve() -> None:\n    n, s = map(int, input().split())\n    a = list(map(int, input().split()))\n    mid = n // 2\n    left_sums = subset_sums(a[:mid])\n    right_sums = sorted(subset_sums(a[mid:]))\n    for left in left_sums:\n        need = s - left\n        idx = bisect_left(right_sums, need)\n        if idx < len(right_sums) and right_sums[idx] == need:\n            print('Yes')\n            return\n    print('No')\n\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
