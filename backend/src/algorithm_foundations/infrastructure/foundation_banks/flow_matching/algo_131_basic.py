from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('foundation')

UNIT_BANK = unit_bank(
    unit_id='algo-131-basic',
    title='プロジェクト選択問題（燃やす埋める） の基本',
    unit_kind='foundation',
    target_skill='プロジェクト選択問題（燃やす埋める） の基本',
    concept_overview='プロジェクト選択問題は、利益・損失・依存制約つきの選択を s-t カットに落として最適化する知識です。まずは最大利益値そのものを求める基本を学びます。',
    problem_bank=[
        problem(
            problem_id='algo-131-basic-p1',
            title='プロジェクト選択問題（燃やす埋める） の基本 / 依存つきプロジェクトの最大利益を求める',
            problem_statement='各プロジェクト i には利益 w_i があり、依存関係 a -> b は「a を選ぶなら b も選ぶ」を意味する。条件を満たす部分集合のうち、総利益の最大値を求めよ。',
            input_format='1 行目に N M。\n2 行目に w_1..w_N。\n続く M 行に a b。',
            output_format='最大総利益を出力する。',
            constraints='1 <= N <= 200\n0 <= M <= 2000\n-10^9 <= w_i <= 10^9',
            examples=[{'input': '3 2\n5 -4 6\n1 2\n3 2', 'output': '7'}],
            canonical_reference_solution="class Dinic:\n    def __init__(self, n: int) -> None:\n        self.n = n\n        self.g = [[] for _ in range(n)]\n\n    def add_edge(self, fr: int, to: int, cap: int) -> None:\n        fwd = [to, cap, None]\n        rev = [fr, 0, fwd]\n        fwd[2] = rev\n        self.g[fr].append(fwd)\n        self.g[to].append(rev)\n\n    def max_flow(self, s: int, t: int) -> int:\n        from collections import deque\n        flow = 0\n        inf = 10 ** 18\n        while True:\n            level = [-1] * self.n\n            level[s] = 0\n            dq = deque([s])\n            while dq:\n                v = dq.popleft()\n                for to, cap, _ in self.g[v]:\n                    if cap > 0 and level[to] == -1:\n                        level[to] = level[v] + 1\n                        dq.append(to)\n            if level[t] == -1:\n                return flow\n            it = [0] * self.n\n            def dfs(v: int, f: int) -> int:\n                if v == t:\n                    return f\n                for i in range(it[v], len(self.g[v])):\n                    it[v] = i\n                    to, cap, rev = self.g[v][i]\n                    if cap <= 0 or level[v] + 1 != level[to]:\n                        continue\n                    pushed = dfs(to, min(f, cap))\n                    if pushed:\n                        self.g[v][i][1] -= pushed\n                        rev[1] += pushed\n                        return pushed\n                return 0\n            while True:\n                pushed = dfs(s, inf)\n                if pushed == 0:\n                    break\n                flow += pushed\n\n\ndef solve() -> None:\n    n, m = map(int, input().split())\n    profit = list(map(int, input().split()))\n    s = n\n    t = n + 1\n    dinic = Dinic(n + 2)\n    total_positive = 0\n    inf = 10 ** 18\n    for i, value in enumerate(profit):\n        if value >= 0:\n            total_positive += value\n            dinic.add_edge(s, i, value)\n        else:\n            dinic.add_edge(i, t, -value)\n    for _ in range(m):\n        a, b = map(int, input().split())\n        dinic.add_edge(a - 1, b - 1, inf)\n    min_cut = dinic.max_flow(s, t)\n    print(total_positive - min_cut)\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
