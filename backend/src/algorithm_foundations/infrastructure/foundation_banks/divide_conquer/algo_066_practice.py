from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('foundation')

UNIT_BANK = unit_bank(
    unit_id='algo-066-practice',
    title='セグメント木上の分割統治 を素直に実装する',
    unit_kind='foundation',
    target_skill='セグメント木上の分割統治 を素直に実装する',
    concept_overview='同じ枠組みで、時刻ごとの連結判定だけでなく「その成分に載っている値の合計」も追えます。rollback できる成分和管理を加えて、葉で各頂点の属する成分の総和を読み取ります。',
    problem_bank=[
        problem(
            problem_id='algo-066-practice-p1',
            title='セグメント木上の分割統治 を素直に実装する / 辺の追加削除つきで頂点 v の連結成分の値の総和を求める',
            problem_statement='頂点 1..N には初期値 W_i がある。無向グラフに対する Q 個の操作が与えられる。`+ u v` は辺 (u, v) を追加、`- u v` はその辺を削除、`? v` はその時点で頂点 v を含む連結成分に属する頂点値の総和を答える。各辺の追加と削除は対応している。',
            input_format='1 行目に N Q。\n2 行目に W_1..W_N。\n続く Q 行に操作。',
            output_format='各 `?` について成分値総和を 1 行ずつ出力する。',
            constraints='1 <= N, Q <= 2 * 10^5\n0 <= W_i <= 10^9',
            examples=[{'input': '4 7\n5 1 4 3\n+ 1 2\n? 1\n+ 2 3\n? 1\n- 1 2\n? 1\n? 3\n', 'output': '6\n10\n5\n5'}],
            canonical_reference_solution="def solve() -> None:\n    import sys\n    input = sys.stdin.readline\n    sys.setrecursionlimit(1 << 25)\n    n, q = map(int, input().split())\n    weight = list(map(int, input().split()))\n    ops = []\n    active = {}\n    seg = [[] for _ in range(4 * q + 5)]\n\n    def norm(u: int, v: int) -> tuple[int, int]:\n        return (u, v) if u < v else (v, u)\n\n    def add_interval(node: int, left: int, right: int, ql: int, qr: int, edge: tuple[int, int]) -> None:\n        if qr <= left or right <= ql:\n            return\n        if ql <= left and right <= qr:\n            seg[node].append(edge)\n            return\n        mid = (left + right) // 2\n        add_interval(node * 2, left, mid, ql, qr, edge)\n        add_interval(node * 2 + 1, mid, right, ql, qr, edge)\n\n    for t in range(q):\n        parts = input().split()\n        kind = parts[0]\n        if kind == '+':\n            u = int(parts[1]) - 1\n            v = int(parts[2]) - 1\n            edge = norm(u, v)\n            active[edge] = t\n            ops.append((kind, edge))\n        elif kind == '-':\n            u = int(parts[1]) - 1\n            v = int(parts[2]) - 1\n            edge = norm(u, v)\n            add_interval(1, 0, q, active.pop(edge), t, edge)\n            ops.append((kind, edge))\n        else:\n            v = int(parts[1]) - 1\n            ops.append((kind, v))\n    for edge, start in active.items():\n        add_interval(1, 0, q, start, q, edge)\n\n    parent = list(range(n))\n    size = [1] * n\n    comp_sum = weight[:]\n    history = []\n\n    def find(x: int) -> int:\n        while parent[x] != x:\n            x = parent[x]\n        return x\n\n    def unite(a: int, b: int) -> None:\n        a = find(a)\n        b = find(b)\n        if a == b:\n            history.append((-1, -1, -1, -1, -1))\n            return\n        if size[a] < size[b]:\n            a, b = b, a\n        history.append((b, parent[b], a, size[a], comp_sum[a]))\n        parent[b] = a\n        size[a] += size[b]\n        comp_sum[a] += comp_sum[b]\n\n    def rollback(snapshot: int) -> None:\n        while len(history) > snapshot:\n            b, prev_parent, a, prev_size, prev_sum = history.pop()\n            if b == -1:\n                continue\n            parent[b] = prev_parent\n            size[a] = prev_size\n            comp_sum[a] = prev_sum\n\n    out = []\n\n    def dfs(node: int, left: int, right: int) -> None:\n        snapshot = len(history)\n        for u, v in seg[node]:\n            unite(u, v)\n        if right - left == 1:\n            op = ops[left]\n            if op[0] == '?':\n                root = find(op[1])\n                out.append(str(comp_sum[root]))\n        else:\n            mid = (left + right) // 2\n            dfs(node * 2, left, mid)\n            dfs(node * 2 + 1, mid, right)\n        rollback(snapshot)\n\n    dfs(1, 0, q)\n    sys.stdout.write('\\n'.join(out))\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
