from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('foundation')

UNIT_BANK = unit_bank(
    unit_id='algo-067-basic',
    title='重心分解 の基本',
    unit_kind='foundation',
    target_skill='重心分解 の基本',
    concept_overview='重心分解は、木を「どこで切っても大きすぎる部分木が残らない」頂点で分けて再帰する知識です。まずは距離ちょうど K の頂点対を数える問題で、重心をまたぐ寄与の数え方を確認します。',
    problem_bank=[
        problem(
            problem_id='algo-067-basic-p1',
            title='重心分解 の基本 / 距離がちょうど K の頂点対を数える',
            problem_statement='N 頂点の木と整数 K が与えられる。距離がちょうど K である unordered pair (u, v) の個数を求めよ。',
            input_format='1 行目に N K。\n続く N-1 行に辺 u v。',
            output_format='条件を満たす頂点対の個数を出力する。',
            constraints='1 <= N <= 2 * 10^5\n1 <= K < N',
            examples=[{'input': '5 2\n1 2\n2 3\n3 4\n3 5', 'output': '4'}],
            canonical_reference_solution="def solve() -> None:\n    import sys\n    input = sys.stdin.readline\n    sys.setrecursionlimit(1 << 25)\n    n, k = map(int, input().split())\n    graph = [[] for _ in range(n)]\n    for _ in range(n - 1):\n        u, v = map(int, input().split())\n        u -= 1\n        v -= 1\n        graph[u].append(v)\n        graph[v].append(u)\n\n    removed = [False] * n\n    size = [0] * n\n    answer = 0\n\n    def calc_size(v: int, p: int) -> int:\n        size[v] = 1\n        for to in graph[v]:\n            if to == p or removed[to]:\n                continue\n            size[v] += calc_size(to, v)\n        return size[v]\n\n    def find_centroid(v: int, p: int, total: int) -> int:\n        for to in graph[v]:\n            if to == p or removed[to]:\n                continue\n            if size[to] * 2 > total:\n                return find_centroid(to, v, total)\n        return v\n\n    def collect_depths(v: int, p: int, depth: int, out: list[int]) -> None:\n        if depth > k:\n            return\n        out.append(depth)\n        for to in graph[v]:\n            if to == p or removed[to]:\n                continue\n            collect_depths(to, v, depth + 1, out)\n\n    def decompose(root: int) -> None:\n        nonlocal answer\n        total = calc_size(root, -1)\n        centroid = find_centroid(root, -1, total)\n        removed[centroid] = True\n        freq = [0] * (k + 1)\n        freq[0] = 1\n        for to in graph[centroid]:\n            if removed[to]:\n                continue\n            depths = []\n            collect_depths(to, centroid, 1, depths)\n            for d in depths:\n                answer += freq[k - d]\n            for d in depths:\n                freq[d] += 1\n        for to in graph[centroid]:\n            if not removed[to]:\n                decompose(to)\n\n    decompose(0)\n    print(answer)\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
