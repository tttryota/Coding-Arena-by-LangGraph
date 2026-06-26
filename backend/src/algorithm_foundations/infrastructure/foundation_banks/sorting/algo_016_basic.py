from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('foundation')

UNIT_BANK = unit_bank(
    unit_id='algo-016-basic',
    title='ヒープソート の基本',
    unit_kind='foundation',
    target_skill='ヒープソート の基本',
    concept_overview='ヒープソートは、まず配列をヒープにし、根と末尾を交換しながら整列済み部分を後ろへ広げる解き方です。ここでは 1 回ぶんの操作で配列がどう変わるかを確かめます。',
    problem_bank=[
        problem(
            problem_id='algo-016-basic-p1',
            title='ヒープソート の基本 / 最大ヒープを作って 1 回だけ取り出す',
            problem_statement='長さ N の整数列 A が与えられる。配列 A を bottom-up で最大ヒープにしたあと、根と末尾を交換し、ヒープサイズを 1 減らして根から sift-down を 1 回行え。操作後の配列全体を出力せよ。',
            input_format='1 行目に N。\n2 行目に A1..AN。',
            output_format='1 回めの交換と sift-down を終えたあとの配列を空白区切りで出力する。',
            constraints='2 <= N <= 2 * 10^5',
            examples=[{'input': '6\n4 1 6 3 5 2', 'output': '5 3 4 2 1 6'}],
            canonical_reference_solution="def sift_down(a: list[int], start: int, end: int) -> None:\n    root = start\n    while True:\n        child = root * 2 + 1\n        if child >= end:\n            return\n        if child + 1 < end and a[child] < a[child + 1]:\n            child += 1\n        if a[root] >= a[child]:\n            return\n        a[root], a[child] = a[child], a[root]\n        root = child\n\n\ndef solve() -> None:\n    n = int(input())\n    a = list(map(int, input().split()))\n    for i in range(n // 2 - 1, -1, -1):\n        sift_down(a, i, n)\n    a[0], a[-1] = a[-1], a[0]\n    sift_down(a, 0, n - 1)\n    print(*a)\n\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
