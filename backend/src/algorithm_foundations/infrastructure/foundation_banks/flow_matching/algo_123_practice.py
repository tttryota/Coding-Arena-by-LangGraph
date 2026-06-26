from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('foundation')

UNIT_BANK = unit_bank(
    unit_id='algo-123-practice',
    title='最大フロー（Ford-Fulkerson法） を素直に実装する',
    unit_kind='foundation',
    target_skill='最大フロー（Ford-Fulkerson法） を素直に実装する',
    concept_overview='最大流は二部マッチングのような組み合わせ問題にも変換できます。ここでは二部グラフの最大マッチング数を flow ネットワークとして求めます。',
    problem_bank=[
        problem(
            problem_id='algo-123-practice-p1',
            title='最大フロー（Ford-Fulkerson法） を素直に実装する / 二部グラフの最大マッチング数を求める',
            problem_statement='左側に L 頂点、右側に R 頂点を持つ二部グラフが与えられる。各辺は左頂点 1 個と右頂点 1 個を結ぶ。Ford-Fulkerson 法を用いて最大マッチング数を求めよ。',
            input_format='1 行目に L R M。\n続く M 行に u v。',
            output_format='最大マッチング数を出力する。',
            constraints='1 <= L, R <= 100\n0 <= M <= 1000\n1 <= u <= L\n1 <= v <= R',
            examples=[{'input': '3 3 4\n1 1\n1 2\n2 2\n3 3', 'output': '3'}],
            canonical_reference_solution="def solve() -> None:\n    import sys\n    sys.setrecursionlimit(10 ** 7)\n    input = sys.stdin.readline\n    left_n, right_n, m = map(int, input().split())\n    n = left_n + right_n + 2\n    source = 0\n    sink = n - 1\n    graph = [[] for _ in range(n)]\n\n    def add_edge(u: int, v: int, cap: int) -> None:\n        graph[u].append([v, cap, len(graph[v])])\n        graph[v].append([u, 0, len(graph[u]) - 1])\n\n    for u in range(1, left_n + 1):\n        add_edge(source, u, 1)\n    for v in range(1, right_n + 1):\n        add_edge(left_n + v, sink, 1)\n    for _ in range(m):\n        u, v = map(int, input().split())\n        add_edge(u, left_n + v, 1)\n\n    def dfs(node: int, goal: int, flow: int, seen: list[bool]) -> int:\n        if node == goal:\n            return flow\n        seen[node] = True\n        for edge in graph[node]:\n            nxt, cap, rev = edge\n            if cap == 0 or seen[nxt]:\n                continue\n            pushed = dfs(nxt, goal, min(flow, cap), seen)\n            if pushed:\n                edge[1] -= pushed\n                graph[nxt][rev][1] += pushed\n                return pushed\n        return 0\n\n    ans = 0\n    while True:\n        pushed = dfs(source, sink, 1, [False] * n)\n        if pushed == 0:\n            break\n        ans += pushed\n    print(ans)\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
