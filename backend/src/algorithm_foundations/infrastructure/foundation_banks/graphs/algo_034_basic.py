from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('foundation')

UNIT_BANK = unit_bank(
    unit_id='algo-034-basic',
    title='木のオイラーツアー の基本',
    unit_kind='foundation',
    target_skill='木のオイラーツアー の基本',
    concept_overview='オイラー路・オイラー閉路は、辺をちょうど 1 回ずつ通る道が作れるかを考える知識です。次数や通り方の条件を整理する基本を学びます。',
    problem_bank=[
        problem(
            problem_id='algo-034-basic-p1',
            title='木のオイラーツアー の基本 / 1 ケースをそのまま解く',
            problem_statement='根 1 の木が与えられる。深さ優先探索によるオイラーツアーの訪問順を出力せよ。',
            input_format='1 行目に N。\n続く N-1 行に辺 u v。',
            output_format='訪問順を空白区切りで出力する。',
            constraints='1 <= N <= 2 * 10^5',
            examples=[
                {
                    'input': '4\n1 2\n1 3\n3 4',
                    'output': '1 2 1 3 4 3 1',
                },
            ],
            canonical_reference_solution="def solve() -> None:\n    import sys\n    sys.setrecursionlimit(10 ** 7)\n    input = sys.stdin.readline\n    n = int(input())\n    graph = [[] for _ in range(n)]\n    for _ in range(n - 1):\n        u, v = map(int, input().split())\n        u -= 1\n        v -= 1\n        graph[u].append(v)\n        graph[v].append(u)\n    for adj in graph:\n        adj.sort()\n    order = []\n\n    def dfs(node: int, parent: int) -> None:\n        order.append(node + 1)\n        for nxt in graph[node]:\n            if nxt == parent:\n                continue\n            dfs(nxt, node)\n            order.append(node + 1)\n\n    dfs(0, -1)\n    print(*order)\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
        problem(
            problem_id='algo-034-basic-p2',
            title='木のオイラーツアー の基本 / 2 ケースを連続して解く',
            problem_statement='2 ケース分の入力が続けて与えられる。それぞれについて、根 1 の木が与えられる。深さ優先探索によるオイラーツアーの訪問順を出力せよ。',
            input_format='1 行目に 2。\n続く 2 ケースについて:\n1 行目に N。\n続く N-1 行に辺 u v。',
            output_format='各ケースの答えを順に出力する。',
            constraints='1 <= N <= 2 * 10^5\n2 ケースの合計でも同じ方針で処理すること。',
            examples=[
                {
                    'input': '2\n4\n1 2\n1 3\n3 4\n4\n1 2\n1 3\n3 4',
                    'output': '1 2 1 3 4 3 1\n1 2 1 3 4 3 1',
                },
            ],
            canonical_reference_solution="import io\nimport sys\nfrom contextlib import redirect_stdout\n\ndef solve_one() -> None:\n    import sys\n    sys.setrecursionlimit(10 ** 7)\n    input = sys.stdin.readline\n    n = int(input())\n    graph = [[] for _ in range(n)]\n    for _ in range(n - 1):\n        u, v = map(int, input().split())\n        u -= 1\n        v -= 1\n        graph[u].append(v)\n        graph[v].append(u)\n    for adj in graph:\n        adj.sort()\n    order = []\n\n    def dfs(node: int, parent: int) -> None:\n        order.append(node + 1)\n        for nxt in graph[node]:\n            if nxt == parent:\n                continue\n            dfs(nxt, node)\n            order.append(node + 1)\n\n    dfs(0, -1)\n    print(*order)\n\ndef solve() -> None:\n    t = 2\n    outputs = []\n    for _ in range(t):\n        buf = io.StringIO()\n        with redirect_stdout(buf):\n            solve_one()\n        outputs.append(buf.getvalue().rstrip('\\n'))\n    sys.stdout.write('\\n'.join(outputs))\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
        problem(
            problem_id='algo-034-basic-p3',
            title='木のオイラーツアー の基本 / 3 ケースを連続して解く',
            problem_statement='3 ケース分の入力が続けて与えられる。それぞれについて、根 1 の木が与えられる。深さ優先探索によるオイラーツアーの訪問順を出力せよ。',
            input_format='1 行目に 3。\n続く 3 ケースについて:\n1 行目に N。\n続く N-1 行に辺 u v。',
            output_format='各ケースの答えを順に出力する。',
            constraints='1 <= N <= 2 * 10^5\n3 ケースの合計でも同じ方針で処理すること。',
            examples=[
                {
                    'input': '3\n4\n1 2\n1 3\n3 4\n4\n1 2\n1 3\n3 4\n4\n1 2\n1 3\n3 4',
                    'output': '1 2 1 3 4 3 1\n1 2 1 3 4 3 1\n1 2 1 3 4 3 1',
                },
            ],
            canonical_reference_solution="import io\nimport sys\nfrom contextlib import redirect_stdout\n\ndef solve_one() -> None:\n    import sys\n    sys.setrecursionlimit(10 ** 7)\n    input = sys.stdin.readline\n    n = int(input())\n    graph = [[] for _ in range(n)]\n    for _ in range(n - 1):\n        u, v = map(int, input().split())\n        u -= 1\n        v -= 1\n        graph[u].append(v)\n        graph[v].append(u)\n    for adj in graph:\n        adj.sort()\n    order = []\n\n    def dfs(node: int, parent: int) -> None:\n        order.append(node + 1)\n        for nxt in graph[node]:\n            if nxt == parent:\n                continue\n            dfs(nxt, node)\n            order.append(node + 1)\n\n    dfs(0, -1)\n    print(*order)\n\ndef solve() -> None:\n    t = 3\n    outputs = []\n    for _ in range(t):\n        buf = io.StringIO()\n        with redirect_stdout(buf):\n            solve_one()\n        outputs.append(buf.getvalue().rstrip('\\n'))\n    sys.stdout.write('\\n'.join(outputs))\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
