from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('integration')

UNIT_BANK = unit_bank(
    unit_id='algo-004-integration',
    title='深さ優先探索（DFS） の総合演習',
    unit_kind='integration',
    target_skill='深さ優先探索（DFS） の総合演習',
    concept_overview='深さ優先探索は、行けるところまで進んでから戻る形で状態や頂点をたどる解き方です。再帰やスタックで探索順を管理する基本を学びます。 この unit では、既習の 深さ優先探索（DFS） の基本 と 深さ優先探索（DFS） を素直に実装する を順に使いながら、1 問を分けて解く流れまで確認します。',
    problem_bank=[
        problem(
            problem_id='algo-004-integration-p1',
            title='深さ優先探索（DFS） の総合演習 / 1 ケースをそのまま解く',
            problem_statement='長さ N の整数列 A と整数 x が与えられる。A に x が含まれるか判定せよ。\n\nこの問題では、前提 unit までで扱った知識だけを順に使えば解ける。',
            input_format='1 行目に N x。\n2 行目に A1..AN。',
            output_format='含まれるなら Yes、そうでなければ No。',
            constraints='1 <= N <= 2 * 10^5\n使う知識は前提 unit までに限定すること。',
            examples=[
                {
                    'input': '5 3\n1 4 3 7 9',
                    'output': 'Yes',
                },
            ],
            canonical_reference_solution="def solve() -> None:\n    n, x = map(int, input().split())\n    a = list(map(int, input().split()))\n    print('Yes' if x in a else 'No')\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
        problem(
            problem_id='algo-004-integration-p2',
            title='深さ優先探索（DFS） の総合演習 / 2 ケースを連続して解く',
            problem_statement='2 ケース分の入力が続けて与えられる。それぞれについて、長さ N の整数列 A と整数 x が与えられる。A に x が含まれるか判定せよ。\n\nこの問題では、前提 unit までで扱った知識だけを順に使えば解ける。',
            input_format='1 行目に 2。\n続く 2 ケースについて:\n1 行目に N x。\n2 行目に A1..AN。',
            output_format='各ケースの答えを順に出力する。',
            constraints='1 <= N <= 2 * 10^5\n使う知識は前提 unit までに限定すること。\n2 ケースの合計でも同じ方針で処理すること。',
            examples=[
                {
                    'input': '2\n5 3\n1 4 3 7 9\n5 3\n1 4 3 7 9',
                    'output': 'Yes\nYes',
                },
            ],
            canonical_reference_solution="import io\nimport sys\nfrom contextlib import redirect_stdout\n\ndef solve_one() -> None:\n    n, x = map(int, input().split())\n    a = list(map(int, input().split()))\n    print('Yes' if x in a else 'No')\n\ndef solve() -> None:\n    t = 2\n    outputs = []\n    for _ in range(t):\n        buf = io.StringIO()\n        with redirect_stdout(buf):\n            solve_one()\n        outputs.append(buf.getvalue().rstrip('\\n'))\n    sys.stdout.write('\\n'.join(outputs))\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
        problem(
            problem_id='algo-004-integration-p3',
            title='深さ優先探索（DFS） の総合演習 / 3 ケースを連続して解く',
            problem_statement='3 ケース分の入力が続けて与えられる。それぞれについて、長さ N の整数列 A と整数 x が与えられる。A に x が含まれるか判定せよ。\n\nこの問題では、前提 unit までで扱った知識だけを順に使えば解ける。',
            input_format='1 行目に 3。\n続く 3 ケースについて:\n1 行目に N x。\n2 行目に A1..AN。',
            output_format='各ケースの答えを順に出力する。',
            constraints='1 <= N <= 2 * 10^5\n使う知識は前提 unit までに限定すること。\n3 ケースの合計でも同じ方針で処理すること。',
            examples=[
                {
                    'input': '3\n5 3\n1 4 3 7 9\n5 3\n1 4 3 7 9\n5 3\n1 4 3 7 9',
                    'output': 'Yes\nYes\nYes',
                },
            ],
            canonical_reference_solution="import io\nimport sys\nfrom contextlib import redirect_stdout\n\ndef solve_one() -> None:\n    n, x = map(int, input().split())\n    a = list(map(int, input().split()))\n    print('Yes' if x in a else 'No')\n\ndef solve() -> None:\n    t = 3\n    outputs = []\n    for _ in range(t):\n        buf = io.StringIO()\n        with redirect_stdout(buf):\n            solve_one()\n        outputs.append(buf.getvalue().rstrip('\\n'))\n    sys.stdout.write('\\n'.join(outputs))\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
