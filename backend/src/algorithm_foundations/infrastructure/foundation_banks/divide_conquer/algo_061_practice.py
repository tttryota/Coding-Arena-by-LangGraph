from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('foundation')

UNIT_BANK = unit_bank(
    unit_id='algo-061-practice',
    title='マージソートによる分割統治 を素直に実装する',
    unit_kind='foundation',
    target_skill='マージソートによる分割統治 を素直に実装する',
    concept_overview='マージソートによる分割統治は、列を半分ずつに分けてそれぞれを整列し、最後にマージして全体の昇順列を作る知識です。ここでは併合操作を土台として、分割と再帰呼び出しを含むマージソート全体を素直に組み立てます。',
    problem_bank=[
        problem(
            problem_id='algo-061-practice-p1',
            title='マージソートによる分割統治 を素直に実装する / A をマージソートで昇順に並べ替えて出力せよ',
            problem_statement='長さ N の整数列 A が与えられる。A を昇順に並べ替えて出力せよ。',
            input_format='1 行目に N。\n2 行目に A1..AN。',
            output_format='昇順に並べた列を空白区切りで出力する。',
            constraints='1 <= N <= 2 * 10^5, -10^9 <= Ai <= 10^9',
            examples=[{'input': '5\n4 1 5 2 3', 'output': '1 2 3 4 5'}],
            canonical_reference_solution="def merge(left: list[int], right: list[int]) -> list[int]:\n    i = 0\n    j = 0\n    merged = []\n    while i < len(left) and j < len(right):\n        if left[i] <= right[j]:\n            merged.append(left[i])\n            i += 1\n        else:\n            merged.append(right[j])\n            j += 1\n    merged.extend(left[i:])\n    merged.extend(right[j:])\n    return merged\n\n\ndef merge_sort(values: list[int]) -> list[int]:\n    if len(values) <= 1:\n        return values[:]\n    mid = len(values) // 2\n    left = merge_sort(values[:mid])\n    right = merge_sort(values[mid:])\n    return merge(left, right)\n\n\ndef solve() -> None:\n    input()\n    a = list(map(int, input().split()))\n    print(*merge_sort(a))\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
