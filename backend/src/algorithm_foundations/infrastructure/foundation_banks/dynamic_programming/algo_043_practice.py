from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('foundation')

UNIT_BANK = unit_bank(
    unit_id='algo-043-practice',
    title='木DP を素直に実装する',
    unit_kind='foundation',
    target_skill='木DP を素直に実装する',
    concept_overview='木DP は、頂点に重みが付いても同じ 2 状態で集約できます。ここでは「取る/取らない」の人数ではなく、重み和を最大化します。',
    problem_bank=[
        problem(
            problem_id='algo-043-practice-p1',
            title='木DP を素直に実装する / 重み付き最大独立集合の重み和を求める',
            problem_statement='各頂点 i に重み w_i が付いた木が与えられる。隣接頂点を同時に選ばないように頂点を選ぶとき、選んだ頂点の重み和の最大値を求めよ。',
            input_format='1 行目に N。\n2 行目に w_1..w_N。\n続く N-1 行に辺 u v。',
            output_format='最大の重み和を出力する。',
            constraints='1 <= N <= 2 * 10^5\n1 <= w_i <= 10^9',
            examples=[{'input': '5\n5 2 4 3 6\n1 2\n1 3\n3 4\n3 5', 'output': '14'}],
            canonical_reference_solution="def solve() -> None:\n    import sys\n    sys.setrecursionlimit(10 ** 7)\n    input = sys.stdin.readline\n    n = int(input())\n    weights = list(map(int, input().split()))\n    graph = [[] for _ in range(n)]\n    for _ in range(n - 1):\n        u, v = map(int, input().split())\n        u -= 1\n        v -= 1\n        graph[u].append(v)\n        graph[v].append(u)\n\n    def dfs(node: int, parent: int) -> tuple[int, int]:\n        take = weights[node]\n        skip = 0\n        for nxt in graph[node]:\n            if nxt == parent:\n                continue\n            child_take, child_skip = dfs(nxt, node)\n            take += child_skip\n            skip += max(child_take, child_skip)\n        return take, skip\n\n    take, skip = dfs(0, -1)\n    print(max(take, skip))\n\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
