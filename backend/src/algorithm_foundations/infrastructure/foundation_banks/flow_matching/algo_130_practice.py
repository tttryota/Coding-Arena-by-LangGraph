from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('foundation')

UNIT_BANK = unit_bank(
    unit_id='algo-130-practice',
    title='Hopcroft-Karp法 を素直に実装する',
    unit_kind='foundation',
    target_skill='Hopcroft-Karp法 を素直に実装する',
    concept_overview='Hopcroft-Karp 法で最大マッチングを求めたあと、Kőnig の定理を使うと最小頂点被覆も復元できます。ここでは最小頂点被覆を 1 つ出力します。',
    problem_bank=[
        problem(
            problem_id='algo-130-practice-p1',
            title='Hopcroft-Karp法 を素直に実装する / 最小頂点被覆を 1 つ出力する',
            problem_statement='左側 N 頂点、右側 M 頂点の二部グラフが与えられる。最小頂点被覆を 1 つ求めよ。出力は、選んだ左側頂点と右側頂点の集合で表す。',
            input_format='1 行目に N M E。\n続く E 行に u v。',
            output_format='1 行目に選んだ左側頂点数 A と右側頂点数 B、2 行目に左側頂点、3 行目に右側頂点を空白区切りで出力する。空なら空行でもよい。',
            constraints='1 <= N, M <= 2 * 10^5\n1 <= E <= 5 * 10^5\n1 <= u <= N\n1 <= v <= M',
            examples=[{'input': '3 3 4\n1 1\n1 2\n2 2\n3 3', 'output': '3 0\n1 2 3'}],
            canonical_reference_solution="from collections import deque\n\n\ndef solve() -> None:\n    import sys\n    sys.setrecursionlimit(1_000_000)\n    input = sys.stdin.readline\n    n, m, e = map(int, input().split())\n    graph = [[] for _ in range(n)]\n    for _ in range(e):\n        u, v = map(int, input().split())\n        graph[u - 1].append(v - 1)\n    match_l = [-1] * n\n    match_r = [-1] * m\n    dist = [0] * n\n\n    def bfs() -> bool:\n        dq = deque()\n        found = False\n        for v in range(n):\n            if match_l[v] == -1:\n                dist[v] = 0\n                dq.append(v)\n            else:\n                dist[v] = -1\n        while dq:\n            v = dq.popleft()\n            for to in graph[v]:\n                mate = match_r[to]\n                if mate == -1:\n                    found = True\n                elif dist[mate] == -1:\n                    dist[mate] = dist[v] + 1\n                    dq.append(mate)\n        return found\n\n    def dfs(v: int) -> bool:\n        for to in graph[v]:\n            mate = match_r[to]\n            if mate == -1 or (dist[mate] == dist[v] + 1 and dfs(mate)):\n                match_l[v] = to\n                match_r[to] = v\n                return True\n        dist[v] = -1\n        return False\n\n    while bfs():\n        for v in range(n):\n            if match_l[v] == -1:\n                dfs(v)\n\n    vis_l = [False] * n\n    vis_r = [False] * m\n    dq = deque(v for v in range(n) if match_l[v] == -1)\n    for v in dq:\n        vis_l[v] = True\n    while dq:\n        v = dq.popleft()\n        for to in graph[v]:\n            if vis_r[to] or match_l[v] == to:\n                continue\n            vis_r[to] = True\n            mate = match_r[to]\n            if mate != -1 and not vis_l[mate]:\n                vis_l[mate] = True\n                dq.append(mate)\n    left_cover = [i + 1 for i in range(n) if not vis_l[i]]\n    right_cover = [i + 1 for i in range(m) if vis_r[i]]\n    print(len(left_cover), len(right_cover))\n    print(*left_cover)\n    print(*right_cover)\n\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
