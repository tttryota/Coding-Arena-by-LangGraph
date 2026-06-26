from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('foundation')

UNIT_BANK = unit_bank(
    unit_id='algo-025-practice',
    title='プリム法（最小全域木） を素直に実装する',
    unit_kind='foundation',
    target_skill='プリム法（最小全域木） を素直に実装する',
    concept_overview='プリム法は、まだ木に入っていない頂点のうち最も安くつなげるものを順に選びます。密なグラフでは、各頂点へ伸びる最小コストを配列で持つ実装でも進められます。',
    problem_bank=[
        problem(
            problem_id='algo-025-practice-p1',
            title='プリム法（最小全域木） を素直に実装する / 重み行列から最小全域木の重みを求める',
            problem_statement='N 頂点の完全無向グラフの重み行列 W が与えられる。プリム法で最小全域木の重みを求めよ。',
            input_format='1 行目に N。\n続く N 行に W の各行。',
            output_format='最小全域木の重みを出力する。',
            constraints='1 <= N <= 500\n0 <= W[i][j] <= 10^9\nW[i][i] = 0\nW[i][j] = W[j][i]',
            examples=[{'input': '4\n0 1 4 7\n1 0 2 5\n4 2 0 1\n7 5 1 0', 'output': '4'}],
            canonical_reference_solution="def solve() -> None:\n    n = int(input())\n    w = [list(map(int, input().split())) for _ in range(n)]\n    used = [False] * n\n    best = [10 ** 18] * n\n    best[0] = 0\n    total = 0\n    for _ in range(n):\n        node = -1\n        for v in range(n):\n            if used[v]:\n                continue\n            if node == -1 or best[v] < best[node]:\n                node = v\n        used[node] = True\n        total += best[node]\n        for nxt in range(n):\n            if not used[nxt] and w[node][nxt] < best[nxt]:\n                best[nxt] = w[node][nxt]\n    print(total)\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
