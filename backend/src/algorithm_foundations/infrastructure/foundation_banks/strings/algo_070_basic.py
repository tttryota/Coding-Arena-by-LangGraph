from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('foundation')

UNIT_BANK = unit_bank(
    unit_id='algo-070-basic',
    title='KMP法 の基本',
    unit_kind='foundation',
    target_skill='KMP法 の基本',
    concept_overview='KMP 法では、文字列の自己一致を表す prefix function を先に作り、その情報を検索時に再利用します。まずは各位置の LPS 配列を作る基本を学びます。',
    problem_bank=[
        problem(
            problem_id='algo-070-basic-p1',
            title='KMP法 の基本 / 文字列 T の LPS 配列を求める',
            problem_statement='文字列 T が与えられる。各位置 i について、T[1..i] の接頭辞でもあり接尾辞でもある最長の真部分文字列の長さを求めよ。これを LPS 配列として出力せよ。',
            input_format='1 行目に T。',
            output_format='LPS 配列を空白区切りで出力する。',
            constraints='1 <= |T| <= 2 * 10^5',
            examples=[{'input': 'ababa', 'output': '0 0 1 2 3'}],
            canonical_reference_solution="def build_lps(pattern: str) -> list[int]:\n    lps = [0] * len(pattern)\n    length = 0\n    i = 1\n    while i < len(pattern):\n        if pattern[i] == pattern[length]:\n            length += 1\n            lps[i] = length\n            i += 1\n        elif length:\n            length = lps[length - 1]\n        else:\n            i += 1\n    return lps\n\n\ndef solve() -> None:\n    t = input().strip()\n    print(*build_lps(t))\n\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
