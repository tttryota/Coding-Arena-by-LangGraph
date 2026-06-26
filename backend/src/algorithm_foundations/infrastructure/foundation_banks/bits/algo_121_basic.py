from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('foundation')

UNIT_BANK = unit_bank(
    unit_id='algo-121-basic',
    title='最下位ビット（LSB）の取得 の基本',
    unit_kind='foundation',
    target_skill='最下位ビット（LSB）の取得 の基本',
    concept_overview='最下位ビット（LSB）の取得は、いちばん右に立っている 1 bit だけを取り出す知識です。まずは `X & -X` の形で 1 回だけ最下位の立っている bit を求める基本を学びます。',
    problem_bank=[
        problem(
            problem_id='algo-121-basic-p1',
            title='最下位ビット（LSB）の取得 の基本 / 最下位の立っているビットの値を求める',
            problem_statement='非負整数 X が与えられる。最下位の立っているビットの値を出力せよ。X=0 のときは 0 を出力する。',
            input_format='1 行目に X。',
            output_format='答えを出力する。',
            constraints='0 <= X < 2^60',
            examples=[{'input': '12', 'output': '4'}],
            canonical_reference_solution="def solve() -> None:\n    x = int(input())\n    print(x & -x if x else 0)\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
