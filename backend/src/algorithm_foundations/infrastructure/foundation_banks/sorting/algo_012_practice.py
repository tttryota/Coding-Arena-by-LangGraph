from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('foundation')

UNIT_BANK = unit_bank(
    unit_id='algo-012-practice',
    title='選択ソート を素直に実装する',
    unit_kind='foundation',
    target_skill='選択ソート を素直に実装する',
    concept_overview='選択ソートでは、各位置 i に対して i 以降の最小要素を探し、その位置と交換します。最小値探索と 1 回交換を繰り返す実装の流れを確かめます。',
    problem_bank=[
        problem(
            problem_id='algo-012-practice-p1',
            title='選択ソート を素直に実装する / 選択ソートで昇順に並べ替えて出力せよ',
            problem_statement='長さ N の整数列 A が与えられる。選択ソートで昇順に並べ替えて出力せよ。',
            input_format='1 行目に N。\n2 行目に A1..AN。',
            output_format='昇順の列を空白区切りで出力する。',
            constraints='1 <= N <= 2000',
            examples=[{'input': '5\n4 1 5 2 3', 'output': '1 2 3 4 5'}],
            canonical_reference_solution="def solve() -> None:\n    n = int(input())\n    a = list(map(int, input().split()))\n    for i in range(n):\n        best = i\n        for j in range(i + 1, n):\n            if a[j] < a[best]:\n                best = j\n        a[i], a[best] = a[best], a[i]\n    print(*a)\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
