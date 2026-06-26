from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('foundation')

UNIT_BANK = unit_bank(
    unit_id='algo-011-practice',
    title='バブルソート を素直に実装する',
    unit_kind='foundation',
    target_skill='バブルソート を素直に実装する',
    concept_overview='バブルソートでは、左から右へ隣接比較を行い、1 周ごとに未確定部分の最大値を後ろへ送ります。二重ループで交換を重ねる実装の流れを確かめます。',
    problem_bank=[
        problem(
            problem_id='algo-011-practice-p1',
            title='バブルソート を素直に実装する / バブルソートで昇順に並べ替えて出力せよ',
            problem_statement='長さ N の整数列 A が与えられる。バブルソートで昇順に並べ替えて出力せよ。',
            input_format='1 行目に N。\n2 行目に A1..AN。',
            output_format='昇順の列を空白区切りで出力する。',
            constraints='1 <= N <= 2000',
            examples=[{'input': '5\n4 1 5 2 3', 'output': '1 2 3 4 5'}],
            canonical_reference_solution="def solve() -> None:\n    n = int(input())\n    a = list(map(int, input().split()))\n    for i in range(n):\n        for j in range(n - 1 - i):\n            if a[j] > a[j + 1]:\n                a[j], a[j + 1] = a[j + 1], a[j]\n    print(*a)\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
