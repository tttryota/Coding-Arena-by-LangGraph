from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('foundation')

UNIT_BANK = unit_bank(
    unit_id='algo-015-practice',
    title='クイックソート を素直に実装する',
    unit_kind='foundation',
    target_skill='クイックソート を素直に実装する',
    concept_overview='クイックソートでは、pivot を 1 つ決めて配列を二分し、それぞれを再帰的に処理します。partition での境界更新と再帰呼び出しの実装の流れを確かめます。',
    problem_bank=[
        problem(
            problem_id='algo-015-practice-p1',
            title='クイックソート を素直に実装する / クイックソートで昇順に並べ替えて出力せよ',
            problem_statement='長さ N の整数列 A が与えられる。クイックソートで昇順に並べ替えて出力せよ。',
            input_format='1 行目に N。\n2 行目に A1..AN。',
            output_format='昇順の列を空白区切りで出力する。',
            constraints='1 <= N <= 2 * 10^5',
            examples=[{'input': '5\n4 1 5 2 3', 'output': '1 2 3 4 5'}],
            canonical_reference_solution="def quick_sort(arr: list[int]) -> list[int]:\n    if len(arr) <= 1:\n        return arr\n    pivot = arr[len(arr) // 2]\n    left = [x for x in arr if x < pivot]\n    mid = [x for x in arr if x == pivot]\n    right = [x for x in arr if x > pivot]\n    return quick_sort(left) + mid + quick_sort(right)\n\ndef solve() -> None:\n    input()\n    a = list(map(int, input().split()))\n    print(*quick_sort(a))\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
