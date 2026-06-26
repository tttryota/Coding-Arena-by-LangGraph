from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('foundation')

UNIT_BANK = unit_bank(
    unit_id='algo-034-practice',
    title='木のオイラーツアー を素直に実装する',
    unit_kind='foundation',
    target_skill='木のオイラーツアー を素直に実装する',
    concept_overview='木のオイラーツアーでは、訪問順そのものだけでなく、各頂点の入時刻と出時刻も持てます。DFS の入る瞬間と戻る瞬間を時刻として記録する実装を確かめます。',
    problem_bank=[
        problem(
            problem_id='algo-034-practice-p1',
            title='木のオイラーツアー を素直に実装する / 各頂点の入時刻と出時刻を求める',
            problem_statement='根 1 の木が与えられる。深さ優先探索を行ったときの各頂点の入時刻 tin と出時刻 tout を求めよ。時刻は 1 から始め、頂点に入るたびに 1 進め、すべての子を見終えて頂点から出るときにも 1 進める。',
            input_format='1 行目に N。\n続く N-1 行に辺 u v。',
            output_format='各頂点について `tin tout` を 1 行ずつ出力する。',
            constraints='1 <= N <= 2 * 10^5',
            examples=[{'input': '4\n1 2\n1 3\n3 4', 'output': '1 8\n2 3\n4 7\n5 6'}],
            canonical_reference_solution="def solve() -> None:\n    import sys\n    sys.setrecursionlimit(10 ** 7)\n    input = sys.stdin.readline\n    n = int(input())\n    graph = [[] for _ in range(n)]\n    for _ in range(n - 1):\n        u, v = map(int, input().split())\n        u -= 1\n        v -= 1\n        graph[u].append(v)\n        graph[v].append(u)\n    for adj in graph:\n        adj.sort()\n    tin = [0] * n\n    tout = [0] * n\n    timer = 1\n\n    def dfs(node: int, parent: int) -> None:\n        nonlocal timer\n        tin[node] = timer\n        timer += 1\n        for nxt in graph[node]:\n            if nxt == parent:\n                continue\n            dfs(nxt, node)\n        tout[node] = timer\n        timer += 1\n\n    dfs(0, -1)\n    print('\\n'.join(f'{tin[i]} {tout[i]}' for i in range(n)))\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
