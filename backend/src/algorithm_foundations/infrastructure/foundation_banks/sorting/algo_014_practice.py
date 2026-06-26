from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('foundation')

UNIT_BANK = unit_bank(
    unit_id='algo-014-practice',
    title='マージソート を素直に実装する',
    unit_kind='foundation',
    target_skill='マージソート を素直に実装する',
    concept_overview='マージソートでは、左右の半分を再帰的に整列したあと、先頭どうしを比べながら小さい方を順に取ります。再帰とマージを組み合わせる実装の流れを確かめます。',
    problem_bank=[
        problem(
            problem_id='algo-014-practice-p1',
            title='マージソート を素直に実装する / マージソートで昇順に並べ替えて出力せよ',
            problem_statement='長さ N の整数列 A が与えられる。マージソートで昇順に並べ替えて出力せよ。',
            input_format='1 行目に N。\n2 行目に A1..AN。',
            output_format='昇順の列を空白区切りで出力する。',
            constraints='1 <= N <= 2 * 10^5',
            examples=[{'input': '5\n4 1 5 2 3', 'output': '1 2 3 4 5'}],
            canonical_reference_solution="def merge_sort(arr: list[int]) -> list[int]:\n    if len(arr) <= 1:\n        return arr\n    mid = len(arr) // 2\n    left = merge_sort(arr[:mid])\n    right = merge_sort(arr[mid:])\n    out = []\n    i = j = 0\n    while i < len(left) and j < len(right):\n        if left[i] <= right[j]:\n            out.append(left[i]); i += 1\n        else:\n            out.append(right[j]); j += 1\n    out.extend(left[i:])\n    out.extend(right[j:])\n    return out\n\ndef solve() -> None:\n    input()\n    a = list(map(int, input().split()))\n    print(*merge_sort(a))\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
