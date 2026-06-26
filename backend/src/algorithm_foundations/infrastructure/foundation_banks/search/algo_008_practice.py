from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('foundation')

UNIT_BANK = unit_bank(
    unit_id='algo-008-practice',
    title='半分全列挙（meet in the middle） を素直に実装する',
    unit_kind='foundation',
    target_skill='半分全列挙（meet in the middle） を素直に実装する',
    concept_overview='半分全列挙では、前半の和一覧と後半の和一覧を別々に作ってから組み合わせることで、40 個前後の候補でも最良値探索を現実的な計算量で行えます。ここでは S 以下で最大の部分集合和を求めます。',
    problem_bank=[
        problem(
            problem_id='algo-008-practice-p1',
            title='半分全列挙（meet in the middle） を素直に実装する / N が 40 ある部分集合和で、S 以下最大を求める',
            problem_statement='長さ N の非負整数列 A と目標値 S が与えられる。N は最大 40 なので、全 2^N 個の部分集合を直接調べる方法では間に合わない。部分集合の和のうち S 以下で最大の値を求めよ。',
            input_format='1 行目に N S。\n2 行目に A1..AN。',
            output_format='求める最大値を出力する。',
            constraints='30 <= N <= 40\n0 <= A_i <= 10^9\n0 <= S <= 10^18',
            examples=[{'input': '40 20\n8 3 11 7 5 13 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0', 'output': '20'}],
            canonical_reference_solution="from bisect import bisect_right\n\n\ndef subset_sums(values: list[int]) -> list[int]:\n    out = [0]\n    for value in values:\n        out += [cur + value for cur in out]\n    return out\n\n\ndef solve() -> None:\n    n, s = map(int, input().split())\n    a = list(map(int, input().split()))\n    mid = n // 2\n    left_sums = subset_sums(a[:mid])\n    right_sums = sorted(subset_sums(a[mid:]))\n    ans = 0\n    for left in left_sums:\n        if left > s:\n            continue\n        idx = bisect_right(right_sums, s - left) - 1\n        if idx >= 0:\n            ans = max(ans, left + right_sums[idx])\n    print(ans)\n\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
