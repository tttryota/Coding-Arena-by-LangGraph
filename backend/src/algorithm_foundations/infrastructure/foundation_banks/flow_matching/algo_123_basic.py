from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('foundation')

UNIT_BANK = unit_bank(
    unit_id='algo-123-basic',
    title='最大フロー（Ford-Fulkerson法） の基本',
    unit_kind='foundation',
    target_skill='最大フロー（Ford-Fulkerson法） の基本',
    concept_overview='最大流・マッチングは、通せる量や組み合わせをグラフの辺として表し、制約つきでどれだけ流せるか・結べるかを考える知識です。問題をネットワークに置き換える基本を学びます。',
    problem_bank=[
        problem(
            problem_id='algo-123-basic-p1',
            title='最大フロー（Ford-Fulkerson法） の基本 / 1 ケースをそのまま解く',
            problem_statement='容量付き有向グラフが与えられる。頂点 1 から頂点 N への最大フローを Ford-Fulkerson 法で求めよ。',
            input_format='1 行目に N M。\n続く M 行に u v c。',
            output_format='最大フロー値を出力する。',
            constraints='2 <= N <= 100\n1 <= M <= 1000\n1 <= c <= 10^9',
            examples=[
                {
                    'input': '4 5\n1 2 2\n1 3 1\n2 3 1\n2 4 1\n3 4 2',
                    'output': '3',
                },
            ],
            canonical_reference_solution="def solve() -> None:\n    import sys\n    sys.setrecursionlimit(10 ** 7)\n    input = sys.stdin.readline\n    n, m = map(int, input().split())\n    graph = [[] for _ in range(n)]\n\n    def add_edge(u: int, v: int, cap: int) -> None:\n        graph[u].append([v, cap, len(graph[v])])\n        graph[v].append([u, 0, len(graph[u]) - 1])\n\n    for _ in range(m):\n        u, v, c = map(int, input().split())\n        add_edge(u - 1, v - 1, c)\n\n    def dfs(node: int, goal: int, flow: int, seen: list[bool]) -> int:\n        if node == goal:\n            return flow\n        seen[node] = True\n        for edge in graph[node]:\n            nxt, cap, rev = edge\n            if cap == 0 or seen[nxt]:\n                continue\n            pushed = dfs(nxt, goal, min(flow, cap), seen)\n            if pushed:\n                edge[1] -= pushed\n                graph[nxt][rev][1] += pushed\n                return pushed\n        return 0\n\n    ans = 0\n    while True:\n        pushed = dfs(0, n - 1, 10 ** 18, [False] * n)\n        if pushed == 0:\n            break\n        ans += pushed\n    print(ans)\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
        problem(
            problem_id='algo-123-basic-p2',
            title='最大フロー（Ford-Fulkerson法） の基本 / 2 ケースを連続して解く',
            problem_statement='2 ケース分の入力が続けて与えられる。それぞれについて、容量付き有向グラフが与えられる。頂点 1 から頂点 N への最大フローを Ford-Fulkerson 法で求めよ。',
            input_format='1 行目に 2。\n続く 2 ケースについて:\n1 行目に N M。\n続く M 行に u v c。',
            output_format='各ケースの答えを順に出力する。',
            constraints='2 <= N <= 100\n1 <= M <= 1000\n1 <= c <= 10^9\n2 ケースの合計でも同じ方針で処理すること。',
            examples=[
                {
                    'input': '2\n4 5\n1 2 2\n1 3 1\n2 3 1\n2 4 1\n3 4 2\n4 5\n1 2 2\n1 3 1\n2 3 1\n2 4 1\n3 4 2',
                    'output': '3\n3',
                },
            ],
            canonical_reference_solution="import io\nimport sys\nfrom contextlib import redirect_stdout\n\ndef solve_one() -> None:\n    import sys\n    sys.setrecursionlimit(10 ** 7)\n    input = sys.stdin.readline\n    n, m = map(int, input().split())\n    graph = [[] for _ in range(n)]\n\n    def add_edge(u: int, v: int, cap: int) -> None:\n        graph[u].append([v, cap, len(graph[v])])\n        graph[v].append([u, 0, len(graph[u]) - 1])\n\n    for _ in range(m):\n        u, v, c = map(int, input().split())\n        add_edge(u - 1, v - 1, c)\n\n    def dfs(node: int, goal: int, flow: int, seen: list[bool]) -> int:\n        if node == goal:\n            return flow\n        seen[node] = True\n        for edge in graph[node]:\n            nxt, cap, rev = edge\n            if cap == 0 or seen[nxt]:\n                continue\n            pushed = dfs(nxt, goal, min(flow, cap), seen)\n            if pushed:\n                edge[1] -= pushed\n                graph[nxt][rev][1] += pushed\n                return pushed\n        return 0\n\n    ans = 0\n    while True:\n        pushed = dfs(0, n - 1, 10 ** 18, [False] * n)\n        if pushed == 0:\n            break\n        ans += pushed\n    print(ans)\n\ndef solve() -> None:\n    t = 2\n    outputs = []\n    for _ in range(t):\n        buf = io.StringIO()\n        with redirect_stdout(buf):\n            solve_one()\n        outputs.append(buf.getvalue().rstrip('\\n'))\n    sys.stdout.write('\\n'.join(outputs))\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
        problem(
            problem_id='algo-123-basic-p3',
            title='最大フロー（Ford-Fulkerson法） の基本 / 3 ケースを連続して解く',
            problem_statement='3 ケース分の入力が続けて与えられる。それぞれについて、容量付き有向グラフが与えられる。頂点 1 から頂点 N への最大フローを Ford-Fulkerson 法で求めよ。',
            input_format='1 行目に 3。\n続く 3 ケースについて:\n1 行目に N M。\n続く M 行に u v c。',
            output_format='各ケースの答えを順に出力する。',
            constraints='2 <= N <= 100\n1 <= M <= 1000\n1 <= c <= 10^9\n3 ケースの合計でも同じ方針で処理すること。',
            examples=[
                {
                    'input': '3\n4 5\n1 2 2\n1 3 1\n2 3 1\n2 4 1\n3 4 2\n4 5\n1 2 2\n1 3 1\n2 3 1\n2 4 1\n3 4 2\n4 5\n1 2 2\n1 3 1\n2 3 1\n2 4 1\n3 4 2',
                    'output': '3\n3\n3',
                },
            ],
            canonical_reference_solution="import io\nimport sys\nfrom contextlib import redirect_stdout\n\ndef solve_one() -> None:\n    import sys\n    sys.setrecursionlimit(10 ** 7)\n    input = sys.stdin.readline\n    n, m = map(int, input().split())\n    graph = [[] for _ in range(n)]\n\n    def add_edge(u: int, v: int, cap: int) -> None:\n        graph[u].append([v, cap, len(graph[v])])\n        graph[v].append([u, 0, len(graph[u]) - 1])\n\n    for _ in range(m):\n        u, v, c = map(int, input().split())\n        add_edge(u - 1, v - 1, c)\n\n    def dfs(node: int, goal: int, flow: int, seen: list[bool]) -> int:\n        if node == goal:\n            return flow\n        seen[node] = True\n        for edge in graph[node]:\n            nxt, cap, rev = edge\n            if cap == 0 or seen[nxt]:\n                continue\n            pushed = dfs(nxt, goal, min(flow, cap), seen)\n            if pushed:\n                edge[1] -= pushed\n                graph[nxt][rev][1] += pushed\n                return pushed\n        return 0\n\n    ans = 0\n    while True:\n        pushed = dfs(0, n - 1, 10 ** 18, [False] * n)\n        if pushed == 0:\n            break\n        ans += pushed\n    print(ans)\n\ndef solve() -> None:\n    t = 3\n    outputs = []\n    for _ in range(t):\n        buf = io.StringIO()\n        with redirect_stdout(buf):\n            solve_one()\n        outputs.append(buf.getvalue().rstrip('\\n'))\n    sys.stdout.write('\\n'.join(outputs))\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
