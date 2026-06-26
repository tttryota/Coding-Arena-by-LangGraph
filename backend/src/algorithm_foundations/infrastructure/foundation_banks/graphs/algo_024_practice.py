from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('foundation')

UNIT_BANK = unit_bank(
    unit_id='algo-024-practice',
    title='ワーシャルフロイド法 を素直に実装する',
    unit_kind='foundation',
    target_skill='ワーシャルフロイド法 を素直に実装する',
    concept_overview='ワーシャルフロイド法は、『この頂点を経由してよいか』を順に増やしながら、全点対間の最短距離を更新する解き方です。表を段階的に改善する形を押さえます。',
    problem_bank=[
        problem(
            problem_id='algo-024-practice-p1',
            title='ワーシャルフロイド法 を素直に実装する / 1 ケースをそのまま解く',
            problem_statement='N 頂点 M 辺の有向重み付きグラフと Q 個の問い合わせ s, t が与えられる。 各問い合わせについて s から t への最短距離を求め、到達できなければ -1 を出力せよ。',
            input_format='1 行目に N M Q。\n続く M 行に u v w。\n続く Q 行に s t。',
            output_format='各問い合わせの答えを 1 行ずつ出力する。',
            constraints='1 <= N <= 300\n1 <= M <= 2 * 10^5\n1 <= Q <= 2 * 10^5',
            examples=[
                {
                    'input': '3 3 2\n1 2 4\n2 3 5\n1 3 20\n1 3\n3 1',
                    'output': '9\n-1',
                },
            ],
            canonical_reference_solution="def solve() -> None:\n    import sys\n    input = sys.stdin.readline\n    n, m, q = map(int, input().split())\n    INF = 10 ** 18\n    dist = [[INF] * n for _ in range(n)]\n    for i in range(n):\n        dist[i][i] = 0\n    for _ in range(m):\n        u, v, w = map(int, input().split())\n        u -= 1\n        v -= 1\n        dist[u][v] = min(dist[u][v], w)\n    for k in range(n):\n        for i in range(n):\n            dik = dist[i][k]\n            if dik == INF:\n                continue\n            row_i = dist[i]\n            row_k = dist[k]\n            for j in range(n):\n                nd = dik + row_k[j]\n                if nd < row_i[j]:\n                    row_i[j] = nd\n    out = []\n    for _ in range(q):\n        s, t = map(int, input().split())\n        ans = dist[s - 1][t - 1]\n        out.append(str(-1 if ans == INF else ans))\n    sys.stdout.write('\\n'.join(out))\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
        problem(
            problem_id='algo-024-practice-p2',
            title='ワーシャルフロイド法 を素直に実装する / 2 ケースを連続して解く',
            problem_statement='2 ケース分の入力が続けて与えられる。それぞれについて、N 頂点 M 辺の有向重み付きグラフと Q 個の問い合わせ s, t が与えられる。 各問い合わせについて s から t への最短距離を求め、到達できなければ -1 を出力せよ。',
            input_format='1 行目に 2。\n続く 2 ケースについて:\n1 行目に N M Q。\n続く M 行に u v w。\n続く Q 行に s t。',
            output_format='各ケースの答えを順に出力する。',
            constraints='1 <= N <= 300\n1 <= M <= 2 * 10^5\n1 <= Q <= 2 * 10^5\n2 ケースの合計でも同じ方針で処理すること。',
            examples=[
                {
                    'input': '2\n3 3 2\n1 2 4\n2 3 5\n1 3 20\n1 3\n3 1\n3 3 2\n1 2 4\n2 3 5\n1 3 20\n1 3\n3 1',
                    'output': '9\n-1\n9\n-1',
                },
            ],
            canonical_reference_solution="import io\nimport sys\nfrom contextlib import redirect_stdout\n\ndef solve_one() -> None:\n    import sys\n    input = sys.stdin.readline\n    n, m, q = map(int, input().split())\n    INF = 10 ** 18\n    dist = [[INF] * n for _ in range(n)]\n    for i in range(n):\n        dist[i][i] = 0\n    for _ in range(m):\n        u, v, w = map(int, input().split())\n        u -= 1\n        v -= 1\n        dist[u][v] = min(dist[u][v], w)\n    for k in range(n):\n        for i in range(n):\n            dik = dist[i][k]\n            if dik == INF:\n                continue\n            row_i = dist[i]\n            row_k = dist[k]\n            for j in range(n):\n                nd = dik + row_k[j]\n                if nd < row_i[j]:\n                    row_i[j] = nd\n    out = []\n    for _ in range(q):\n        s, t = map(int, input().split())\n        ans = dist[s - 1][t - 1]\n        out.append(str(-1 if ans == INF else ans))\n    sys.stdout.write('\\n'.join(out))\n\ndef solve() -> None:\n    t = 2\n    outputs = []\n    for _ in range(t):\n        buf = io.StringIO()\n        with redirect_stdout(buf):\n            solve_one()\n        outputs.append(buf.getvalue().rstrip('\\n'))\n    sys.stdout.write('\\n'.join(outputs))\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
        problem(
            problem_id='algo-024-practice-p3',
            title='ワーシャルフロイド法 を素直に実装する / 3 ケースを連続して解く',
            problem_statement='3 ケース分の入力が続けて与えられる。それぞれについて、N 頂点 M 辺の有向重み付きグラフと Q 個の問い合わせ s, t が与えられる。 各問い合わせについて s から t への最短距離を求め、到達できなければ -1 を出力せよ。',
            input_format='1 行目に 3。\n続く 3 ケースについて:\n1 行目に N M Q。\n続く M 行に u v w。\n続く Q 行に s t。',
            output_format='各ケースの答えを順に出力する。',
            constraints='1 <= N <= 300\n1 <= M <= 2 * 10^5\n1 <= Q <= 2 * 10^5\n3 ケースの合計でも同じ方針で処理すること。',
            examples=[
                {
                    'input': '3\n3 3 2\n1 2 4\n2 3 5\n1 3 20\n1 3\n3 1\n3 3 2\n1 2 4\n2 3 5\n1 3 20\n1 3\n3 1\n3 3 2\n1 2 4\n2 3 5\n1 3 20\n1 3\n3 1',
                    'output': '9\n-1\n9\n-1\n9\n-1',
                },
            ],
            canonical_reference_solution="import io\nimport sys\nfrom contextlib import redirect_stdout\n\ndef solve_one() -> None:\n    import sys\n    input = sys.stdin.readline\n    n, m, q = map(int, input().split())\n    INF = 10 ** 18\n    dist = [[INF] * n for _ in range(n)]\n    for i in range(n):\n        dist[i][i] = 0\n    for _ in range(m):\n        u, v, w = map(int, input().split())\n        u -= 1\n        v -= 1\n        dist[u][v] = min(dist[u][v], w)\n    for k in range(n):\n        for i in range(n):\n            dik = dist[i][k]\n            if dik == INF:\n                continue\n            row_i = dist[i]\n            row_k = dist[k]\n            for j in range(n):\n                nd = dik + row_k[j]\n                if nd < row_i[j]:\n                    row_i[j] = nd\n    out = []\n    for _ in range(q):\n        s, t = map(int, input().split())\n        ans = dist[s - 1][t - 1]\n        out.append(str(-1 if ans == INF else ans))\n    sys.stdout.write('\\n'.join(out))\n\ndef solve() -> None:\n    t = 3\n    outputs = []\n    for _ in range(t):\n        buf = io.StringIO()\n        with redirect_stdout(buf):\n            solve_one()\n        outputs.append(buf.getvalue().rstrip('\\n'))\n    sys.stdout.write('\\n'.join(outputs))\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
