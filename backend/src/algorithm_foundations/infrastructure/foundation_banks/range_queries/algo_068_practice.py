from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('foundation')

UNIT_BANK = unit_bank(
    unit_id='algo-068-practice',
    title='マージソートで転倒数 を素直に実装する',
    unit_kind='foundation',
    target_skill='マージソートで転倒数 を素直に実装する',
    concept_overview='左右の列のあいだの転倒数を数えられれば、再帰的に分割した全体の転倒数も求められます。ここでは転倒数と整列結果を同時に作る実装を確認します。',
    problem_bank=[
        problem(
            problem_id='algo-068-practice-p1',
            title='マージソートで転倒数 を素直に実装する / 転倒数と整列後の列を同時に求める',
            problem_statement='長さ N の整数列 A が与えられる。マージソートを用いて転倒数を求め、あわせて整列後の列も出力せよ。',
            input_format='1 行目に N。\n2 行目に A1..AN。',
            output_format='1 行目に転倒数、2 行目に整列後の列を空白区切りで出力する。',
            constraints='1 <= N <= 2 * 10^5\n-10^18 <= A_i <= 10^18',
            examples=[{'input': '4\n3 1 4 2', 'output': '3\n1 2 3 4'}],
            canonical_reference_solution="def merge_count(arr: list[int]) -> tuple[list[int], int]:\n    if len(arr) <= 1:\n        return arr, 0\n    mid = len(arr) // 2\n    left, lc = merge_count(arr[:mid])\n    right, rc = merge_count(arr[mid:])\n    merged = []\n    i = j = 0\n    inv = lc + rc\n    while i < len(left) and j < len(right):\n        if left[i] <= right[j]:\n            merged.append(left[i])\n            i += 1\n        else:\n            merged.append(right[j])\n            j += 1\n            inv += len(left) - i\n    merged.extend(left[i:])\n    merged.extend(right[j:])\n    return merged, inv\n\n\ndef solve() -> None:\n    input()\n    a = list(map(int, input().split()))\n    sorted_arr, inv = merge_count(a)\n    print(inv)\n    print(*sorted_arr)\n\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
