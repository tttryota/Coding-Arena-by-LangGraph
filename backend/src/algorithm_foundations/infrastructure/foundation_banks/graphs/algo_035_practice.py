from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('foundation')

UNIT_BANK = unit_bank(
    unit_id='algo-035-practice',
    title='関節点・橋の検出 を素直に実装する',
    unit_kind='foundation',
    target_skill='関節点・橋の検出 を素直に実装する',
    concept_overview='関節点・橋の検出は、入力の構造や候補を整理し、決まった手順で答えを作る知識です。まずは典型の使い方を自分の手で追える状態を目指します。',
    problem_bank=[
        problem(
            problem_id='algo-035-practice-p1',
            title='関節点・橋の検出 を素直に実装する / 1 ケースをそのまま解く',
            problem_statement='無向グラフが与えられる。橋の本数を求めよ。',
            input_format='1 行目に N M。\n続く M 行に辺 u v。',
            output_format='橋の本数を出力する。',
            constraints='1 <= N, M <= 2 * 10^5',
            examples=[
                {
                    'input': '5 5\n1 2\n2 3\n3 1\n3 4\n4 5',
                    'output': '2',
                },
            ],
            canonical_reference_solution="def solve() -> None:\n    import sys\n    sys.setrecursionlimit(10 ** 7)\n    input = sys.stdin.readline\n    n, m = map(int, input().split())\n    graph = [[] for _ in range(n)]\n    for idx in range(m):\n        u, v = map(int, input().split())\n        u -= 1\n        v -= 1\n        graph[u].append((v, idx))\n        graph[v].append((u, idx))\n    order = [-1] * n\n    low = [0] * n\n    timer = 0\n    bridges = 0\n\n    def dfs(node: int, parent_edge: int) -> None:\n        nonlocal timer, bridges\n        order[node] = low[node] = timer\n        timer += 1\n        for nxt, edge_id in graph[node]:\n            if edge_id == parent_edge:\n                continue\n            if order[nxt] == -1:\n                dfs(nxt, edge_id)\n                low[node] = min(low[node], low[nxt])\n                if order[node] < low[nxt]:\n                    bridges += 1\n            else:\n                low[node] = min(low[node], order[nxt])\n\n    for node in range(n):\n        if order[node] == -1:\n            dfs(node, -1)\n    print(bridges)\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
        problem(
            problem_id='algo-035-practice-p2',
            title='関節点・橋の検出 を素直に実装する / 2 ケースを連続して解く',
            problem_statement='2 ケース分の入力が続けて与えられる。それぞれについて、無向グラフが与えられる。橋の本数を求めよ。',
            input_format='1 行目に 2。\n続く 2 ケースについて:\n1 行目に N M。\n続く M 行に辺 u v。',
            output_format='各ケースの答えを順に出力する。',
            constraints='1 <= N, M <= 2 * 10^5\n2 ケースの合計でも同じ方針で処理すること。',
            examples=[
                {
                    'input': '2\n5 5\n1 2\n2 3\n3 1\n3 4\n4 5\n5 5\n1 2\n2 3\n3 1\n3 4\n4 5',
                    'output': '2\n2',
                },
            ],
            canonical_reference_solution="import io\nimport sys\nfrom contextlib import redirect_stdout\n\ndef solve_one() -> None:\n    import sys\n    sys.setrecursionlimit(10 ** 7)\n    input = sys.stdin.readline\n    n, m = map(int, input().split())\n    graph = [[] for _ in range(n)]\n    for idx in range(m):\n        u, v = map(int, input().split())\n        u -= 1\n        v -= 1\n        graph[u].append((v, idx))\n        graph[v].append((u, idx))\n    order = [-1] * n\n    low = [0] * n\n    timer = 0\n    bridges = 0\n\n    def dfs(node: int, parent_edge: int) -> None:\n        nonlocal timer, bridges\n        order[node] = low[node] = timer\n        timer += 1\n        for nxt, edge_id in graph[node]:\n            if edge_id == parent_edge:\n                continue\n            if order[nxt] == -1:\n                dfs(nxt, edge_id)\n                low[node] = min(low[node], low[nxt])\n                if order[node] < low[nxt]:\n                    bridges += 1\n            else:\n                low[node] = min(low[node], order[nxt])\n\n    for node in range(n):\n        if order[node] == -1:\n            dfs(node, -1)\n    print(bridges)\n\ndef solve() -> None:\n    t = 2\n    outputs = []\n    for _ in range(t):\n        buf = io.StringIO()\n        with redirect_stdout(buf):\n            solve_one()\n        outputs.append(buf.getvalue().rstrip('\\n'))\n    sys.stdout.write('\\n'.join(outputs))\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
        problem(
            problem_id='algo-035-practice-p3',
            title='関節点・橋の検出 を素直に実装する / 3 ケースを連続して解く',
            problem_statement='3 ケース分の入力が続けて与えられる。それぞれについて、無向グラフが与えられる。橋の本数を求めよ。',
            input_format='1 行目に 3。\n続く 3 ケースについて:\n1 行目に N M。\n続く M 行に辺 u v。',
            output_format='各ケースの答えを順に出力する。',
            constraints='1 <= N, M <= 2 * 10^5\n3 ケースの合計でも同じ方針で処理すること。',
            examples=[
                {
                    'input': '3\n5 5\n1 2\n2 3\n3 1\n3 4\n4 5\n5 5\n1 2\n2 3\n3 1\n3 4\n4 5\n5 5\n1 2\n2 3\n3 1\n3 4\n4 5',
                    'output': '2\n2\n2',
                },
            ],
            canonical_reference_solution="import io\nimport sys\nfrom contextlib import redirect_stdout\n\ndef solve_one() -> None:\n    import sys\n    sys.setrecursionlimit(10 ** 7)\n    input = sys.stdin.readline\n    n, m = map(int, input().split())\n    graph = [[] for _ in range(n)]\n    for idx in range(m):\n        u, v = map(int, input().split())\n        u -= 1\n        v -= 1\n        graph[u].append((v, idx))\n        graph[v].append((u, idx))\n    order = [-1] * n\n    low = [0] * n\n    timer = 0\n    bridges = 0\n\n    def dfs(node: int, parent_edge: int) -> None:\n        nonlocal timer, bridges\n        order[node] = low[node] = timer\n        timer += 1\n        for nxt, edge_id in graph[node]:\n            if edge_id == parent_edge:\n                continue\n            if order[nxt] == -1:\n                dfs(nxt, edge_id)\n                low[node] = min(low[node], low[nxt])\n                if order[node] < low[nxt]:\n                    bridges += 1\n            else:\n                low[node] = min(low[node], order[nxt])\n\n    for node in range(n):\n        if order[node] == -1:\n            dfs(node, -1)\n    print(bridges)\n\ndef solve() -> None:\n    t = 3\n    outputs = []\n    for _ in range(t):\n        buf = io.StringIO()\n        with redirect_stdout(buf):\n            solve_one()\n        outputs.append(buf.getvalue().rstrip('\\n'))\n    sys.stdout.write('\\n'.join(outputs))\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
