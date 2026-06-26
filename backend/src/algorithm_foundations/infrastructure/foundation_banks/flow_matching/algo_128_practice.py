from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('foundation')

UNIT_BANK = unit_bank(
    unit_id='algo-128-practice',
    title='最小費用流 を素直に実装する',
    unit_kind='foundation',
    target_skill='最小費用流 を素直に実装する',
    concept_overview='最小費用流では、指定量を送り切る代わりに、予算内でどこまで流せるかを求める形にもできます。ここでは総コスト制約つきで最大流量を求めます。',
    problem_bank=[
        problem(
            problem_id='algo-128-practice-p1',
            title='最小費用流 を素直に実装する / 予算 B 以内で送れる最大流量を求める',
            problem_statement='容量とコストを持つ有向グラフが与えられる。頂点 1 から頂点 N へフローを流すとき、総コストが B 以下となる範囲で送れる最大流量を求めよ。',
            input_format='1 行目に N M B。\n続く M 行に u v cap cost。',
            output_format='送れる最大流量を出力する。',
            constraints='2 <= N <= 60\n1 <= M <= 300\n0 <= B <= 10^9\n0 <= cap <= 300\n0 <= cost <= 10^6',
            examples=[{'input': '4 5 8\n1 2 2 1\n1 3 1 4\n2 3 1 2\n2 4 1 6\n3 4 2 1', 'output': '1'}],
            canonical_reference_solution="from heapq import heappop, heappush\n\nclass MinCostFlow:\n    def __init__(self, n: int) -> None:\n        self.n = n\n        self.g = [[] for _ in range(n)]\n\n    def add_edge(self, fr: int, to: int, cap: int, cost: int) -> None:\n        fwd = [to, cap, cost, None]\n        rev = [fr, 0, -cost, fwd]\n        fwd[3] = rev\n        self.g[fr].append(fwd)\n        self.g[to].append(rev)\n\n    def max_flow_with_budget(self, s: int, t: int, budget: int) -> int:\n        n = self.n\n        h = [0] * n\n        inf = 10 ** 18\n        total_cost = 0\n        total_flow = 0\n        while True:\n            dist = [inf] * n\n            dist[s] = 0\n            prev_v = [-1] * n\n            prev_e = [None] * n\n            pq = [(0, s)]\n            while pq:\n                d, v = heappop(pq)\n                if d != dist[v]:\n                    continue\n                for e in self.g[v]:\n                    to, cap, cost, _ = e\n                    nd = d + cost + h[v] - h[to]\n                    if cap > 0 and nd < dist[to]:\n                        dist[to] = nd\n                        prev_v[to] = v\n                        prev_e[to] = e\n                        heappush(pq, (nd, to))\n            if dist[t] == inf:\n                break\n            for v in range(n):\n                if dist[v] < inf:\n                    h[v] += dist[v]\n            add = inf\n            v = t\n            while v != s:\n                add = min(add, prev_e[v][1])\n                v = prev_v[v]\n            path_cost = h[t]\n            if path_cost == 0:\n                affordable = add\n            else:\n                affordable = min(add, (budget - total_cost) // path_cost)\n            if affordable <= 0:\n                break\n            total_flow += affordable\n            total_cost += affordable * path_cost\n            v = t\n            while v != s:\n                e = prev_e[v]\n                e[1] -= affordable\n                e[3][1] += affordable\n                v = prev_v[v]\n        return total_flow\n\n\ndef solve() -> None:\n    n, m, b = map(int, input().split())\n    mcf = MinCostFlow(n)\n    for _ in range(m):\n        u, v, cap, cost = map(int, input().split())\n        mcf.add_edge(u - 1, v - 1, cap, cost)\n    print(mcf.max_flow_with_budget(0, n - 1, b))\n\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
