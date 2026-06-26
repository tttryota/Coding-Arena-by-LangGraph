from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('foundation')

UNIT_BANK = unit_bank(
    unit_id='algo-128-basic',
    title='最小費用流 の基本',
    unit_kind='foundation',
    target_skill='最小費用流 の基本',
    concept_overview='最小費用流は、必要量を流しつつ総コストを最小化する問題を、残余グラフと最短路更新で解く知識です。まずは指定流量を送り切る最小コストを求める基本を学びます。',
    problem_bank=[
        problem(
            problem_id='algo-128-basic-p1',
            title='最小費用流 の基本 / 必要流量を送る最小コストを求める',
            problem_statement='容量とコストを持つ有向グラフが与えられる。頂点 1 から頂点 N へちょうど F 単位のフローを流す最小コストを求めよ。流し切れなければ -1 を出力せよ。',
            input_format='1 行目に N M F。\n続く M 行に u v cap cost。',
            output_format='最小総コスト、流し切れなければ -1 を出力する。',
            constraints='2 <= N <= 60\n1 <= M <= 300\n1 <= F <= 300\n0 <= cap <= 300\n0 <= cost <= 10^6',
            examples=[{'input': '4 5 2\n1 2 2 1\n1 3 1 4\n2 3 1 2\n2 4 1 6\n3 4 2 1', 'output': '9'}],
            canonical_reference_solution="from heapq import heappop, heappush\n\nclass MinCostFlow:\n    def __init__(self, n: int) -> None:\n        self.n = n\n        self.g = [[] for _ in range(n)]\n\n    def add_edge(self, fr: int, to: int, cap: int, cost: int) -> None:\n        fwd = [to, cap, cost, None]\n        rev = [fr, 0, -cost, fwd]\n        fwd[3] = rev\n        self.g[fr].append(fwd)\n        self.g[to].append(rev)\n\n    def flow(self, s: int, t: int, need: int) -> int | None:\n        n = self.n\n        h = [0] * n\n        result = 0\n        inf = 10 ** 18\n        while need > 0:\n            dist = [inf] * n\n            dist[s] = 0\n            prev_v = [-1] * n\n            prev_e = [None] * n\n            pq = [(0, s)]\n            while pq:\n                d, v = heappop(pq)\n                if d != dist[v]:\n                    continue\n                for e in self.g[v]:\n                    to, cap, cost, _ = e\n                    nd = d + cost + h[v] - h[to]\n                    if cap > 0 and nd < dist[to]:\n                        dist[to] = nd\n                        prev_v[to] = v\n                        prev_e[to] = e\n                        heappush(pq, (nd, to))\n            if dist[t] == inf:\n                return None\n            for v in range(n):\n                if dist[v] < inf:\n                    h[v] += dist[v]\n            add = need\n            v = t\n            while v != s:\n                add = min(add, prev_e[v][1])\n                v = prev_v[v]\n            need -= add\n            result += add * h[t]\n            v = t\n            while v != s:\n                e = prev_e[v]\n                e[1] -= add\n                e[3][1] += add\n                v = prev_v[v]\n        return result\n\ndef solve() -> None:\n    n, m, f = map(int, input().split())\n    mcf = MinCostFlow(n)\n    for _ in range(m):\n        u, v, cap, cost = map(int, input().split())\n        mcf.add_edge(u - 1, v - 1, cap, cost)\n    ans = mcf.flow(0, n - 1, f)\n    print(-1 if ans is None else ans)\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
