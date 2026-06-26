from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('integration')

UNIT_BANK = unit_bank(
    unit_id='algo-014-integration',
    title='マージソート の総合演習',
    unit_kind='integration',
    target_skill='マージソート の総合演習',
    concept_overview='マージソートでは、整列だけでなく安定性も保てます。同じ key を持つ要素の相対順を保ったまま並べる流れを確認します。',
    problem_bank=[
        problem(
            problem_id='algo-014-integration-p1',
            title='マージソート の総合演習 / key で安定整列したあとの id 順を出力する',
            problem_statement='長さ N の `(key, id)` 列が与えられる。`key` の昇順で安定に整列したあと、`id` を順に出力せよ。',
            input_format='1 行目に N。\n続く N 行に key id。',
            output_format='整列後の id を空白区切りで出力する。',
            constraints='1 <= N <= 2 * 10^5',
            examples=[{'input': '5\n4 10\n1 20\n4 30\n2 40\n4 50', 'output': '20 40 10 30 50'}],
            canonical_reference_solution="def merge_sort(arr: list[tuple[int, int]]) -> list[tuple[int, int]]:\n    if len(arr) <= 1:\n        return arr\n    mid = len(arr) // 2\n    left = merge_sort(arr[:mid])\n    right = merge_sort(arr[mid:])\n    out = []\n    i = j = 0\n    while i < len(left) and j < len(right):\n        if left[i][0] <= right[j][0]:\n            out.append(left[i])\n            i += 1\n        else:\n            out.append(right[j])\n            j += 1\n    out.extend(left[i:])\n    out.extend(right[j:])\n    return out\n\ndef solve() -> None:\n    n = int(input())\n    a = [tuple(map(int, input().split())) for _ in range(n)]\n    print(*[v for _, v in merge_sort(a)])\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
