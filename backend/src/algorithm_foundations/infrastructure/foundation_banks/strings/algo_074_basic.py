from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('foundation')

UNIT_BANK = unit_bank(
    unit_id='algo-074-basic',
    title='Manacher法（最長回文） の基本',
    unit_kind='foundation',
    target_skill='Manacher法（最長回文） の基本',
    concept_overview='Manacher法（最長回文）は、各位置を中心とする回文半径を前の情報から引き継ぎ、全体を線形時間で調べる知識です。まずは最長回文部分文字列の長さを求める基本を学びます。',
    problem_bank=[
        problem(
            problem_id='algo-074-basic-p1',
            title='Manacher法（最長回文） の基本 / 回文部分文字列の最長長さを求める',
            problem_statement='文字列 S が与えられる。回文部分文字列の最長長さを求めよ。',
            input_format='1 行目に S。',
            output_format='最長長さを出力する。',
            constraints='1 <= |S| <= 2 * 10^5',
            examples=[{'input': 'abacaba', 'output': '7'}],
            canonical_reference_solution="def solve() -> None:\n    s = input().strip()\n    t = '^#' + '#'.join(s) + '#$'\n    radius = [0] * len(t)\n    center = right = 0\n    ans = 0\n    for i in range(1, len(t) - 1):\n        mirror = 2 * center - i\n        if i < right:\n            radius[i] = min(right - i, radius[mirror])\n        while t[i + radius[i] + 1] == t[i - radius[i] - 1]:\n            radius[i] += 1\n        if i + radius[i] > right:\n            center = i\n            right = i + radius[i]\n        ans = max(ans, radius[i])\n    print(ans)\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
