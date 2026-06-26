from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('foundation')

UNIT_BANK = unit_bank(
    unit_id='algo-031-practice',
    title='強連結成分分解（SCC） を素直に実装する',
    unit_kind='foundation',
    target_skill='強連結成分分解（SCC） を素直に実装する',
    concept_overview='強連結成分分解は、互いに行き来できる頂点どうしをひとかたまりにまとめる考え方です。グラフを縮約して構造を見やすくする基本を学びます。',
    problem_bank=[
        problem(
            problem_id='algo-031-practice-p1',
            title='強連結成分分解（SCC） を素直に実装する / 1 ケースをそのまま解く',
            problem_statement='有向グラフが与えられる。強連結成分の個数を求めよ。',
            input_format='1 行目に N M。\n続く M 行に辺 u v。',
            output_format='強連結成分の個数を出力する。',
            constraints='1 <= N, M <= 2 * 10^5',
            examples=[
                {
                    'input': '5 6\n1 2\n2 1\n2 3\n3 4\n4 3\n4 5',
                    'output': '3',
                },
            ],
            canonical_reference_solution="def solve() -> None:\n    import sys\n    sys.setrecursionlimit(10 ** 7)\n    input = sys.stdin.readline\n    n, m = map(int, input().split())\n    graph = [[] for _ in range(n)]\n    rev = [[] for _ in range(n)]\n    for _ in range(m):\n        u, v = map(int, input().split())\n        u -= 1\n        v -= 1\n        graph[u].append(v)\n        rev[v].append(u)\n    order = []\n    seen = [False] * n\n\n    def dfs(node: int) -> None:\n        seen[node] = True\n        for nxt in graph[node]:\n            if not seen[nxt]:\n                dfs(nxt)\n        order.append(node)\n\n    def rdfs(node: int) -> None:\n        seen[node] = True\n        for nxt in rev[node]:\n            if not seen[nxt]:\n                rdfs(nxt)\n\n    for node in range(n):\n        if not seen[node]:\n            dfs(node)\n    seen = [False] * n\n    count = 0\n    for node in reversed(order):\n        if seen[node]:\n            continue\n        rdfs(node)\n        count += 1\n    print(count)\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
        problem(
            problem_id='algo-031-practice-p2',
            title='強連結成分分解（SCC） を素直に実装する / 2 ケースを連続して解く',
            problem_statement='2 ケース分の入力が続けて与えられる。それぞれについて、有向グラフが与えられる。強連結成分の個数を求めよ。',
            input_format='1 行目に 2。\n続く 2 ケースについて:\n1 行目に N M。\n続く M 行に辺 u v。',
            output_format='各ケースの答えを順に出力する。',
            constraints='1 <= N, M <= 2 * 10^5\n2 ケースの合計でも同じ方針で処理すること。',
            examples=[
                {
                    'input': '2\n5 6\n1 2\n2 1\n2 3\n3 4\n4 3\n4 5\n5 6\n1 2\n2 1\n2 3\n3 4\n4 3\n4 5',
                    'output': '3\n3',
                },
            ],
            canonical_reference_solution="import io\nimport sys\nfrom contextlib import redirect_stdout\n\ndef solve_one() -> None:\n    import sys\n    sys.setrecursionlimit(10 ** 7)\n    input = sys.stdin.readline\n    n, m = map(int, input().split())\n    graph = [[] for _ in range(n)]\n    rev = [[] for _ in range(n)]\n    for _ in range(m):\n        u, v = map(int, input().split())\n        u -= 1\n        v -= 1\n        graph[u].append(v)\n        rev[v].append(u)\n    order = []\n    seen = [False] * n\n\n    def dfs(node: int) -> None:\n        seen[node] = True\n        for nxt in graph[node]:\n            if not seen[nxt]:\n                dfs(nxt)\n        order.append(node)\n\n    def rdfs(node: int) -> None:\n        seen[node] = True\n        for nxt in rev[node]:\n            if not seen[nxt]:\n                rdfs(nxt)\n\n    for node in range(n):\n        if not seen[node]:\n            dfs(node)\n    seen = [False] * n\n    count = 0\n    for node in reversed(order):\n        if seen[node]:\n            continue\n        rdfs(node)\n        count += 1\n    print(count)\n\ndef solve() -> None:\n    t = 2\n    outputs = []\n    for _ in range(t):\n        buf = io.StringIO()\n        with redirect_stdout(buf):\n            solve_one()\n        outputs.append(buf.getvalue().rstrip('\\n'))\n    sys.stdout.write('\\n'.join(outputs))\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
        problem(
            problem_id='algo-031-practice-p3',
            title='強連結成分分解（SCC） を素直に実装する / 3 ケースを連続して解く',
            problem_statement='3 ケース分の入力が続けて与えられる。それぞれについて、有向グラフが与えられる。強連結成分の個数を求めよ。',
            input_format='1 行目に 3。\n続く 3 ケースについて:\n1 行目に N M。\n続く M 行に辺 u v。',
            output_format='各ケースの答えを順に出力する。',
            constraints='1 <= N, M <= 2 * 10^5\n3 ケースの合計でも同じ方針で処理すること。',
            examples=[
                {
                    'input': '3\n5 6\n1 2\n2 1\n2 3\n3 4\n4 3\n4 5\n5 6\n1 2\n2 1\n2 3\n3 4\n4 3\n4 5\n5 6\n1 2\n2 1\n2 3\n3 4\n4 3\n4 5',
                    'output': '3\n3\n3',
                },
            ],
            canonical_reference_solution="import io\nimport sys\nfrom contextlib import redirect_stdout\n\ndef solve_one() -> None:\n    import sys\n    sys.setrecursionlimit(10 ** 7)\n    input = sys.stdin.readline\n    n, m = map(int, input().split())\n    graph = [[] for _ in range(n)]\n    rev = [[] for _ in range(n)]\n    for _ in range(m):\n        u, v = map(int, input().split())\n        u -= 1\n        v -= 1\n        graph[u].append(v)\n        rev[v].append(u)\n    order = []\n    seen = [False] * n\n\n    def dfs(node: int) -> None:\n        seen[node] = True\n        for nxt in graph[node]:\n            if not seen[nxt]:\n                dfs(nxt)\n        order.append(node)\n\n    def rdfs(node: int) -> None:\n        seen[node] = True\n        for nxt in rev[node]:\n            if not seen[nxt]:\n                rdfs(nxt)\n\n    for node in range(n):\n        if not seen[node]:\n            dfs(node)\n    seen = [False] * n\n    count = 0\n    for node in reversed(order):\n        if seen[node]:\n            continue\n        rdfs(node)\n        count += 1\n    print(count)\n\ndef solve() -> None:\n    t = 3\n    outputs = []\n    for _ in range(t):\n        buf = io.StringIO()\n        with redirect_stdout(buf):\n            solve_one()\n        outputs.append(buf.getvalue().rstrip('\\n'))\n    sys.stdout.write('\\n'.join(outputs))\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
