from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('integration')

UNIT_BANK = unit_bank(
    unit_id='algo-016-integration',
    title='ヒープソート の総合演習',
    unit_kind='integration',
    target_skill='ヒープソート の総合演習',
    concept_overview='ヒープソートは、整数だけでなく「比較できる組」を並べ替えるときにも同じ流れで使えます。ここでは score と id の組をヒープソートで整列して、並び順を答えます。',
    problem_bank=[
        problem(
            problem_id='algo-016-integration-p1',
            title='ヒープソート の総合演習 / 点数順に並んだ選手番号を出力する',
            problem_statement='N 人の選手の点数 A1..AN が与えられる。選手 i を組 (Ai, i) とみなし、(点数の昇順, 同点なら番号の昇順) にヒープソートで並べたときの選手番号列を出力せよ。',
            input_format='1 行目に N。\n2 行目に A1..AN。',
            output_format='並べ替え後の選手番号を空白区切りで出力する。',
            constraints='1 <= N <= 2 * 10^5',
            examples=[{'input': '5\n40 10 40 20 10', 'output': '2 5 4 1 3'}],
            canonical_reference_solution="def sift_down(a: list[tuple[int, int]], start: int, end: int) -> None:\n    root = start\n    while True:\n        child = root * 2 + 1\n        if child >= end:\n            return\n        if child + 1 < end and a[child] < a[child + 1]:\n            child += 1\n        if a[root] >= a[child]:\n            return\n        a[root], a[child] = a[child], a[root]\n        root = child\n\n\ndef solve() -> None:\n    n = int(input())\n    scores = list(map(int, input().split()))\n    a = [(score, idx + 1) for idx, score in enumerate(scores)]\n    for i in range(n // 2 - 1, -1, -1):\n        sift_down(a, i, n)\n    for end in range(n - 1, 0, -1):\n        a[0], a[end] = a[end], a[0]\n        sift_down(a, 0, end)\n    print(*(idx for _, idx in a))\n\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
