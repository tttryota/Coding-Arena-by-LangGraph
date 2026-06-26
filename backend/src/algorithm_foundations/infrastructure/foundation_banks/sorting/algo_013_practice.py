from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('foundation')

UNIT_BANK = unit_bank(
    unit_id='algo-013-practice',
    title='挿入ソート を素直に実装する',
    unit_kind='foundation',
    target_skill='挿入ソート を素直に実装する',
    concept_overview='挿入ソートでは、現在の値を一時保存し、それより大きい値を右へずらしながら挿入位置を探します。シフトと代入で整列済み部分を更新する実装の流れを確かめます。',
    problem_bank=[
        problem(
            problem_id='algo-013-practice-p1',
            title='挿入ソート を素直に実装する / 挿入ソートで昇順に並べ替えて出力せよ',
            problem_statement='長さ N の整数列 A が与えられる。挿入ソートで昇順に並べ替えて出力せよ。',
            input_format='1 行目に N。\n2 行目に A1..AN。',
            output_format='昇順の列を空白区切りで出力する。',
            constraints='1 <= N <= 2000',
            examples=[{'input': '5\n4 1 5 2 3', 'output': '1 2 3 4 5'}],
            canonical_reference_solution="def solve() -> None:\n    n = int(input())\n    a = list(map(int, input().split()))\n    for i in range(1, n):\n        value = a[i]\n        j = i - 1\n        while j >= 0 and a[j] > value:\n            a[j + 1] = a[j]\n            j -= 1\n        a[j + 1] = value\n    print(*a)\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
