from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('integration')

UNIT_BANK = unit_bank(
    unit_id='algo-004-integration',
    title='深さ優先探索（DFS） の総合演習',
    unit_kind='integration',
    target_skill='深さ優先探索（DFS） の総合演習',
    concept_overview='DFS では、親へ戻る辺を除いて、すでに訪問済みの頂点へ戻る辺が見つかると閉路を検出できます。ここでは無向グラフにサイクルがあるかを判定します。',
    problem_bank=[
        problem(
            problem_id='algo-004-integration-p1',
            title='深さ優先探索（DFS） の総合演習 / 無向グラフに閉路があるか判定する',
            problem_statement='N 頂点 M 辺の単純無向グラフが与えられる。深さ優先探索を用いて、このグラフに閉路が存在するか判定せよ。',
            input_format='1 行目に N M。\n続く M 行に辺 u v。',
            output_format='閉路があるなら Yes、なければ No を出力する。',
            constraints='1 <= N <= 2 * 10^5\n0 <= M <= 2 * 10^5\n1 <= u < v <= N\n同じ辺は 2 回以上現れない',
            examples=[{'input': '4 4\n1 2\n2 3\n3 1\n3 4', 'output': 'Yes'}],
            canonical_reference_solution="def solve() -> None:\n    import sys\n    input = sys.stdin.readline\n    n, m = map(int, input().split())\n    graph = [[] for _ in range(n)]\n    for _ in range(m):\n        u, v = map(int, input().split())\n        u -= 1\n        v -= 1\n        graph[u].append(v)\n        graph[v].append(u)\n    seen = [False] * n\n    for start in range(n):\n        if seen[start]:\n            continue\n        seen[start] = True\n        stack = [(start, -1)]\n        while stack:\n            node, parent = stack.pop()\n            for nxt in graph[node]:\n                if nxt == parent:\n                    continue\n                if seen[nxt]:\n                    print('Yes')\n                    return\n                seen[nxt] = True\n                stack.append((nxt, node))\n    print('No')\n\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
