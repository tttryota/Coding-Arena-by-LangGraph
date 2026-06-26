from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('foundation')

UNIT_BANK = unit_bank(
    unit_id='algo-021-practice',
    title='隣接リスト・隣接行列 を素直に実装する',
    unit_kind='foundation',
    target_skill='隣接リスト・隣接行列 を素直に実装する',
    concept_overview='隣接リストでは、各辺を読んだら両端の頂点のリストへ相手を追加します。頂点ごとの行き先をそのまま持つ表現を実装で確かめます。',
    problem_bank=[
        problem(
            problem_id='algo-021-practice-p1',
            title='隣接リスト・隣接行列 を素直に実装する / 各頂点の隣接頂点を入力順に並べる',
            problem_statement='N 頂点 M 辺の無向グラフが与えられる。各頂点 v について、1 行に `隣接頂点数 k` と、その後ろに v と隣接する頂点を入力に現れた順で出力せよ。隣接頂点がないときは 0 だけを出力する。',
            input_format='1 行目に N M。\n続く M 行に辺 u v。',
            output_format='各頂点について、隣接頂点数 k と、その後ろに隣接頂点 k 個を 1 行で出力する。隣接頂点がないときは 0 だけを出力する。',
            constraints='1 <= N, M <= 2 * 10^5',
            examples=[{'input': '4 3\n1 2\n2 3\n2 4', 'output': '1 2\n3 1 3 4\n1 2\n1 2'}],
            canonical_reference_solution="def solve() -> None:\n    import sys\n    input = sys.stdin.readline\n    n, m = map(int, input().split())\n    graph = [[] for _ in range(n)]\n    for _ in range(m):\n        u, v = map(int, input().split())\n        u -= 1\n        v -= 1\n        graph[u].append(v + 1)\n        graph[v].append(u + 1)\n    out = []\n    for adj in graph:\n        if not adj:\n            out.append('0')\n        else:\n            out.append(' '.join([str(len(adj)), *map(str, adj)]))\n    sys.stdout.write('\\n'.join(out))\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
