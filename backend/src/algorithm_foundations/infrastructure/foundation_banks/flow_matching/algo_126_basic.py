from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('foundation')

UNIT_BANK = unit_bank(
    unit_id='algo-126-basic',
    title='二部マッチング の基本',
    unit_kind='foundation',
    target_skill='二部マッチング の基本',
    concept_overview='二部マッチングは、左側と右側の頂点を重ならないように結ぶ最大本数を求める知識です。まずは増加道 DFS で最大マッチング数を求め、左右それぞれの対応を配列で管理する基本を学びます。',
    problem_bank=[
        problem(
            problem_id='algo-126-basic-p1',
            title='二部マッチング の基本 / 最大マッチング数を求める',
            problem_statement='左側 N 頂点、右側 M 頂点の二部グラフが与えられる。最大マッチング数を求めよ。',
            input_format='1 行目に N M E。\n続く E 行に u v。',
            output_format='最大マッチング数を出力する。',
            constraints='1 <= N, M <= 200\n1 <= E <= 2 * 10^4\n1 <= u <= N\n1 <= v <= M',
            examples=[{'input': '2 2 3\n1 1\n1 2\n2 2', 'output': '2'}],
            canonical_reference_solution="def solve() -> None:\n    import sys\n    input = sys.stdin.readline\n    n, m, e = map(int, input().split())\n    graph = [[] for _ in range(n)]\n    for _ in range(e):\n        u, v = map(int, input().split())\n        graph[u - 1].append(v - 1)\n    match_l = [-1] * n\n    match_r = [-1] * m\n\n    def dfs(v: int, seen: list[bool]) -> bool:\n        for to in graph[v]:\n            if seen[to]:\n                continue\n            seen[to] = True\n            mate = match_r[to]\n            if mate == -1 or dfs(mate, seen):\n                match_l[v] = to\n                match_r[to] = v\n                return True\n        return False\n\n    ans = 0\n    for v in range(n):\n        if match_l[v] == -1 and dfs(v, [False] * m):\n            ans += 1\n    print(ans)\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
