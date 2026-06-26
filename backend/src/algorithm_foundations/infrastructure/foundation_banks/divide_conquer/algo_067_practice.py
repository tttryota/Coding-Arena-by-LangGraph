from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('foundation')

UNIT_BANK = unit_bank(
    unit_id='algo-067-practice',
    title='重心分解 を素直に実装する',
    unit_kind='foundation',
    target_skill='重心分解 を素直に実装する',
    concept_overview='重心分解で各頂点から重心列への距離を持っておくと、色を付けた頂点への最短距離を高速に更新・問い合わせできます。重心親方向へ情報を集約する定番形を実装で確かめます。',
    problem_bank=[
        problem(
            problem_id='algo-067-practice-p1',
            title='重心分解 を素直に実装する / 赤い頂点への最短距離を更新しながら求める',
            problem_statement='N 頂点の木に対して Q 個の操作が与えられる。`1 v` は頂点 v を赤く塗る。`2 v` は赤い頂点までの最短距離を求める。赤い頂点が 1 つもなければ -1 を出力せよ。',
            input_format='1 行目に N Q。\n続く N-1 行に辺 u v。\n続く Q 行に操作。',
            output_format='各 `2 v` に対する答えを 1 行ずつ出力する。',
            constraints='1 <= N, Q <= 2 * 10^5',
            examples=[{'input': '5 5\n1 2\n2 3\n3 4\n3 5\n2 4\n1 2\n2 4\n1 5\n2 4', 'output': '-1\n2\n2'}],
            canonical_reference_solution="def solve() -> None:\n    import sys\n    input = sys.stdin.readline\n    sys.setrecursionlimit(1 << 25)\n    n, q = map(int, input().split())\n    graph = [[] for _ in range(n)]\n    for _ in range(n - 1):\n        u, v = map(int, input().split())\n        u -= 1\n        v -= 1\n        graph[u].append(v)\n        graph[v].append(u)\n\n    removed = [False] * n\n    size = [0] * n\n    paths = [[] for _ in range(n)]\n\n    def calc_size(v: int, p: int) -> int:\n        size[v] = 1\n        for to in graph[v]:\n            if to == p or removed[to]:\n                continue\n            size[v] += calc_size(to, v)\n        return size[v]\n\n    def find_centroid(v: int, p: int, total: int) -> int:\n        for to in graph[v]:\n            if to == p or removed[to]:\n                continue\n            if size[to] * 2 > total:\n                return find_centroid(to, v, total)\n        return v\n\n    def fill_paths(v: int, p: int, dist: int, centroid: int) -> None:\n        paths[v].append((centroid, dist))\n        for to in graph[v]:\n            if to == p or removed[to]:\n                continue\n            fill_paths(to, v, dist + 1, centroid)\n\n    def decompose(root: int) -> None:\n        total = calc_size(root, -1)\n        centroid = find_centroid(root, -1, total)\n        removed[centroid] = True\n        fill_paths(centroid, -1, 0, centroid)\n        for to in graph[centroid]:\n            if not removed[to]:\n                decompose(to)\n\n    decompose(0)\n    inf = 10 ** 18\n    best = [inf] * n\n\n    def paint(v: int) -> None:\n        for centroid, dist in paths[v]:\n            if dist < best[centroid]:\n                best[centroid] = dist\n\n    def query(v: int) -> int:\n        ans = inf\n        for centroid, dist in paths[v]:\n            cand = best[centroid] + dist\n            if cand < ans:\n                ans = cand\n        return -1 if ans == inf else ans\n\n    out = []\n    for _ in range(q):\n        t, v = map(int, input().split())\n        v -= 1\n        if t == 1:\n            paint(v)\n        else:\n            out.append(str(query(v)))\n    sys.stdout.write('\\n'.join(out))\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
