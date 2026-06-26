from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('integration')

UNIT_BANK = unit_bank(
    unit_id='algo-021-integration',
    title='隣接リスト・隣接行列 の総合演習',
    unit_kind='integration',
    target_skill='隣接リスト・隣接行列 の総合演習',
    concept_overview='隣接行列では、頂点 u から v へ辺があるかを表の 1 マスで持てます。辺を読み込んだあとに存在判定を何度も答える流れで、表現の使い分けを確認します。',
    problem_bank=[
        problem(
            problem_id='algo-021-integration-p1',
            title='隣接リスト・隣接行列 の総合演習 / 問い合わせの 2 頂点の間に辺があるか判定する',
            problem_statement='N 頂点 M 辺の無向グラフと Q 個の問い合わせが与えられる。各問い合わせ u, v について、u と v の間に辺があれば Yes、なければ No を出力せよ。',
            input_format='1 行目に N M Q。\n続く M 行に辺 u v。\n続く Q 行に問い合わせ u v。',
            output_format='各問い合わせの答えを 1 行ずつ出力する。',
            constraints='1 <= N <= 2000\n0 <= M <= N * (N - 1) / 2\n1 <= Q <= 2 * 10^5',
            examples=[{'input': '4 3 4\n1 2\n2 3\n2 4\n1 2\n1 3\n2 4\n3 4', 'output': 'Yes\nNo\nYes\nNo'}],
            canonical_reference_solution="def solve() -> None:\n    import sys\n    input = sys.stdin.readline\n    n, m, q = map(int, input().split())\n    adj = [[False] * n for _ in range(n)]\n    for _ in range(m):\n        u, v = map(int, input().split())\n        u -= 1\n        v -= 1\n        adj[u][v] = True\n        adj[v][u] = True\n    out = []\n    for _ in range(q):\n        u, v = map(int, input().split())\n        out.append('Yes' if adj[u - 1][v - 1] else 'No')\n    sys.stdout.write('\\n'.join(out))\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
