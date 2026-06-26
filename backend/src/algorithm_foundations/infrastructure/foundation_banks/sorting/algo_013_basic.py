from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('foundation')

UNIT_BANK = unit_bank(
    unit_id='algo-013-basic',
    title='挿入ソート の基本',
    unit_kind='foundation',
    target_skill='挿入ソート の基本',
    concept_overview='挿入ソートは、新しい要素を左側の整列済み部分へ差し込み、必要なら右へずらして場所を作る知識です。まずは 1 要素ずつ整列済み区間を広げる基本を学びます。',
    problem_bank=[
        problem(
            problem_id='algo-013-basic-p1',
            title='挿入ソート の基本 / 最後の 1 要素を整列済み prefix に差し込む',
            problem_statement='長さ N の整数列 A が与えられる。`A1..A{N-1}` はすでに昇順に並んでいる。最後の要素 `A_N` を適切な位置へ差し込み、全体を昇順にした列を出力せよ。',
            input_format='1 行目に N。\n2 行目に A1..AN。',
            output_format='差し込み後の列を空白区切りで出力する。',
            constraints='1 <= N <= 2000',
            examples=[{'input': '5\n1 3 4 5 2', 'output': '1 2 3 4 5'}],
            canonical_reference_solution="def solve() -> None:\n    n = int(input())\n    a = list(map(int, input().split()))\n    value = a[-1]\n    j = n - 2\n    while j >= 0 and a[j] > value:\n        a[j + 1] = a[j]\n        j -= 1\n    a[j + 1] = value\n    print(*a)\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
