from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('foundation')

UNIT_BANK = unit_bank(
    unit_id='algo-027-basic',
    title='トポロジカルソート の基本',
    unit_kind='foundation',
    target_skill='トポロジカルソート の基本',
    concept_overview='トポロジカルソートは、依存関係を壊さない順番に頂点を並べる考え方です。『先に済ませるべきもの』を整理して順序を作る基本を学びます。',
    problem_bank=[
        problem(
            problem_id='algo-027-basic-p1',
            title='トポロジカルソート の基本 / 1 ケースをそのまま解く',
            problem_statement='N 頂点 M 辺の有向非巡回グラフが与えられる。 辞書順最小のトポロジカル順序を 1 つ出力せよ。',
            input_format='1 行目に N M。\n続く M 行に辺 u v。',
            output_format='トポロジカル順序を空白区切りで出力する。',
            constraints='1 <= N, M <= 2 * 10^5',
            examples=[
                {
                    'input': '4 3\n1 2\n1 3\n3 4',
                    'output': '1 2 3 4',
                },
            ],
            canonical_reference_solution="import heapq\n\ndef solve() -> None:\n    import sys\n    input = sys.stdin.readline\n    n, m = map(int, input().split())\n    graph = [[] for _ in range(n)]\n    indeg = [0] * n\n    for _ in range(m):\n        u, v = map(int, input().split())\n        u -= 1\n        v -= 1\n        graph[u].append(v)\n        indeg[v] += 1\n    pq = [i for i, deg in enumerate(indeg) if deg == 0]\n    heapq.heapify(pq)\n    order = []\n    while pq:\n        node = heapq.heappop(pq)\n        order.append(node + 1)\n        for nxt in graph[node]:\n            indeg[nxt] -= 1\n            if indeg[nxt] == 0:\n                heapq.heappush(pq, nxt)\n    print(*order)\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
        problem(
            problem_id='algo-027-basic-p2',
            title='トポロジカルソート の基本 / 2 ケースを連続して解く',
            problem_statement='2 ケース分の入力が続けて与えられる。それぞれについて、N 頂点 M 辺の有向非巡回グラフが与えられる。 辞書順最小のトポロジカル順序を 1 つ出力せよ。',
            input_format='1 行目に 2。\n続く 2 ケースについて:\n1 行目に N M。\n続く M 行に辺 u v。',
            output_format='各ケースの答えを順に出力する。',
            constraints='1 <= N, M <= 2 * 10^5\n2 ケースの合計でも同じ方針で処理すること。',
            examples=[
                {
                    'input': '2\n4 3\n1 2\n1 3\n3 4\n4 3\n1 2\n1 3\n3 4',
                    'output': '1 2 3 4\n1 2 3 4',
                },
            ],
            canonical_reference_solution="import io\nimport sys\nfrom contextlib import redirect_stdout\n\nimport heapq\n\ndef solve_one() -> None:\n    import sys\n    input = sys.stdin.readline\n    n, m = map(int, input().split())\n    graph = [[] for _ in range(n)]\n    indeg = [0] * n\n    for _ in range(m):\n        u, v = map(int, input().split())\n        u -= 1\n        v -= 1\n        graph[u].append(v)\n        indeg[v] += 1\n    pq = [i for i, deg in enumerate(indeg) if deg == 0]\n    heapq.heapify(pq)\n    order = []\n    while pq:\n        node = heapq.heappop(pq)\n        order.append(node + 1)\n        for nxt in graph[node]:\n            indeg[nxt] -= 1\n            if indeg[nxt] == 0:\n                heapq.heappush(pq, nxt)\n    print(*order)\n\ndef solve() -> None:\n    t = 2\n    outputs = []\n    for _ in range(t):\n        buf = io.StringIO()\n        with redirect_stdout(buf):\n            solve_one()\n        outputs.append(buf.getvalue().rstrip('\\n'))\n    sys.stdout.write('\\n'.join(outputs))\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
        problem(
            problem_id='algo-027-basic-p3',
            title='トポロジカルソート の基本 / 3 ケースを連続して解く',
            problem_statement='3 ケース分の入力が続けて与えられる。それぞれについて、N 頂点 M 辺の有向非巡回グラフが与えられる。 辞書順最小のトポロジカル順序を 1 つ出力せよ。',
            input_format='1 行目に 3。\n続く 3 ケースについて:\n1 行目に N M。\n続く M 行に辺 u v。',
            output_format='各ケースの答えを順に出力する。',
            constraints='1 <= N, M <= 2 * 10^5\n3 ケースの合計でも同じ方針で処理すること。',
            examples=[
                {
                    'input': '3\n4 3\n1 2\n1 3\n3 4\n4 3\n1 2\n1 3\n3 4\n4 3\n1 2\n1 3\n3 4',
                    'output': '1 2 3 4\n1 2 3 4\n1 2 3 4',
                },
            ],
            canonical_reference_solution="import io\nimport sys\nfrom contextlib import redirect_stdout\n\nimport heapq\n\ndef solve_one() -> None:\n    import sys\n    input = sys.stdin.readline\n    n, m = map(int, input().split())\n    graph = [[] for _ in range(n)]\n    indeg = [0] * n\n    for _ in range(m):\n        u, v = map(int, input().split())\n        u -= 1\n        v -= 1\n        graph[u].append(v)\n        indeg[v] += 1\n    pq = [i for i, deg in enumerate(indeg) if deg == 0]\n    heapq.heapify(pq)\n    order = []\n    while pq:\n        node = heapq.heappop(pq)\n        order.append(node + 1)\n        for nxt in graph[node]:\n            indeg[nxt] -= 1\n            if indeg[nxt] == 0:\n                heapq.heappush(pq, nxt)\n    print(*order)\n\ndef solve() -> None:\n    t = 3\n    outputs = []\n    for _ in range(t):\n        buf = io.StringIO()\n        with redirect_stdout(buf):\n            solve_one()\n        outputs.append(buf.getvalue().rstrip('\\n'))\n    sys.stdout.write('\\n'.join(outputs))\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
