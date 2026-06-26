from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('foundation')

UNIT_BANK = unit_bank(
    unit_id='algo-066-basic',
    title='セグメント木上の分割統治 の基本',
    unit_kind='foundation',
    target_skill='セグメント木上の分割統治 の基本',
    concept_overview='時間区間に対する操作をセグメント木の節点へ載せ、再帰で区間ごとに処理すると、追加と削除が混ざる問題をまとめて扱えます。まずは動的な連結判定をこの形で解く流れを確認します。',
    problem_bank=[
        problem(
            problem_id='algo-066-basic-p1',
            title='セグメント木上の分割統治 の基本 / 辺の追加削除つき連結判定を行う',
            problem_statement='N 頂点の無向グラフに対する Q 個の操作が与えられる。`+ u v` は辺 (u, v) を追加、`- u v` はその辺を削除、`? u v` はその時点で u と v が連結かを答える。各辺の追加と削除は対応している。',
            input_format='1 行目に N Q。\n続く Q 行に操作。',
            output_format='各 `?` について `Yes` または `No` を 1 行ずつ出力する。',
            constraints='1 <= N, Q <= 2 * 10^5',
            examples=[{'input': '4 7\n+ 1 2\n+ 2 3\n? 1 3\n- 2 3\n? 1 3\n+ 3 4\n? 1 4', 'output': 'Yes\nNo\nNo'}],
            canonical_reference_solution="def solve() -> None:\n    import sys\n    input = sys.stdin.readline\n    sys.setrecursionlimit(1 << 25)\n    n, q = map(int, input().split())\n    ops = []\n    active = {}\n    seg = [[] for _ in range(4 * q + 5)]\n\n    def norm(u: int, v: int) -> tuple[int, int]:\n        return (u, v) if u < v else (v, u)\n\n    def add_interval(node: int, left: int, right: int, ql: int, qr: int, edge: tuple[int, int]) -> None:\n        if qr <= left or right <= ql:\n            return\n        if ql <= left and right <= qr:\n            seg[node].append(edge)\n            return\n        mid = (left + right) // 2\n        add_interval(node * 2, left, mid, ql, qr, edge)\n        add_interval(node * 2 + 1, mid, right, ql, qr, edge)\n\n    for t in range(q):\n        parts = input().split()\n        kind = parts[0]\n        if kind == '+':\n            u = int(parts[1]) - 1\n            v = int(parts[2]) - 1\n            edge = norm(u, v)\n            active[edge] = t\n            ops.append((kind, edge))\n        elif kind == '-':\n            u = int(parts[1]) - 1\n            v = int(parts[2]) - 1\n            edge = norm(u, v)\n            add_interval(1, 0, q, active.pop(edge), t, edge)\n            ops.append((kind, edge))\n        else:\n            u = int(parts[1]) - 1\n            v = int(parts[2]) - 1\n            ops.append((kind, u, v))\n    for edge, start in active.items():\n        add_interval(1, 0, q, start, q, edge)\n\n    parent = list(range(n))\n    size = [1] * n\n    history = []\n\n    def find(x: int) -> int:\n        while parent[x] != x:\n            x = parent[x]\n        return x\n\n    def unite(a: int, b: int) -> None:\n        a = find(a)\n        b = find(b)\n        if a == b:\n            history.append((-1, -1, -1, -1))\n            return\n        if size[a] < size[b]:\n            a, b = b, a\n        history.append((b, parent[b], a, size[a]))\n        parent[b] = a\n        size[a] += size[b]\n\n    def rollback(snapshot: int) -> None:\n        while len(history) > snapshot:\n            b, prev_parent, a, prev_size = history.pop()\n            if b == -1:\n                continue\n            parent[b] = prev_parent\n            size[a] = prev_size\n\n    out = []\n\n    def dfs(node: int, left: int, right: int) -> None:\n        snapshot = len(history)\n        for u, v in seg[node]:\n            unite(u, v)\n        if right - left == 1:\n            op = ops[left]\n            if op[0] == '?':\n                out.append('Yes' if find(op[1]) == find(op[2]) else 'No')\n        else:\n            mid = (left + right) // 2\n            dfs(node * 2, left, mid)\n            dfs(node * 2 + 1, mid, right)\n        rollback(snapshot)\n\n    dfs(1, 0, q)\n    sys.stdout.write('\\n'.join(out))\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
