from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('foundation')

UNIT_BANK = unit_bank(
    unit_id='algo-019-basic',
    title='座標圧縮 の基本',
    unit_kind='foundation',
    target_skill='座標圧縮 の基本',
    concept_overview='座標圧縮は、大小関係を保ったまま値を小さい番号に置き換える考え方です。まずは 1 本の数列を圧縮し、元の順番のまま圧縮値へ写す基本形を学びます。',
    problem_bank=[
        problem(
            problem_id='algo-019-basic-p1',
            title='座標圧縮 の基本 / 長さ N の整数列 A を座標圧縮し、各要素の圧縮後の値を求める',
            problem_statement='長さ N の整数列 A を座標圧縮し、各要素の圧縮後の値を出力せよ。',
            input_format='1 行目に N。\n2 行目に A1..AN。',
            output_format='圧縮後の列を空白区切りで出力する。',
            constraints='1 <= N <= 2 * 10^5\n-10^18 <= A_i <= 10^18',
            examples=[{'input': '5\n100 50 1000 50 200', 'output': '1 0 3 0 2'}],
            canonical_reference_solution="def solve() -> None:\n    input()\n    a = list(map(int, input().split()))\n    values = {value: idx for idx, value in enumerate(sorted(set(a)))}\n    print(*[values[value] for value in a])\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
