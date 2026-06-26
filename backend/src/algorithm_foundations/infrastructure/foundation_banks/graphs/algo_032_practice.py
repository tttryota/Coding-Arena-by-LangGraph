from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('foundation')

UNIT_BANK = unit_bank(
    unit_id='algo-032-practice',
    title='二部グラフ判定 を素直に実装する',
    unit_kind='foundation',
    target_skill='二部グラフ判定 を素直に実装する',
    concept_overview='二部グラフ判定では、判定だけでなく実際の 2 色分けも復元できます。BFS で塗った色を最後にそのまま出力する流れを確かめます。',
    problem_bank=[
        problem(
            problem_id='algo-032-practice-p1',
            title='二部グラフ判定 を素直に実装する / 二部グラフなら 2 色分けを 1 つ出力する',
            problem_statement='N 頂点 M 辺の無向グラフが与えられる。二部グラフなら Yes と各頂点の色 1 または 2 を出力し、そうでなければ No を出力せよ。',
            input_format='1 行目に N M。\n続く M 行に辺 u v。',
            output_format='二部グラフなら 1 行目に Yes、2 行目に N 個の色を出力する。そうでなければ 1 行目に No を出力する。',
            constraints='1 <= N <= 2 * 10^5\n0 <= M <= 2 * 10^5',
            examples=[{'input': '4 4\n1 2\n2 3\n3 4\n4 1', 'output': 'Yes\n1 2 1 2'}],
            canonical_reference_solution="from collections import deque\n\ndef solve() -> None:\n    import sys\n    input = sys.stdin.readline\n    n, m = map(int, input().split())\n    graph = [[] for _ in range(n)]\n    for _ in range(m):\n        u, v = map(int, input().split())\n        u -= 1\n        v -= 1\n        graph[u].append(v)\n        graph[v].append(u)\n    color = [-1] * n\n    for start in range(n):\n        if color[start] != -1:\n            continue\n        color[start] = 0\n        dq = deque([start])\n        while dq:\n            node = dq.popleft()\n            for nxt in graph[node]:\n                if color[nxt] == -1:\n                    color[nxt] = color[node] ^ 1\n                    dq.append(nxt)\n                elif color[nxt] == color[node]:\n                    print('No')\n                    return\n    print('Yes')\n    print(*[c + 1 for c in color])\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
