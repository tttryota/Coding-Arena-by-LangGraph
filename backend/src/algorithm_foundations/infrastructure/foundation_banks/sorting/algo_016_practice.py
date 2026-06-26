from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('foundation')

UNIT_BANK = unit_bank(
    unit_id='algo-016-practice',
    title='ヒープソート を素直に実装する',
    unit_kind='foundation',
    target_skill='ヒープソート を素直に実装する',
    concept_overview='ヒープソートでは、最大ヒープを作ってから「根と末尾の交換 -> sift-down」を末尾側へ向かって繰り返します。配列内で整列を完了する流れを実装します。',
    problem_bank=[
        problem(
            problem_id='algo-016-practice-p1',
            title='ヒープソート を素直に実装する / 配列全体を in-place で昇順に並べる',
            problem_statement='長さ N の整数列 A が与えられる。ヒープソートで昇順に並べ替えて出力せよ。',
            input_format='1 行目に N。\n2 行目に A1..AN。',
            output_format='昇順の列を空白区切りで出力する。',
            constraints='1 <= N <= 2 * 10^5',
            examples=[{'input': '5\n4 1 5 2 3', 'output': '1 2 3 4 5'}],
            canonical_reference_solution="def sift_down(a: list[int], start: int, end: int) -> None:\n    root = start\n    while True:\n        child = root * 2 + 1\n        if child >= end:\n            return\n        if child + 1 < end and a[child] < a[child + 1]:\n            child += 1\n        if a[root] >= a[child]:\n            return\n        a[root], a[child] = a[child], a[root]\n        root = child\n\n\ndef solve() -> None:\n    n = int(input())\n    a = list(map(int, input().split()))\n    for i in range(n // 2 - 1, -1, -1):\n        sift_down(a, i, n)\n    for end in range(n - 1, 0, -1):\n        a[0], a[end] = a[end], a[0]\n        sift_down(a, 0, end)\n    print(*a)\n\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
