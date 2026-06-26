from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('integration')

UNIT_BANK = unit_bank(
    unit_id='algo-011-integration',
    title='バブルソート の総合演習',
    unit_kind='integration',
    target_skill='バブルソート の総合演習',
    concept_overview='バブルソートでは、1 周ごとに未確定部分の最大値が右端へ沈みます。ここでは「何回の周回で整列が完了するか」を追い、1 回の走査と全体反復のつながりを確認します。',
    problem_bank=[
        problem(
            problem_id='algo-011-integration-p1',
            title='バブルソート の総合演習 / 昇順になるまでに swap が起こる周回数を求める',
            problem_statement='長さ N の整数列 A が与えられる。バブルソートを行い、左から右への 1 周で 1 回以上 swap が起こるかぎり次の周回へ進むものとする。昇順になるまでに、swap が起こった周回数を求めよ。',
            input_format='1 行目に N。\n2 行目に A1..AN。',
            output_format='swap が起こった周回数を出力する。',
            constraints='1 <= N <= 2000',
            examples=[{'input': '5\n4 1 5 2 3', 'output': '2'}],
            canonical_reference_solution="def solve() -> None:\n    n = int(input())\n    a = list(map(int, input().split()))\n    passes = 0\n    for i in range(n):\n        swapped = False\n        for j in range(n - 1 - i):\n            if a[j] > a[j + 1]:\n                a[j], a[j + 1] = a[j + 1], a[j]\n                swapped = True\n        if not swapped:\n            break\n        passes += 1\n    print(passes)\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
