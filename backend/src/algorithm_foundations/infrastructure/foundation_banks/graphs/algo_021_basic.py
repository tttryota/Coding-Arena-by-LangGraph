from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('foundation')

UNIT_BANK = unit_bank(
    unit_id='algo-021-basic',
    title='隣接リスト・隣接行列 の基本',
    unit_kind='foundation',
    target_skill='隣接リスト・隣接行列 の基本',
    concept_overview='隣接リスト・隣接行列は、グラフの辺情報を「各頂点からどこへつながるか」という形で持つ知識です。まずは辺を読み取り、頂点ごとのつながり数へ直す基本を学びます。',
    problem_bank=[
        problem(
            problem_id='algo-021-basic-p1',
            title='隣接リスト・隣接行列 の基本 / 各頂点の次数を数える',
            problem_statement='N 頂点 M 辺の無向グラフが与えられる。各頂点の次数を求めよ。',
            input_format='1 行目に N M。\n続く M 行に辺 u v。',
            output_format='1 行に N 個、各頂点の次数を出力する。',
            constraints='1 <= N, M <= 2 * 10^5',
            examples=[{'input': '4 3\n1 2\n2 3\n2 4', 'output': '1 3 1 1'}],
            canonical_reference_solution="def solve() -> None:\n    import sys\n    input = sys.stdin.readline\n    n, m = map(int, input().split())\n    deg = [0] * n\n    for _ in range(m):\n        u, v = map(int, input().split())\n        deg[u - 1] += 1\n        deg[v - 1] += 1\n    print(*deg)\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
