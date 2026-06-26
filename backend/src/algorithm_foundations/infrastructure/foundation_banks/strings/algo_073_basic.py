from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('foundation')

UNIT_BANK = unit_bank(
    unit_id='algo-073-basic',
    title='Suffix Array の基本',
    unit_kind='foundation',
    target_skill='Suffix Array の基本',
    concept_overview='Suffix Array や LCP は、文字列の suffix を順序づけて管理し、部分文字列の比較や共通部分を扱いやすくする知識です。並べ替えた構造で文字列を見る基本を学びます。',
    problem_bank=[
        problem(
            problem_id='algo-073-basic-p1',
            title='Suffix Array の基本 / Suffix Array を構成し、各接尾辞の開始位置を 1-indexed で出力せよ',
            problem_statement='文字列 S が与えられる。Suffix Array を構成し、各接尾辞の開始位置を 1-indexed で出力せよ。',
            input_format='1 行目に S。',
            output_format='開始位置を空白区切りで出力する。',
            constraints='1 <= |S| <= 2000',
            examples=[{'input': 'banana', 'output': '6 4 2 1 5 3'}],
            canonical_reference_solution="def solve() -> None:\n    s = input().strip()\n    order = sorted(range(len(s)), key=lambda i: s[i:])\n    print(*[i + 1 for i in order])\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
