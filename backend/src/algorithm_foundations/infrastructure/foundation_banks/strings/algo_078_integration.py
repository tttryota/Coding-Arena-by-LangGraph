from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('integration')

UNIT_BANK = unit_bank(
    unit_id='algo-078-integration',
    title='回文判定 の総合演習',
    unit_kind='integration',
    target_skill='回文判定 の総合演習',
    concept_overview='回文判定で左右を比べる視点を持てると、不一致が出た地点で「左を捨てるか右を捨てるか」を分岐する問題も扱えます。ここでは単純な回文判定に 1 回だけの調整を組み合わせます。',
    problem_bank=[
        problem(
            problem_id='algo-078-integration-p1',
            title='回文判定 の総合演習 / 1 文字まで削除して回文にできるか判定する',
            problem_statement='文字列 S が与えられる。高々 1 文字を削除して S を回文にできるなら Yes、できないなら No を出力せよ。',
            input_format='1 行目に文字列 S。',
            output_format='Yes / No を出力する。',
            constraints='1 <= |S| <= 2 * 10^5',
            examples=[{'input': 'abca', 'output': 'Yes'}],
            canonical_reference_solution="def is_palindrome_range(s: str, left: int, right: int) -> bool:\n    while left < right:\n        if s[left] != s[right]:\n            return False\n        left += 1\n        right -= 1\n    return True\n\n\ndef solve() -> None:\n    s = input().strip()\n    left = 0\n    right = len(s) - 1\n    while left < right and s[left] == s[right]:\n        left += 1\n        right -= 1\n    if left >= right:\n        print('Yes')\n        return\n    ok = is_palindrome_range(s, left + 1, right) or is_palindrome_range(s, left, right - 1)\n    print('Yes' if ok else 'No')\n\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
