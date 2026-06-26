from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('integration')

UNIT_BANK = unit_bank(
    unit_id='algo-021-integration',
    title='隣接リスト・隣接行列 の総合演習',
    unit_kind='integration',
    target_skill='隣接リスト・隣接行列 の総合演習',
    concept_overview='隣接リスト・隣接行列は、入力の構造や候補を整理し、決まった手順で答えを作る知識です。まずは典型の使い方を自分の手で追える状態を目指します。 この unit では、既習の 隣接リスト・隣接行列 の基本 と 隣接リスト・隣接行列 を素直に実装する を順に使いながら、1 問を分けて解く流れまで確認します。',
    problem_bank=[
        problem(
            problem_id='algo-021-integration-p1',
            title='隣接リスト・隣接行列 の総合演習 / 1 ケースをそのまま解く',
            problem_statement='N 頂点 M 辺の無向グラフが与えられる。各頂点の次数を求めよ。\n\nこの問題では、前提 unit までで扱った知識だけを順に使えば解ける。',
            input_format='1 行目に N M。\n続く M 行に辺 u v。',
            output_format='1 行に N 個、各頂点の次数を出力する。',
            constraints='1 <= N, M <= 2 * 10^5\n使う知識は前提 unit までに限定すること。',
            examples=[
                {
                    'input': '4 3\n1 2\n2 3\n2 4',
                    'output': '1 3 1 1',
                },
            ],
            canonical_reference_solution="def solve() -> None:\n    import sys\n    input = sys.stdin.readline\n    n, m = map(int, input().split())\n    deg = [0] * n\n    for _ in range(m):\n        u, v = map(int, input().split())\n        deg[u - 1] += 1\n        deg[v - 1] += 1\n    print(*deg)\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
        problem(
            problem_id='algo-021-integration-p2',
            title='隣接リスト・隣接行列 の総合演習 / 2 ケースを連続して解く',
            problem_statement='2 ケース分の入力が続けて与えられる。それぞれについて、N 頂点 M 辺の無向グラフが与えられる。各頂点の次数を求めよ。\n\nこの問題では、前提 unit までで扱った知識だけを順に使えば解ける。',
            input_format='1 行目に 2。\n続く 2 ケースについて:\n1 行目に N M。\n続く M 行に辺 u v。',
            output_format='各ケースの答えを順に出力する。',
            constraints='1 <= N, M <= 2 * 10^5\n使う知識は前提 unit までに限定すること。\n2 ケースの合計でも同じ方針で処理すること。',
            examples=[
                {
                    'input': '2\n4 3\n1 2\n2 3\n2 4\n4 3\n1 2\n2 3\n2 4',
                    'output': '1 3 1 1\n1 3 1 1',
                },
            ],
            canonical_reference_solution="import io\nimport sys\nfrom contextlib import redirect_stdout\n\ndef solve_one() -> None:\n    import sys\n    input = sys.stdin.readline\n    n, m = map(int, input().split())\n    deg = [0] * n\n    for _ in range(m):\n        u, v = map(int, input().split())\n        deg[u - 1] += 1\n        deg[v - 1] += 1\n    print(*deg)\n\ndef solve() -> None:\n    t = 2\n    outputs = []\n    for _ in range(t):\n        buf = io.StringIO()\n        with redirect_stdout(buf):\n            solve_one()\n        outputs.append(buf.getvalue().rstrip('\\n'))\n    sys.stdout.write('\\n'.join(outputs))\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
        problem(
            problem_id='algo-021-integration-p3',
            title='隣接リスト・隣接行列 の総合演習 / 3 ケースを連続して解く',
            problem_statement='3 ケース分の入力が続けて与えられる。それぞれについて、N 頂点 M 辺の無向グラフが与えられる。各頂点の次数を求めよ。\n\nこの問題では、前提 unit までで扱った知識だけを順に使えば解ける。',
            input_format='1 行目に 3。\n続く 3 ケースについて:\n1 行目に N M。\n続く M 行に辺 u v。',
            output_format='各ケースの答えを順に出力する。',
            constraints='1 <= N, M <= 2 * 10^5\n使う知識は前提 unit までに限定すること。\n3 ケースの合計でも同じ方針で処理すること。',
            examples=[
                {
                    'input': '3\n4 3\n1 2\n2 3\n2 4\n4 3\n1 2\n2 3\n2 4\n4 3\n1 2\n2 3\n2 4',
                    'output': '1 3 1 1\n1 3 1 1\n1 3 1 1',
                },
            ],
            canonical_reference_solution="import io\nimport sys\nfrom contextlib import redirect_stdout\n\ndef solve_one() -> None:\n    import sys\n    input = sys.stdin.readline\n    n, m = map(int, input().split())\n    deg = [0] * n\n    for _ in range(m):\n        u, v = map(int, input().split())\n        deg[u - 1] += 1\n        deg[v - 1] += 1\n    print(*deg)\n\ndef solve() -> None:\n    t = 3\n    outputs = []\n    for _ in range(t):\n        buf = io.StringIO()\n        with redirect_stdout(buf):\n            solve_one()\n        outputs.append(buf.getvalue().rstrip('\\n'))\n    sys.stdout.write('\\n'.join(outputs))\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
