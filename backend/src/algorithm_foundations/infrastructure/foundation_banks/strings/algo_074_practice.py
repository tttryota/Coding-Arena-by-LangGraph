from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('foundation')

UNIT_BANK = unit_bank(
    unit_id='algo-074-practice',
    title='Manacher法（最長回文） を素直に実装する',
    unit_kind='foundation',
    target_skill='Manacher法（最長回文） を素直に実装する',
    concept_overview='Manacher法では、奇数長と偶数長それぞれの中心について回文半径を持つと、最長長さだけでなく回文部分文字列の総数も数えられます。左右対称な中心情報を使い回しながら、各中心が何個の回文を生むか集計する見方を確かめます。',
    problem_bank=[
        problem(
            problem_id='algo-074-practice-p1',
            title='Manacher法（最長回文） を素直に実装する / 回文部分文字列の総数を求める',
            problem_statement='文字列 S が与えられる。S の回文部分文字列の総数を求めよ。同じ文字列でも位置が異なれば別の部分文字列として数える。',
            input_format='1 行目に S。',
            output_format='総数を出力する。',
            constraints='1 <= |S| <= 2 * 10^5',
            examples=[{'input': 'abac', 'output': '5'}],
            canonical_reference_solution="def solve() -> None:\n    s = input().strip()\n    n = len(s)\n\n    odd = [0] * n\n    left = 0\n    right = -1\n    for i in range(n):\n        radius = 1 if i > right else min(odd[left + right - i], right - i + 1)\n        while 0 <= i - radius and i + radius < n and s[i - radius] == s[i + radius]:\n            radius += 1\n        odd[i] = radius\n        if i + radius - 1 > right:\n            left = i - radius + 1\n            right = i + radius - 1\n\n    even = [0] * n\n    left = 0\n    right = -1\n    for i in range(n):\n        radius = 0 if i > right else min(even[left + right - i + 1], right - i + 1)\n        while 0 <= i - radius - 1 and i + radius < n and s[i - radius - 1] == s[i + radius]:\n            radius += 1\n        even[i] = radius\n        if i + radius - 1 > right:\n            left = i - radius\n            right = i + radius - 1\n\n    print(sum(odd) + sum(even))\n\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
