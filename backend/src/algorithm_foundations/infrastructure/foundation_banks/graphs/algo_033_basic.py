from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('foundation')

UNIT_BANK = unit_bank(
    unit_id='algo-033-basic',
    title='オイラー路・オイラー閉路 の基本',
    unit_kind='foundation',
    target_skill='オイラー路・オイラー閉路 の基本',
    concept_overview='オイラー路・オイラー閉路は、辺をちょうど 1 回ずつ通る道が作れるかを考える知識です。次数や通り方の条件を整理する基本を学びます。',
    problem_bank=[
        problem(
            problem_id='algo-033-basic-p1',
            title='オイラー路・オイラー閉路 の基本 / 1 ケースをそのまま解く',
            problem_statement='N 頂点 M 辺の無向グラフが与えられる。 すべての辺をちょうど 1 回ずつ通る道が存在するなら Yes、存在しなければ No を出力せよ。',
            input_format='1 行目に N M。\n続く M 行に辺 u v。',
            output_format='Yes / No を出力する。',
            constraints='1 <= N, M <= 2 * 10^5',
            examples=[
                {
                    'input': '4 3\n1 2\n2 3\n3 4',
                    'output': 'Yes',
                },
            ],
            canonical_reference_solution="def solve() -> None:\n    import sys\n    input = sys.stdin.readline\n    n, m = map(int, input().split())\n    parent = list(range(n))\n    size = [1] * n\n    degree = [0] * n\n\n    def find(x: int) -> int:\n        while parent[x] != x:\n            parent[x] = parent[parent[x]]\n            x = parent[x]\n        return x\n\n    def unite(a: int, b: int) -> None:\n        ra = find(a)\n        rb = find(b)\n        if ra == rb:\n            return\n        if size[ra] < size[rb]:\n            ra, rb = rb, ra\n        parent[rb] = ra\n        size[ra] += size[rb]\n\n    for _ in range(m):\n        u, v = map(int, input().split())\n        u -= 1\n        v -= 1\n        degree[u] += 1\n        degree[v] += 1\n        unite(u, v)\n    active = [i for i, deg in enumerate(degree) if deg > 0]\n    if active:\n        root = find(active[0])\n        if any(find(node) != root for node in active):\n            print('No')\n            return\n    odd = sum(deg % 2 for deg in degree)\n    print('Yes' if odd in (0, 2) else 'No')\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
        problem(
            problem_id='algo-033-basic-p2',
            title='オイラー路・オイラー閉路 の基本 / 2 ケースを連続して解く',
            problem_statement='2 ケース分の入力が続けて与えられる。それぞれについて、N 頂点 M 辺の無向グラフが与えられる。 すべての辺をちょうど 1 回ずつ通る道が存在するなら Yes、存在しなければ No を出力せよ。',
            input_format='1 行目に 2。\n続く 2 ケースについて:\n1 行目に N M。\n続く M 行に辺 u v。',
            output_format='各ケースの答えを順に出力する。',
            constraints='1 <= N, M <= 2 * 10^5\n2 ケースの合計でも同じ方針で処理すること。',
            examples=[
                {
                    'input': '2\n4 3\n1 2\n2 3\n3 4\n4 3\n1 2\n2 3\n3 4',
                    'output': 'Yes\nYes',
                },
            ],
            canonical_reference_solution="import io\nimport sys\nfrom contextlib import redirect_stdout\n\ndef solve_one() -> None:\n    import sys\n    input = sys.stdin.readline\n    n, m = map(int, input().split())\n    parent = list(range(n))\n    size = [1] * n\n    degree = [0] * n\n\n    def find(x: int) -> int:\n        while parent[x] != x:\n            parent[x] = parent[parent[x]]\n            x = parent[x]\n        return x\n\n    def unite(a: int, b: int) -> None:\n        ra = find(a)\n        rb = find(b)\n        if ra == rb:\n            return\n        if size[ra] < size[rb]:\n            ra, rb = rb, ra\n        parent[rb] = ra\n        size[ra] += size[rb]\n\n    for _ in range(m):\n        u, v = map(int, input().split())\n        u -= 1\n        v -= 1\n        degree[u] += 1\n        degree[v] += 1\n        unite(u, v)\n    active = [i for i, deg in enumerate(degree) if deg > 0]\n    if active:\n        root = find(active[0])\n        if any(find(node) != root for node in active):\n            print('No')\n            return\n    odd = sum(deg % 2 for deg in degree)\n    print('Yes' if odd in (0, 2) else 'No')\n\ndef solve() -> None:\n    t = 2\n    outputs = []\n    for _ in range(t):\n        buf = io.StringIO()\n        with redirect_stdout(buf):\n            solve_one()\n        outputs.append(buf.getvalue().rstrip('\\n'))\n    sys.stdout.write('\\n'.join(outputs))\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
        problem(
            problem_id='algo-033-basic-p3',
            title='オイラー路・オイラー閉路 の基本 / 3 ケースを連続して解く',
            problem_statement='3 ケース分の入力が続けて与えられる。それぞれについて、N 頂点 M 辺の無向グラフが与えられる。 すべての辺をちょうど 1 回ずつ通る道が存在するなら Yes、存在しなければ No を出力せよ。',
            input_format='1 行目に 3。\n続く 3 ケースについて:\n1 行目に N M。\n続く M 行に辺 u v。',
            output_format='各ケースの答えを順に出力する。',
            constraints='1 <= N, M <= 2 * 10^5\n3 ケースの合計でも同じ方針で処理すること。',
            examples=[
                {
                    'input': '3\n4 3\n1 2\n2 3\n3 4\n4 3\n1 2\n2 3\n3 4\n4 3\n1 2\n2 3\n3 4',
                    'output': 'Yes\nYes\nYes',
                },
            ],
            canonical_reference_solution="import io\nimport sys\nfrom contextlib import redirect_stdout\n\ndef solve_one() -> None:\n    import sys\n    input = sys.stdin.readline\n    n, m = map(int, input().split())\n    parent = list(range(n))\n    size = [1] * n\n    degree = [0] * n\n\n    def find(x: int) -> int:\n        while parent[x] != x:\n            parent[x] = parent[parent[x]]\n            x = parent[x]\n        return x\n\n    def unite(a: int, b: int) -> None:\n        ra = find(a)\n        rb = find(b)\n        if ra == rb:\n            return\n        if size[ra] < size[rb]:\n            ra, rb = rb, ra\n        parent[rb] = ra\n        size[ra] += size[rb]\n\n    for _ in range(m):\n        u, v = map(int, input().split())\n        u -= 1\n        v -= 1\n        degree[u] += 1\n        degree[v] += 1\n        unite(u, v)\n    active = [i for i, deg in enumerate(degree) if deg > 0]\n    if active:\n        root = find(active[0])\n        if any(find(node) != root for node in active):\n            print('No')\n            return\n    odd = sum(deg % 2 for deg in degree)\n    print('Yes' if odd in (0, 2) else 'No')\n\ndef solve() -> None:\n    t = 3\n    outputs = []\n    for _ in range(t):\n        buf = io.StringIO()\n        with redirect_stdout(buf):\n            solve_one()\n        outputs.append(buf.getvalue().rstrip('\\n'))\n    sys.stdout.write('\\n'.join(outputs))\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
