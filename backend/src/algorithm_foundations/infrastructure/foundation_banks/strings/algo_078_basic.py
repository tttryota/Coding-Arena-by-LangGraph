from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('foundation')

UNIT_BANK = unit_bank(
    unit_id='algo-078-basic',
    title='回文判定 の基本',
    unit_kind='foundation',
    target_skill='回文判定 の基本',
    concept_overview='回文判定は、文字列を前から読んだ順と後ろから読んだ順が一致するかを調べる知識です。まずは文字列全体を 1 つの対象として見て、回文かどうかを判定する基本を学びます。',
    problem_bank=[
        problem(
            problem_id='algo-078-basic-p1',
            title='回文判定 の基本 / S が回文なら Yes、そうでなければ No を求める',
            problem_statement='文字列 S が与えられる。S が回文なら Yes、そうでなければ No を出力せよ。',
            input_format='1 行目に文字列 S。',
            output_format='Yes / No を出力する。',
            constraints='1 <= |S| <= 2 * 10^5',
            examples=[{'input': 'level', 'output': 'Yes'}],
            canonical_reference_solution="def solve() -> None:\n    s = input().strip()\n    print('Yes' if s == s[::-1] else 'No')\n\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
