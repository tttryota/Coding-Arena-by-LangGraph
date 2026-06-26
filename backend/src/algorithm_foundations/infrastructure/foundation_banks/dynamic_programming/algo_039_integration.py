from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('integration')

UNIT_BANK = unit_bank(
    unit_id='algo-039-integration',
    title='編集距離（レーベンシュタイン距離） の総合演習',
    unit_kind='integration',
    target_skill='編集距離（レーベンシュタイン距離） の総合演習',
    concept_overview='編集距離の DP 表が作れると、最小コストだけでなく実際にどの操作を選んだかも逆向きに復元できます。ここでは 1 本の最短編集手順を出力します。',
    problem_bank=[
        problem(
            problem_id='algo-039-integration-p1',
            title='編集距離（レーベンシュタイン距離） の総合演習 / 1 本の最短編集手順を復元する',
            problem_statement='2 つの文字列 S, T が与えられる。S を T に変える編集距離を求め、その最短編集手順を 1 つ出力せよ。出力する操作は次の 4 種とする。`MATCH c` は同じ文字 c をそのまま対応させる。`REPLACE a b` は文字 a を b に置き換える。`DELETE a` は文字 a を削除する。`INSERT b` は文字 b を挿入する。操作列は左から右へ順に読み進めるものとする。',
            input_format='1 行目に S。\n2 行目に T。',
            output_format='1 行目に編集距離 D、2 行目に操作数 K、続く K 行に操作を 1 つずつ出力する。',
            constraints='1 <= |S|, |T| <= 500',
            examples=[{'input': 'abc\nadc', 'output': '1\n3\nMATCH a\nREPLACE b d\nMATCH c'}],
            canonical_reference_solution="def solve() -> None:\n    s = input().strip()\n    t = input().strip()\n    n, m = len(s), len(t)\n    dp = [[0] * (m + 1) for _ in range(n + 1)]\n    for i in range(n + 1):\n        dp[i][0] = i\n    for j in range(m + 1):\n        dp[0][j] = j\n    for i in range(1, n + 1):\n        for j in range(1, m + 1):\n            cost = 0 if s[i - 1] == t[j - 1] else 1\n            dp[i][j] = min(\n                dp[i - 1][j] + 1,\n                dp[i][j - 1] + 1,\n                dp[i - 1][j - 1] + cost,\n            )\n\n    ops = []\n    i, j = n, m\n    while i > 0 or j > 0:\n        if i > 0 and j > 0:\n            cost = 0 if s[i - 1] == t[j - 1] else 1\n            if dp[i][j] == dp[i - 1][j - 1] + cost:\n                if cost == 0:\n                    ops.append(f'MATCH {s[i - 1]}')\n                else:\n                    ops.append(f'REPLACE {s[i - 1]} {t[j - 1]}')\n                i -= 1\n                j -= 1\n                continue\n        if i > 0 and dp[i][j] == dp[i - 1][j] + 1:\n            ops.append(f'DELETE {s[i - 1]}')\n            i -= 1\n            continue\n        ops.append(f'INSERT {t[j - 1]}')\n        j -= 1\n\n    ops.reverse()\n    print(dp[n][m])\n    print(len(ops))\n    print('\\n'.join(ops))\n\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
