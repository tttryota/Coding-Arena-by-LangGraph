from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('foundation')

UNIT_BANK = unit_bank(
    unit_id='algo-033-practice',
    title='オイラー路・オイラー閉路 を素直に実装する',
    unit_kind='foundation',
    target_skill='オイラー路・オイラー閉路 を素直に実装する',
    concept_overview='オイラー路では奇数次数の頂点数が 2 個、オイラー閉路では 0 個です。存在判定に加えて、どちらの型なのか分類する見方を確かめます。',
    problem_bank=[
        problem(
            problem_id='algo-033-practice-p1',
            title='オイラー路・オイラー閉路 を素直に実装する / Euler Path・Euler Circuit・None を判定する',
            problem_statement='N 頂点 M 辺の無向グラフが与えられる。すべての辺をちょうど 1 回ずつ通る道が存在しないなら `None`、存在して始点と終点を同じにできるなら `Euler Circuit`、始点と終点が異なるなら `Euler Path` を出力せよ。',
            input_format='1 行目に N M。\n続く M 行に辺 u v。',
            output_format='判定結果を出力する。',
            constraints='1 <= N, M <= 2 * 10^5',
            examples=[{'input': '4 3\n1 2\n2 3\n3 4', 'output': 'Euler Path'}],
            canonical_reference_solution="def solve() -> None:\n    import sys\n    input = sys.stdin.readline\n    n, m = map(int, input().split())\n    parent = list(range(n))\n    size = [1] * n\n    degree = [0] * n\n\n    def find(x: int) -> int:\n        while parent[x] != x:\n            parent[x] = parent[parent[x]]\n            x = parent[x]\n        return x\n\n    def unite(a: int, b: int) -> None:\n        ra = find(a)\n        rb = find(b)\n        if ra == rb:\n            return\n        if size[ra] < size[rb]:\n            ra, rb = rb, ra\n        parent[rb] = ra\n        size[ra] += size[rb]\n\n    for _ in range(m):\n        u, v = map(int, input().split())\n        u -= 1\n        v -= 1\n        degree[u] += 1\n        degree[v] += 1\n        unite(u, v)\n    active = [i for i, deg in enumerate(degree) if deg > 0]\n    if active:\n        root = find(active[0])\n        if any(find(node) != root for node in active):\n            print('None')\n            return\n    odd = sum(deg % 2 for deg in degree)\n    if odd == 0:\n        print('Euler Circuit')\n    elif odd == 2:\n        print('Euler Path')\n    else:\n        print('None')\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
