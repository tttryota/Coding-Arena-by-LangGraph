from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('foundation')

UNIT_BANK = unit_bank(
    unit_id='algo-023-basic',
    title='ベルマンフォード法 の基本',
    unit_kind='foundation',
    target_skill='ベルマンフォード法 の基本',
    concept_overview='ベルマンフォード法は、辺の緩和を繰り返して最短距離を更新する解き方です。負辺がある場合や負閉路の検出まで扱える基本を学びます。',
    problem_bank=[
        problem(
            problem_id='algo-023-basic-p1',
            title='ベルマンフォード法 の基本 / 1 ケースをそのまま解く',
            problem_statement='N 頂点 M 辺の有向重み付きグラフが与えられる。 頂点 1 から各頂点への最短距離をベルマンフォード法で求め、頂点 N の距離を出力せよ。 到達できなければ -1 を出力する。',
            input_format='1 行目に N M。\n続く M 行に u v w。',
            output_format='頂点 1 から頂点 N までの最短距離を出力する。',
            constraints='1 <= N <= 500\n1 <= M <= 2 * 10^5\n-10^9 <= w <= 10^9',
            examples=[
                {
                    'input': '4 4\n1 2 3\n2 4 5\n1 3 10\n3 4 1',
                    'output': '8',
                },
            ],
            canonical_reference_solution="def solve() -> None:\n    import sys\n    input = sys.stdin.readline\n    n, m = map(int, input().split())\n    edges = [tuple(map(int, input().split())) for _ in range(m)]\n    INF = 10 ** 18\n    dist = [INF] * n\n    dist[0] = 0\n    for _ in range(n - 1):\n        updated = False\n        for u, v, w in edges:\n            if dist[u - 1] == INF:\n                continue\n            nd = dist[u - 1] + w\n            if nd < dist[v - 1]:\n                dist[v - 1] = nd\n                updated = True\n        if not updated:\n            break\n    print(-1 if dist[-1] == INF else dist[-1])\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
        problem(
            problem_id='algo-023-basic-p2',
            title='ベルマンフォード法 の基本 / 2 ケースを連続して解く',
            problem_statement='2 ケース分の入力が続けて与えられる。それぞれについて、N 頂点 M 辺の有向重み付きグラフが与えられる。 頂点 1 から各頂点への最短距離をベルマンフォード法で求め、頂点 N の距離を出力せよ。 到達できなければ -1 を出力する。',
            input_format='1 行目に 2。\n続く 2 ケースについて:\n1 行目に N M。\n続く M 行に u v w。',
            output_format='各ケースの答えを順に出力する。',
            constraints='1 <= N <= 500\n1 <= M <= 2 * 10^5\n-10^9 <= w <= 10^9\n2 ケースの合計でも同じ方針で処理すること。',
            examples=[
                {
                    'input': '2\n4 4\n1 2 3\n2 4 5\n1 3 10\n3 4 1\n4 4\n1 2 3\n2 4 5\n1 3 10\n3 4 1',
                    'output': '8\n8',
                },
            ],
            canonical_reference_solution="import io\nimport sys\nfrom contextlib import redirect_stdout\n\ndef solve_one() -> None:\n    import sys\n    input = sys.stdin.readline\n    n, m = map(int, input().split())\n    edges = [tuple(map(int, input().split())) for _ in range(m)]\n    INF = 10 ** 18\n    dist = [INF] * n\n    dist[0] = 0\n    for _ in range(n - 1):\n        updated = False\n        for u, v, w in edges:\n            if dist[u - 1] == INF:\n                continue\n            nd = dist[u - 1] + w\n            if nd < dist[v - 1]:\n                dist[v - 1] = nd\n                updated = True\n        if not updated:\n            break\n    print(-1 if dist[-1] == INF else dist[-1])\n\ndef solve() -> None:\n    t = 2\n    outputs = []\n    for _ in range(t):\n        buf = io.StringIO()\n        with redirect_stdout(buf):\n            solve_one()\n        outputs.append(buf.getvalue().rstrip('\\n'))\n    sys.stdout.write('\\n'.join(outputs))\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
        problem(
            problem_id='algo-023-basic-p3',
            title='ベルマンフォード法 の基本 / 3 ケースを連続して解く',
            problem_statement='3 ケース分の入力が続けて与えられる。それぞれについて、N 頂点 M 辺の有向重み付きグラフが与えられる。 頂点 1 から各頂点への最短距離をベルマンフォード法で求め、頂点 N の距離を出力せよ。 到達できなければ -1 を出力する。',
            input_format='1 行目に 3。\n続く 3 ケースについて:\n1 行目に N M。\n続く M 行に u v w。',
            output_format='各ケースの答えを順に出力する。',
            constraints='1 <= N <= 500\n1 <= M <= 2 * 10^5\n-10^9 <= w <= 10^9\n3 ケースの合計でも同じ方針で処理すること。',
            examples=[
                {
                    'input': '3\n4 4\n1 2 3\n2 4 5\n1 3 10\n3 4 1\n4 4\n1 2 3\n2 4 5\n1 3 10\n3 4 1\n4 4\n1 2 3\n2 4 5\n1 3 10\n3 4 1',
                    'output': '8\n8\n8',
                },
            ],
            canonical_reference_solution="import io\nimport sys\nfrom contextlib import redirect_stdout\n\ndef solve_one() -> None:\n    import sys\n    input = sys.stdin.readline\n    n, m = map(int, input().split())\n    edges = [tuple(map(int, input().split())) for _ in range(m)]\n    INF = 10 ** 18\n    dist = [INF] * n\n    dist[0] = 0\n    for _ in range(n - 1):\n        updated = False\n        for u, v, w in edges:\n            if dist[u - 1] == INF:\n                continue\n            nd = dist[u - 1] + w\n            if nd < dist[v - 1]:\n                dist[v - 1] = nd\n                updated = True\n        if not updated:\n            break\n    print(-1 if dist[-1] == INF else dist[-1])\n\ndef solve() -> None:\n    t = 3\n    outputs = []\n    for _ in range(t):\n        buf = io.StringIO()\n        with redirect_stdout(buf):\n            solve_one()\n        outputs.append(buf.getvalue().rstrip('\\n'))\n    sys.stdout.write('\\n'.join(outputs))\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
