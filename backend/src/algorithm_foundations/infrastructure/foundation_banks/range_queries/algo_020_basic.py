from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('foundation')

UNIT_BANK = unit_bank(
    unit_id='algo-020-basic',
    title='転倒数の計算 の基本',
    unit_kind='foundation',
    target_skill='転倒数の計算 の基本',
    concept_overview='転倒数は、順序が逆になっている組の個数を数える知識です。まずは列全体に含まれる転倒数の合計を求める基本形を押さえます。',
    problem_bank=[
        problem(
            problem_id='algo-020-basic-p1',
            title='転倒数の計算 の基本 / 転倒数を求める',
            problem_statement='長さ N の整数列 A が与えられる。転倒数を求めよ。',
            input_format='1 行目に N。\n2 行目に A1..AN。',
            output_format='転倒数を出力する。',
            constraints='1 <= N <= 2 * 10^5\n-10^18 <= A_i <= 10^18',
            examples=[{'input': '4\n3 1 4 2', 'output': '3'}],
            canonical_reference_solution="def merge_count(arr: list[int]) -> tuple[list[int], int]:\n    if len(arr) <= 1:\n        return arr, 0\n    mid = len(arr) // 2\n    left, lc = merge_count(arr[:mid])\n    right, rc = merge_count(arr[mid:])\n    merged = []\n    i = j = 0\n    inv = lc + rc\n    while i < len(left) and j < len(right):\n        if left[i] <= right[j]:\n            merged.append(left[i]); i += 1\n        else:\n            merged.append(right[j]); j += 1\n            inv += len(left) - i\n    merged.extend(left[i:])\n    merged.extend(right[j:])\n    return merged, inv\n\ndef solve() -> None:\n    input()\n    a = list(map(int, input().split()))\n    print(merge_count(a)[1])\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
