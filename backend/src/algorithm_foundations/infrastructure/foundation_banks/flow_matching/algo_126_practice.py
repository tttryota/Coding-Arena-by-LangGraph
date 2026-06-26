from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('foundation')

UNIT_BANK = unit_bank(
    unit_id='algo-126-practice',
    title='二部マッチング を素直に実装する',
    unit_kind='foundation',
    target_skill='二部マッチング を素直に実装する',
    concept_overview='最大マッチングを求めたあと、未マッチ左頂点から交互路で到達できる頂点をたどると、Kőnig の定理により最小頂点被覆を復元できます。ここでは最小頂点被覆を 1 つ出力します。',
    problem_bank=[
        problem(
            problem_id='algo-126-practice-p1',
            title='二部マッチング を素直に実装する / 最小頂点被覆を 1 つ出力する',
            problem_statement='左側 N 頂点、右側 M 頂点の二部グラフが与えられる。最小頂点被覆を 1 つ求めよ。出力は、選んだ左側頂点と右側頂点の集合で表す。',
            input_format='1 行目に N M E。\n続く E 行に u v。',
            output_format='1 行目に選んだ左側頂点数 A と右側頂点数 B、2 行目に左側頂点、3 行目に右側頂点を空白区切りで出力する。空なら空行でもよい。',
            constraints='1 <= N, M <= 200\n1 <= E <= 2 * 10^4\n1 <= u <= N\n1 <= v <= M',
            examples=[{'input': '4 3 5\n1 1\n2 1\n2 2\n3 2\n4 3', 'output': '1 2\n4\n1 2'}],
            canonical_reference_solution="from collections import deque\n\n\ndef solve() -> None:\n    import sys\n    input = sys.stdin.readline\n    n, m, e = map(int, input().split())\n    graph = [[] for _ in range(n)]\n    for _ in range(e):\n        u, v = map(int, input().split())\n        graph[u - 1].append(v - 1)\n    match_l = [-1] * n\n    match_r = [-1] * m\n\n    def dfs(v: int, seen: list[bool]) -> bool:\n        for to in graph[v]:\n            if seen[to]:\n                continue\n            seen[to] = True\n            mate = match_r[to]\n            if mate == -1 or dfs(mate, seen):\n                match_l[v] = to\n                match_r[to] = v\n                return True\n        return False\n\n    for v in range(n):\n        if match_l[v] == -1:\n            dfs(v, [False] * m)\n\n    vis_l = [False] * n\n    vis_r = [False] * m\n    dq = deque()\n    for v in range(n):\n        if match_l[v] == -1:\n            vis_l[v] = True\n            dq.append(v)\n    while dq:\n        v = dq.popleft()\n        for to in graph[v]:\n            if match_l[v] == to or vis_r[to]:\n                continue\n            vis_r[to] = True\n            mate = match_r[to]\n            if mate != -1 and not vis_l[mate]:\n                vis_l[mate] = True\n                dq.append(mate)\n\n    left_cover = [i + 1 for i in range(n) if not vis_l[i]]\n    right_cover = [i + 1 for i in range(m) if vis_r[i]]\n    print(len(left_cover), len(right_cover))\n    print(*left_cover)\n    print(*right_cover)\n\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
