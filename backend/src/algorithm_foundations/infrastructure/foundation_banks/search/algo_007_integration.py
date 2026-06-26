from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('integration')

UNIT_BANK = unit_bank(
    unit_id='algo-007-integration',
    title='順列全探索 の総合演習',
    unit_kind='integration',
    target_skill='順列全探索 の総合演習',
    concept_overview='順列全探索は、並べ方をすべて試し、その中から条件を満たすものを見つける解き方です。候補を生成して順に評価する流れを押さえます。 この unit では、既習の 順列全探索 の基本 と 順列全探索 を素直に実装する を順に使いながら、1 問を分けて解く流れまで確認します。',
    problem_bank=[
        problem(
            problem_id='algo-007-integration-p1',
            title='順列全探索 の総合演習 / 1 ケースをそのまま解く',
            problem_statement='N 頂点の完全グラフの重み行列が与えられる。 頂点 1 から始めて残りを 1 回ずつ訪れる順列の中で、移動コスト合計の最小値を求めよ。\n\nこの問題では、前提 unit までで扱った知識だけを順に使えば解ける。',
            input_format='1 行目に N。\n続く N 行に重み行列。',
            output_format='最小コストを出力する。',
            constraints='2 <= N <= 8\n使う知識は前提 unit までに限定すること。',
            examples=[
                {
                    'input': '3\n0 2 5\n2 0 4\n5 4 0',
                    'output': '6',
                },
            ],
            canonical_reference_solution="from itertools import permutations\n\ndef solve() -> None:\n    n = int(input())\n    cost = [list(map(int, input().split())) for _ in range(n)]\n    ans = 10 ** 18\n    for order in permutations(range(1, n)):\n        total = 0\n        prev = 0\n        for nxt in order:\n            total += cost[prev][nxt]\n            prev = nxt\n        ans = min(ans, total)\n    print(ans)\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
        problem(
            problem_id='algo-007-integration-p2',
            title='順列全探索 の総合演習 / 2 ケースを連続して解く',
            problem_statement='2 ケース分の入力が続けて与えられる。それぞれについて、N 頂点の完全グラフの重み行列が与えられる。 頂点 1 から始めて残りを 1 回ずつ訪れる順列の中で、移動コスト合計の最小値を求めよ。\n\nこの問題では、前提 unit までで扱った知識だけを順に使えば解ける。',
            input_format='1 行目に 2。\n続く 2 ケースについて:\n1 行目に N。\n続く N 行に重み行列。',
            output_format='各ケースの答えを順に出力する。',
            constraints='2 <= N <= 8\n使う知識は前提 unit までに限定すること。\n2 ケースの合計でも同じ方針で処理すること。',
            examples=[
                {
                    'input': '2\n3\n0 2 5\n2 0 4\n5 4 0\n3\n0 2 5\n2 0 4\n5 4 0',
                    'output': '6\n6',
                },
            ],
            canonical_reference_solution="import io\nimport sys\nfrom contextlib import redirect_stdout\n\nfrom itertools import permutations\n\ndef solve_one() -> None:\n    n = int(input())\n    cost = [list(map(int, input().split())) for _ in range(n)]\n    ans = 10 ** 18\n    for order in permutations(range(1, n)):\n        total = 0\n        prev = 0\n        for nxt in order:\n            total += cost[prev][nxt]\n            prev = nxt\n        ans = min(ans, total)\n    print(ans)\n\ndef solve() -> None:\n    t = 2\n    outputs = []\n    for _ in range(t):\n        buf = io.StringIO()\n        with redirect_stdout(buf):\n            solve_one()\n        outputs.append(buf.getvalue().rstrip('\\n'))\n    sys.stdout.write('\\n'.join(outputs))\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
        problem(
            problem_id='algo-007-integration-p3',
            title='順列全探索 の総合演習 / 3 ケースを連続して解く',
            problem_statement='3 ケース分の入力が続けて与えられる。それぞれについて、N 頂点の完全グラフの重み行列が与えられる。 頂点 1 から始めて残りを 1 回ずつ訪れる順列の中で、移動コスト合計の最小値を求めよ。\n\nこの問題では、前提 unit までで扱った知識だけを順に使えば解ける。',
            input_format='1 行目に 3。\n続く 3 ケースについて:\n1 行目に N。\n続く N 行に重み行列。',
            output_format='各ケースの答えを順に出力する。',
            constraints='2 <= N <= 8\n使う知識は前提 unit までに限定すること。\n3 ケースの合計でも同じ方針で処理すること。',
            examples=[
                {
                    'input': '3\n3\n0 2 5\n2 0 4\n5 4 0\n3\n0 2 5\n2 0 4\n5 4 0\n3\n0 2 5\n2 0 4\n5 4 0',
                    'output': '6\n6\n6',
                },
            ],
            canonical_reference_solution="import io\nimport sys\nfrom contextlib import redirect_stdout\n\nfrom itertools import permutations\n\ndef solve_one() -> None:\n    n = int(input())\n    cost = [list(map(int, input().split())) for _ in range(n)]\n    ans = 10 ** 18\n    for order in permutations(range(1, n)):\n        total = 0\n        prev = 0\n        for nxt in order:\n            total += cost[prev][nxt]\n            prev = nxt\n        ans = min(ans, total)\n    print(ans)\n\ndef solve() -> None:\n    t = 3\n    outputs = []\n    for _ in range(t):\n        buf = io.StringIO()\n        with redirect_stdout(buf):\n            solve_one()\n        outputs.append(buf.getvalue().rstrip('\\n'))\n    sys.stdout.write('\\n'.join(outputs))\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
