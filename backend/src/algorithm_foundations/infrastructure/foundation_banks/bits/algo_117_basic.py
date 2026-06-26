from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('foundation')

UNIT_BANK = unit_bank(
    unit_id='algo-117-basic',
    title='ポップカウント（立っているビット数） の基本',
    unit_kind='foundation',
    target_skill='ポップカウント（立っているビット数） の基本',
    concept_overview='ポップカウントは、2 進表現の中で 1 が立っている桁数を数える知識です。まずは 1 つの整数に対して、その整数が持つフラグ数を直接求めます。',
    problem_bank=[
        problem(
            problem_id='algo-117-basic-p1',
            title='ポップカウント（立っているビット数） の基本 / 2 進表現で立っている bit 数を求める',
            problem_statement='1 つの非負整数 X が与えられる。2 進表現で立っている bit 数を求めよ。',
            input_format='1 行目に X。',
            output_format='bit 数を出力する。',
            constraints='0 <= X < 2^60',
            examples=[{'input': '13', 'output': '3'}],
            canonical_reference_solution="def solve() -> None:\n    x = int(input())\n    print(x.bit_count())\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
