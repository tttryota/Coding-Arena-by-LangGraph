from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('foundation')

UNIT_BANK = unit_bank(
    unit_id='algo-075-basic',
    title='ランレングス圧縮 の基本',
    unit_kind='foundation',
    target_skill='ランレングス圧縮 の基本',
    concept_overview='ランレングス圧縮は、同じ文字が連続する区間を 1 つの文字と個数へまとめる知識です。まずは左から見て連続区間の長さを数え、圧縮結果へ直す基本を学びます。',
    problem_bank=[
        problem(
            problem_id='algo-075-basic-p1',
            title='ランレングス圧縮 の基本 / 文字列 S をランレングス圧縮し、文字と個数を交互に出力せよ',
            problem_statement='文字列 S をランレングス圧縮し、文字と個数を交互に出力せよ。',
            input_format='1 行目に S。',
            output_format='圧縮結果を 1 行で出力する。',
            constraints='1 <= |S| <= 2 * 10^5',
            examples=[{'input': 'aaabbc', 'output': 'a3b2c1'}],
            canonical_reference_solution="def solve() -> None:\n    s = input().strip()\n    out = []\n    i = 0\n    while i < len(s):\n        j = i\n        while j < len(s) and s[j] == s[i]:\n            j += 1\n        out.append(f'{s[i]}{j - i}')\n        i = j\n    print(''.join(out))\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
