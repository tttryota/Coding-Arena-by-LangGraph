from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('foundation')

UNIT_BANK = unit_bank(
    unit_id='algo-071-basic',
    title='Z-algorithm の基本',
    unit_kind='foundation',
    target_skill='Z-algorithm の基本',
    concept_overview='Z-algorithm は、各位置から始まる接尾辞が文字列全体の接頭辞とどれだけ一致するかを前計算する方法です。まずは Z 配列そのものを作る基本を学びます。',
    problem_bank=[
        problem(
            problem_id='algo-071-basic-p1',
            title='Z-algorithm の基本 / 文字列 S の Z 配列を求める',
            problem_statement='文字列 S が与えられる。各位置 i について、S[i..] と S 全体の接頭辞が一致する最長長さを求めよ。これを Z 配列として出力せよ。',
            input_format='1 行目に S。',
            output_format='Z 配列を空白区切りで出力する。',
            constraints='1 <= |S| <= 2 * 10^5',
            examples=[{'input': 'aabcaabxaaaz', 'output': '12 1 0 0 3 1 0 0 2 2 1 0'}],
            canonical_reference_solution="def z_algorithm(text: str) -> list[int]:\n    z = [0] * len(text)\n    left = right = 0\n    for i in range(1, len(text)):\n        if i <= right:\n            z[i] = min(right - i + 1, z[i - left])\n        while i + z[i] < len(text) and text[z[i]] == text[i + z[i]]:\n            z[i] += 1\n        if i + z[i] - 1 > right:\n            left = i\n            right = i + z[i] - 1\n    z[0] = len(text)\n    return z\n\n\ndef solve() -> None:\n    s = input().strip()\n    print(*z_algorithm(s))\n\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
