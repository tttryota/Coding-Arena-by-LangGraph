from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('foundation')

UNIT_BANK = unit_bank(
    unit_id='algo-078-practice',
    title='回文判定 を素直に実装する',
    unit_kind='foundation',
    target_skill='回文判定 を素直に実装する',
    concept_overview='回文判定では、対象が文字列全体とは限りません。ここでは各接頭辞を順に候補にしながら、どこまでなら左右対称かを調べ、境界を動かす見方を確かめます。',
    problem_bank=[
        problem(
            problem_id='algo-078-practice-p1',
            title='回文判定 を素直に実装する / 最長の回文接頭辞の長さを求める',
            problem_statement='文字列 S が与えられる。S の接頭辞のうち回文であるものの長さの最大値を求めよ。',
            input_format='1 行目に文字列 S。',
            output_format='答えを 1 行で出力する。',
            constraints='1 <= |S| <= 3000',
            examples=[{'input': 'levelup', 'output': '5'}],
            canonical_reference_solution="def is_palindrome(t: str) -> bool:\n    return t == t[::-1]\n\n\ndef solve() -> None:\n    s = input().strip()\n    for length in range(len(s), 0, -1):\n        if is_palindrome(s[:length]):\n            print(length)\n            return\n\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
