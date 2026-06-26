from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('foundation')

UNIT_BANK = unit_bank(
    unit_id='algo-026-practice',
    title='クラスカル法（最小全域木） を素直に実装する',
    unit_kind='foundation',
    target_skill='クラスカル法（最小全域木） を素直に実装する',
    concept_overview='クラスカル法では、重み順に辺を見ながら、採用した辺の集合そのものも復元できます。Union-Find で閉路を避けつつ、どの辺を選んだか追う実装を確かめます。',
    problem_bank=[
        problem(
            problem_id='algo-026-practice-p1',
            title='クラスカル法（最小全域木） を素直に実装する / 最小全域木に採用した辺番号を求める',
            problem_statement='重み付き無向連結グラフが与えられる。クラスカル法で最小全域木を 1 つ作り、採用した辺の入力番号を昇順で出力せよ。',
            input_format='1 行目に N M。\n続く M 行に u v w。',
            output_format='1 行目に最小全域木の重み。2 行目に採用した辺番号を昇順で出力する。',
            constraints='1 <= N <= 2 * 10^5\nN-1 <= M <= 2 * 10^5',
            examples=[{'input': '4 5\n1 2 1\n1 3 4\n2 3 2\n2 4 5\n3 4 1', 'output': '4\n1 3 5'}],
            canonical_reference_solution="def solve() -> None:\n    import sys\n    input = sys.stdin.readline\n    n, m = map(int, input().split())\n    edges = []\n    for idx in range(1, m + 1):\n        u, v, w = map(int, input().split())\n        edges.append((w, idx, u - 1, v - 1))\n    edges.sort()\n    parent = list(range(n))\n    size = [1] * n\n\n    def find(x: int) -> int:\n        while parent[x] != x:\n            parent[x] = parent[parent[x]]\n            x = parent[x]\n        return x\n\n    total = 0\n    picked = []\n    for w, idx, u, v in edges:\n        ru = find(u)\n        rv = find(v)\n        if ru == rv:\n            continue\n        if size[ru] < size[rv]:\n            ru, rv = rv, ru\n        parent[rv] = ru\n        size[ru] += size[rv]\n        total += w\n        picked.append(idx)\n    picked.sort()\n    print(total)\n    print(*picked)\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
