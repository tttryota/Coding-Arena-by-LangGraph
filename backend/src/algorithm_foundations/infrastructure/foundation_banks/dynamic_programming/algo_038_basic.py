from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('foundation')

UNIT_BANK = unit_bank(
    unit_id='algo-038-basic',
    title='最長共通部分列（LCS） の基本',
    unit_kind='foundation',
    target_skill='最長共通部分列（LCS） の基本',
    concept_overview='LCS では、S の先頭 i 文字と T の先頭 j 文字までで答えを持ち、最後の文字を使うか使わないかで遷移します。2 文字列の prefix 同士で表を埋める基本を身につけます。',
    problem_bank=[
        problem(
            problem_id='algo-038-basic-p1',
            title='最長共通部分列（LCS） の基本 / 最長共通部分列の長さを求める',
            problem_statement='2 つの文字列 S, T が与えられる。最長共通部分列の長さを求めよ。',
            input_format='1 行目に S。\n2 行目に T。',
            output_format='LCS の長さを出力する。',
            constraints='1 <= |S|, |T| <= 2000',
            examples=[{'input': 'abcde\nace', 'output': '3'}],
            canonical_reference_solution="def solve() -> None:\n    import sys\n    input = sys.stdin.readline\n    s = input().strip()\n    t = input().strip()\n    dp = [0] * (len(t) + 1)\n    for ch in s:\n        prev = 0\n        for j, tch in enumerate(t, start=1):\n            saved = dp[j]\n            if ch == tch:\n                dp[j] = prev + 1\n            else:\n                dp[j] = max(dp[j], dp[j - 1])\n            prev = saved\n    print(dp[-1])\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
