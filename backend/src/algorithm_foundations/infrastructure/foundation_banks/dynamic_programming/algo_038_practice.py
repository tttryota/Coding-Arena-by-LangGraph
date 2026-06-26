from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('foundation')

UNIT_BANK = unit_bank(
    unit_id='algo-038-practice',
    title='最長共通部分列（LCS） を素直に実装する',
    unit_kind='foundation',
    target_skill='最長共通部分列（LCS） を素直に実装する',
    concept_overview='LCS の DP 表からは、長さだけでなく実際の共通部分列も復元できます。ここでは 1 本の LCS 文字列を出力します。',
    problem_bank=[
        problem(
            problem_id='algo-038-practice-p1',
            title='最長共通部分列（LCS） を素直に実装する / 1 本の LCS を復元する',
            problem_statement='2 つの文字列 S, T が与えられる。最長共通部分列の長さと、そのような部分列を 1 つ出力せよ。',
            input_format='1 行目に S。\n2 行目に T。',
            output_format='1 行目に LCS の長さ、2 行目に LCS を出力する。',
            constraints='1 <= |S|, |T| <= 2000',
            examples=[{'input': 'abcde\nace', 'output': '3\nace'}],
            canonical_reference_solution="def solve() -> None:\n    import sys\n    input = sys.stdin.readline\n    s = input().strip()\n    t = input().strip()\n    n, m = len(s), len(t)\n    dp = [[0] * (m + 1) for _ in range(n + 1)]\n    for i in range(n):\n        for j in range(m):\n            if s[i] == t[j]:\n                dp[i + 1][j + 1] = dp[i][j] + 1\n            elif dp[i][j + 1] >= dp[i + 1][j]:\n                dp[i + 1][j + 1] = dp[i][j + 1]\n            else:\n                dp[i + 1][j + 1] = dp[i + 1][j]\n    out = []\n    i, j = n, m\n    while i > 0 and j > 0:\n        if s[i - 1] == t[j - 1]:\n            out.append(s[i - 1])\n            i -= 1\n            j -= 1\n        elif dp[i - 1][j] >= dp[i][j - 1]:\n            i -= 1\n        else:\n            j -= 1\n    out.reverse()\n    ans = ''.join(out)\n    print(len(ans))\n    print(ans)\n\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
