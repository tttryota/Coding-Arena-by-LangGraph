from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('foundation')

UNIT_BANK = unit_bank(
    unit_id='algo-041-practice',
    title='桁DP を素直に実装する',
    unit_kind='foundation',
    target_skill='桁DP を素直に実装する',
    concept_overview='桁DPでは、「上限にぴったり一致しているか」に加えて、桁和の余りのような追加状態も持てます。ここでは桁和条件つきの個数を数えます。',
    problem_bank=[
        problem(
            problem_id='algo-041-practice-p1',
            title='桁DP を素直に実装する / 桁和が D の倍数になる個数を数える',
            problem_statement='整数 N と正整数 D が与えられる。0 以上 N 以下の整数のうち、10 進表記の各桁の和が D の倍数であるものの個数を求めよ。',
            input_format='1 行目に N D。',
            output_format='個数を出力する。',
            constraints='0 <= N <= 10^18\n1 <= D <= 100',
            examples=[{'input': '20 3', 'output': '7'}],
            canonical_reference_solution="def solve() -> None:\n    n_str, d_str = input().split()\n    d = int(d_str)\n    digits = [ord(ch) - ord('0') for ch in n_str]\n    dp = [[0] * d for _ in range(2)]\n    dp[0][0] = 1\n    for limit in digits:\n        nxt = [[0] * d for _ in range(2)]\n        for tight in range(2):\n            upper = limit if tight == 0 else 9\n            for mod in range(d):\n                cur = dp[tight][mod]\n                if cur == 0:\n                    continue\n                for digit in range(upper + 1):\n                    ntight = 1 if tight or digit < limit else 0\n                    nxt[ntight][(mod + digit) % d] += cur\n        dp = nxt\n    print(dp[0][0] + dp[1][0])\n\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
