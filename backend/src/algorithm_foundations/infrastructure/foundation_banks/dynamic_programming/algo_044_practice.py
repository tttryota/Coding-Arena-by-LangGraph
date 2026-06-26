from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('foundation')

UNIT_BANK = unit_bank(
    unit_id='algo-044-practice',
    title='部分和問題 を素直に実装する',
    unit_kind='foundation',
    target_skill='部分和問題 を素直に実装する',
    concept_overview='部分和 DP では、到達可能性だけでなく「どの数を選んだか」も復元できます。ここではちょうど S を作る 1 つの選び方を出力します。',
    problem_bank=[
        problem(
            problem_id='algo-044-practice-p1',
            title='部分和問題 を素直に実装する / ちょうど S を作る番号集合を 1 つ復元する',
            problem_statement='N 個の正整数 A と目標値 S が与えられる。いくつかを選んで合計をちょうど S にできるなら Yes を出力し、そのような番号集合を 1 つ出力せよ。できなければ No を出力せよ。',
            input_format='1 行目に N S。\n2 行目に A1..AN。',
            output_format='作れないなら No を 1 行だけ出力する。作れるなら 1 行目に Yes、2 行目に選んだ個数 K、3 行目に選んだ番号を昇順で空白区切りにして出力する。',
            constraints='1 <= N <= 200\n1 <= S <= 2 * 10^5',
            examples=[{'input': '4 11\n2 5 9 4', 'output': 'Yes\n3\n1 2 4'}],
            canonical_reference_solution="def solve() -> None:\n    import sys\n    input = sys.stdin.readline\n    n, s = map(int, input().split())\n    a = list(map(int, input().split()))\n    dp = [[False] * (s + 1) for _ in range(n + 1)]\n    dp[0][0] = True\n    for i, value in enumerate(a, start=1):\n        for total in range(s + 1):\n            if dp[i - 1][total]:\n                dp[i][total] = True\n            if total >= value and dp[i - 1][total - value]:\n                dp[i][total] = True\n    if not dp[n][s]:\n        print('No')\n        return\n    ans = []\n    total = s\n    for i in range(n, 0, -1):\n        value = a[i - 1]\n        if total >= value and dp[i - 1][total - value]:\n            ans.append(i)\n            total -= value\n    ans.reverse()\n    print('Yes')\n    print(len(ans))\n    print(*ans)\n\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
