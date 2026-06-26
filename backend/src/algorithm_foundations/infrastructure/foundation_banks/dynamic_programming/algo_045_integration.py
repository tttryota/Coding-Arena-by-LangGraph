from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('integration')

UNIT_BANK = unit_bank(
    unit_id='algo-045-integration',
    title='コイン問題（最小枚数） の総合演習',
    unit_kind='integration',
    target_skill='コイン問題（最小枚数） の総合演習',
    concept_overview='枚数上限つきの最小枚数 DP を 1 回作れば、同じコイン集合に対する複数の目標金額にも答えられます。ここでは bounded coin DP を前計算として使い回します。',
    problem_bank=[
        problem(
            problem_id='algo-045-integration-p1',
            title='コイン問題（最小枚数） の総合演習 / 枚数上限つきで複数の目標金額への最小枚数を答える',
            problem_statement='M 種類のコインについて、額面 c_i と使用できる枚数上限 b_i が与えられる。さらに Q 個の目標金額 x_j が与えられるので、各 x_j について合計をちょうど x_j にする最小枚数を求めよ。できなければ -1 を出力せよ。',
            input_format='1 行目に M Q。\n続く M 行に c_i b_i。\n続く Q 行に x_j。',
            output_format='各問い合わせの答えを 1 行ずつ出力する。',
            constraints='1 <= M <= 50\n1 <= Q <= 2 * 10^5\n1 <= c_i <= 10^4\n0 <= b_i <= 100\n1 <= x_j <= 10^4',
            examples=[{'input': '3 4\n1 2\n5 2\n7 1\n1\n6\n11\n14', 'output': '1\n2\n3\n4'}],
            canonical_reference_solution="def solve() -> None:\n    import sys\n    input = sys.stdin.readline\n    m, q = map(int, input().split())\n    items = [tuple(map(int, input().split())) for _ in range(m)]\n    queries = [int(input()) for _ in range(q)]\n    max_x = max(queries)\n    inf = 10 ** 18\n    dp = [inf] * (max_x + 1)\n    dp[0] = 0\n    for coin, limit in items:\n        nxt = dp[:]\n        for total in range(max_x + 1):\n            if dp[total] == inf:\n                continue\n            for used in range(1, limit + 1):\n                ntotal = total + coin * used\n                if ntotal > max_x:\n                    break\n                cand = dp[total] + used\n                if cand < nxt[ntotal]:\n                    nxt[ntotal] = cand\n        dp = nxt\n    out = []\n    for target in queries:\n        out.append(str(-1 if dp[target] == inf else dp[target]))\n    sys.stdout.write('\\n'.join(out))\n\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
