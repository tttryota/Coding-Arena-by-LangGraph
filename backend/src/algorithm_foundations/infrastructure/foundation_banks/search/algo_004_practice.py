from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('foundation')

UNIT_BANK = unit_bank(
    unit_id='algo-004-practice',
    title='深さ優先探索（DFS） を素直に実装する',
    unit_kind='foundation',
    target_skill='深さ優先探索（DFS） を素直に実装する',
    concept_overview='DFS を 1 回で終えず、未訪問頂点から何度も始めると連結成分を数えられます。ここではグラフ全体を DFS で塗り分けます。',
    problem_bank=[
        problem(
            problem_id='algo-004-practice-p1',
            title='深さ優先探索（DFS） を素直に実装する / 連結成分数を求める',
            problem_statement='N 頂点 M 辺の無向グラフが与えられる。深さ優先探索を用いて、このグラフの連結成分数を求めよ。',
            input_format='1 行目に N M。\n続く M 行に辺 u v。',
            output_format='連結成分数を出力する。',
            constraints='1 <= N <= 2 * 10^5\n0 <= M <= 2 * 10^5',
            examples=[{'input': '5 3\n1 2\n2 3\n4 5', 'output': '2'}],
            canonical_reference_solution="def solve() -> None:\n    import sys\n    input = sys.stdin.readline\n    n, m = map(int, input().split())\n    graph = [[] for _ in range(n)]\n    for _ in range(m):\n        u, v = map(int, input().split())\n        u -= 1\n        v -= 1\n        graph[u].append(v)\n        graph[v].append(u)\n    seen = [False] * n\n    components = 0\n    for start in range(n):\n        if seen[start]:\n            continue\n        components += 1\n        seen[start] = True\n        stack = [start]\n        while stack:\n            node = stack.pop()\n            for nxt in graph[node]:\n                if seen[nxt]:\n                    continue\n                seen[nxt] = True\n                stack.append(nxt)\n    print(components)\n\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
