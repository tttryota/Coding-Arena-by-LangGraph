from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('foundation')

UNIT_BANK = unit_bank(
    unit_id='algo-024-basic',
    title='ワーシャルフロイド法 の基本',
    unit_kind='foundation',
    target_skill='ワーシャルフロイド法 の基本',
    concept_overview='ワーシャルフロイド法の三重ループは、距離だけでなく「到達できるかどうか」の判定にも使えます。まずは重みなしの到達可能性から始めます。',
    problem_bank=[
        problem(
            problem_id='algo-024-basic-p1',
            title='ワーシャルフロイド法 の基本 / 頂点対が到達可能かを判定する',
            problem_statement='N 頂点 M 辺の有向グラフと Q 個の問い合わせ s, t が与えられる。各問い合わせについて、s から t へ到達可能なら Yes、そうでなければ No を出力せよ。',
            input_format='1 行目に N M Q。\n続く M 行に u v。\n続く Q 行に s t。',
            output_format='各問い合わせの答えを 1 行ずつ出力する。',
            constraints='1 <= N <= 300\n1 <= M <= 2 * 10^5\n1 <= Q <= 2 * 10^5',
            examples=[{'input': '4 4 3\n1 2\n2 3\n1 4\n4 3\n1 3\n3 1\n1 4', 'output': 'Yes\nNo\nYes'}],
            canonical_reference_solution="def solve() -> None:\n    import sys\n    input = sys.stdin.readline\n    n, m, q = map(int, input().split())\n    reach = [[False] * n for _ in range(n)]\n    for i in range(n):\n        reach[i][i] = True\n    for _ in range(m):\n        u, v = map(int, input().split())\n        reach[u - 1][v - 1] = True\n    for k in range(n):\n        for i in range(n):\n            if not reach[i][k]:\n                continue\n            row_i = reach[i]\n            row_k = reach[k]\n            for j in range(n):\n                if row_k[j]:\n                    row_i[j] = True\n    out = []\n    for _ in range(q):\n        s, t = map(int, input().split())\n        out.append('Yes' if reach[s - 1][t - 1] else 'No')\n    print('\\n'.join(out))\n\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
