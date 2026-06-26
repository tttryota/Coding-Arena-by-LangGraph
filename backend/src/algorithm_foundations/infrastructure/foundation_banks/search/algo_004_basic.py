from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('foundation')

UNIT_BANK = unit_bank(
    unit_id='algo-004-basic',
    title='深さ優先探索（DFS） の基本',
    unit_kind='foundation',
    target_skill='深さ優先探索（DFS） の基本',
    concept_overview='深さ優先探索は、行けるところまで進んでから戻る形で状態や頂点をたどる解き方です。再帰やスタックで探索順を管理する基本を学びます。',
    problem_bank=[
        problem(
            problem_id='algo-004-basic-p1',
            title='深さ優先探索（DFS） の基本 / 頂点 1 から到達できる頂点数を求める',
            problem_statement='N 頂点 M 辺の無向グラフが与えられる。深さ優先探索を用いて、頂点 1 から到達できる頂点数を求めよ。',
            input_format='1 行目に N M。\n続く M 行に辺 u v。',
            output_format='頂点 1 から到達できる頂点数を出力する。',
            constraints='1 <= N <= 2 * 10^5\n0 <= M <= 2 * 10^5',
            examples=[{'input': '5 3\n1 2\n2 3\n4 5', 'output': '3'}],
            canonical_reference_solution="def solve() -> None:\n    import sys\n    input = sys.stdin.readline\n    n, m = map(int, input().split())\n    graph = [[] for _ in range(n)]\n    for _ in range(m):\n        u, v = map(int, input().split())\n        u -= 1\n        v -= 1\n        graph[u].append(v)\n        graph[v].append(u)\n    seen = [False] * n\n    seen[0] = True\n    stack = [0]\n    total = 0\n    while stack:\n        node = stack.pop()\n        total += 1\n        for nxt in graph[node]:\n            if seen[nxt]:\n                continue\n            seen[nxt] = True\n            stack.append(nxt)\n    print(total)\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
