from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('integration')

UNIT_BANK = unit_bank(
    unit_id='algo-022-integration',
    title='ダイクストラ法 の総合演習',
    unit_kind='integration',
    target_skill='ダイクストラ法 の総合演習',
    concept_overview='ダイクストラ法は、重みが負でないグラフで、いちばん近い頂点から順に最短距離を確定していく解き方です。優先度付きキューを使う最短路の基本形です。 この unit では、既習の ダイクストラ法 の基本 と ダイクストラ法 を素直に実装する を順に使いながら、1 問を分けて解く流れまで確認します。',
    problem_bank=[
        problem(
            problem_id='algo-022-integration-p1',
            title='ダイクストラ法 の総合演習 / 1 ケースをそのまま解く',
            problem_statement='N 頂点 M 辺の有向重み付きグラフが与えられる。 頂点 1 から頂点 N への最短距離を求め、到達できないなら -1 を出力せよ。\n\nこの問題では、前提 unit までで扱った知識だけを順に使えば解ける。',
            input_format='1 行目に N M。\n続く M 行に u v w。',
            output_format='頂点 1 から頂点 N までの最短距離を出力する。',
            constraints='1 <= N, M <= 2 * 10^5\n1 <= w <= 10^9\n使う知識は前提 unit までに限定すること。',
            examples=[
                {
                    'input': '4 4\n1 2 3\n2 4 5\n1 3 10\n3 4 1',
                    'output': '8',
                },
            ],
            canonical_reference_solution="import heapq\n\ndef solve() -> None:\n    import sys\n    input = sys.stdin.readline\n    n, m = map(int, input().split())\n    graph = [[] for _ in range(n)]\n    for _ in range(m):\n        u, v, w = map(int, input().split())\n        graph[u - 1].append((v - 1, w))\n    INF = 10 ** 30\n    dist = [INF] * n\n    dist[0] = 0\n    heap = [(0, 0)]\n    while heap:\n        cost, node = heapq.heappop(heap)\n        if cost != dist[node]:\n            continue\n        for nxt, w in graph[node]:\n            nd = cost + w\n            if nd < dist[nxt]:\n                dist[nxt] = nd\n                heapq.heappush(heap, (nd, nxt))\n    print(-1 if dist[-1] == INF else dist[-1])\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
        problem(
            problem_id='algo-022-integration-p2',
            title='ダイクストラ法 の総合演習 / 2 ケースを連続して解く',
            problem_statement='2 ケース分の入力が続けて与えられる。それぞれについて、N 頂点 M 辺の有向重み付きグラフが与えられる。 頂点 1 から頂点 N への最短距離を求め、到達できないなら -1 を出力せよ。\n\nこの問題では、前提 unit までで扱った知識だけを順に使えば解ける。',
            input_format='1 行目に 2。\n続く 2 ケースについて:\n1 行目に N M。\n続く M 行に u v w。',
            output_format='各ケースの答えを順に出力する。',
            constraints='1 <= N, M <= 2 * 10^5\n1 <= w <= 10^9\n使う知識は前提 unit までに限定すること。\n2 ケースの合計でも同じ方針で処理すること。',
            examples=[
                {
                    'input': '2\n4 4\n1 2 3\n2 4 5\n1 3 10\n3 4 1\n4 4\n1 2 3\n2 4 5\n1 3 10\n3 4 1',
                    'output': '8\n8',
                },
            ],
            canonical_reference_solution="import io\nimport sys\nfrom contextlib import redirect_stdout\n\nimport heapq\n\ndef solve_one() -> None:\n    import sys\n    input = sys.stdin.readline\n    n, m = map(int, input().split())\n    graph = [[] for _ in range(n)]\n    for _ in range(m):\n        u, v, w = map(int, input().split())\n        graph[u - 1].append((v - 1, w))\n    INF = 10 ** 30\n    dist = [INF] * n\n    dist[0] = 0\n    heap = [(0, 0)]\n    while heap:\n        cost, node = heapq.heappop(heap)\n        if cost != dist[node]:\n            continue\n        for nxt, w in graph[node]:\n            nd = cost + w\n            if nd < dist[nxt]:\n                dist[nxt] = nd\n                heapq.heappush(heap, (nd, nxt))\n    print(-1 if dist[-1] == INF else dist[-1])\n\ndef solve() -> None:\n    t = 2\n    outputs = []\n    for _ in range(t):\n        buf = io.StringIO()\n        with redirect_stdout(buf):\n            solve_one()\n        outputs.append(buf.getvalue().rstrip('\\n'))\n    sys.stdout.write('\\n'.join(outputs))\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
        problem(
            problem_id='algo-022-integration-p3',
            title='ダイクストラ法 の総合演習 / 3 ケースを連続して解く',
            problem_statement='3 ケース分の入力が続けて与えられる。それぞれについて、N 頂点 M 辺の有向重み付きグラフが与えられる。 頂点 1 から頂点 N への最短距離を求め、到達できないなら -1 を出力せよ。\n\nこの問題では、前提 unit までで扱った知識だけを順に使えば解ける。',
            input_format='1 行目に 3。\n続く 3 ケースについて:\n1 行目に N M。\n続く M 行に u v w。',
            output_format='各ケースの答えを順に出力する。',
            constraints='1 <= N, M <= 2 * 10^5\n1 <= w <= 10^9\n使う知識は前提 unit までに限定すること。\n3 ケースの合計でも同じ方針で処理すること。',
            examples=[
                {
                    'input': '3\n4 4\n1 2 3\n2 4 5\n1 3 10\n3 4 1\n4 4\n1 2 3\n2 4 5\n1 3 10\n3 4 1\n4 4\n1 2 3\n2 4 5\n1 3 10\n3 4 1',
                    'output': '8\n8\n8',
                },
            ],
            canonical_reference_solution="import io\nimport sys\nfrom contextlib import redirect_stdout\n\nimport heapq\n\ndef solve_one() -> None:\n    import sys\n    input = sys.stdin.readline\n    n, m = map(int, input().split())\n    graph = [[] for _ in range(n)]\n    for _ in range(m):\n        u, v, w = map(int, input().split())\n        graph[u - 1].append((v - 1, w))\n    INF = 10 ** 30\n    dist = [INF] * n\n    dist[0] = 0\n    heap = [(0, 0)]\n    while heap:\n        cost, node = heapq.heappop(heap)\n        if cost != dist[node]:\n            continue\n        for nxt, w in graph[node]:\n            nd = cost + w\n            if nd < dist[nxt]:\n                dist[nxt] = nd\n                heapq.heappush(heap, (nd, nxt))\n    print(-1 if dist[-1] == INF else dist[-1])\n\ndef solve() -> None:\n    t = 3\n    outputs = []\n    for _ in range(t):\n        buf = io.StringIO()\n        with redirect_stdout(buf):\n            solve_one()\n        outputs.append(buf.getvalue().rstrip('\\n'))\n    sys.stdout.write('\\n'.join(outputs))\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
