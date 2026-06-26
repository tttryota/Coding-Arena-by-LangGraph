from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('foundation')

UNIT_BANK = unit_bank(
    unit_id='algo-071-practice',
    title='Z-algorithm を素直に実装する',
    unit_kind='foundation',
    target_skill='Z-algorithm を素直に実装する',
    concept_overview='Z-algorithm では、各位置からどれだけ接頭辞が一致するかがまとめて分かるので、prefix が文字列中に何回現れるかも集計できます。ここでは各 prefix の出現回数を求めます。',
    problem_bank=[
        problem(
            problem_id='algo-071-practice-p1',
            title='Z-algorithm を素直に実装する / 各 prefix が文字列中に何回現れるかを求める',
            problem_statement='文字列 S が与えられる。各 L (1 <= L <= |S|) について、prefix S[1..L] が S の中に開始位置をそろえて何回現れるかを求めよ。',
            input_format='1 行目に S。',
            output_format='L=1 から |S| までの答えを空白区切りで出力する。',
            constraints='1 <= |S| <= 2 * 10^5',
            examples=[{'input': 'ababa', 'output': '3 2 2 1 1'}],
            canonical_reference_solution="def z_algorithm(text: str) -> list[int]:\n    z = [0] * len(text)\n    left = right = 0\n    for i in range(1, len(text)):\n        if i <= right:\n            z[i] = min(right - i + 1, z[i - left])\n        while i + z[i] < len(text) and text[z[i]] == text[i + z[i]]:\n            z[i] += 1\n        if i + z[i] - 1 > right:\n            left = i\n            right = i + z[i] - 1\n    z[0] = len(text)\n    return z\n\n\ndef solve() -> None:\n    s = input().strip()\n    n = len(s)\n    z = z_algorithm(s)\n    count = [0] * (n + 1)\n    for value in z[1:]:\n        count[value] += 1\n    for length in range(n - 1, 0, -1):\n        count[length] += count[length + 1]\n    ans = [str(count[length] + 1) for length in range(1, n + 1)]\n    print(' '.join(ans))\n\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
