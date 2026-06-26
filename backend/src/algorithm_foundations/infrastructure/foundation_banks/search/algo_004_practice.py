from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('foundation')

UNIT_BANK = unit_bank(
    unit_id='algo-004-practice',
    title='深さ優先探索（DFS） を素直に実装する',
    unit_kind='foundation',
    target_skill='深さ優先探索（DFS） を素直に実装する',
    concept_overview='深さ優先探索は、行けるところまで進んでから戻る形で状態や頂点をたどる解き方です。再帰やスタックで探索順を管理する基本を学びます。',
    problem_bank=[
        problem(
            problem_id='algo-004-practice-p1',
            title='深さ優先探索（DFS） を素直に実装する / 1 ケースをそのまま解く',
            problem_statement='長さ N の整数列 A と整数 x が与えられる。A に x が含まれるか判定せよ。',
            input_format='1 行目に N x。\n2 行目に A1..AN。',
            output_format='含まれるなら Yes、そうでなければ No。',
            constraints='1 <= N <= 2 * 10^5',
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
            problem_id='algo-004-practice-p2',
            title='深さ優先探索（DFS） を素直に実装する / 2 ケースを連続して解く',
            problem_statement='2 ケース分の入力が続けて与えられる。それぞれについて、長さ N の整数列 A と整数 x が与えられる。A に x が含まれるか判定せよ。',
            input_format='1 行目に 2。\n続く 2 ケースについて:\n1 行目に N x。\n2 行目に A1..AN。',
            output_format='各ケースの答えを順に出力する。',
            constraints='1 <= N <= 2 * 10^5\n2 ケースの合計でも同じ方針で処理すること。',
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
            problem_id='algo-004-practice-p3',
            title='深さ優先探索（DFS） を素直に実装する / 3 ケースを連続して解く',
            problem_statement='3 ケース分の入力が続けて与えられる。それぞれについて、長さ N の整数列 A と整数 x が与えられる。A に x が含まれるか判定せよ。',
            input_format='1 行目に 3。\n続く 3 ケースについて:\n1 行目に N x。\n2 行目に A1..AN。',
            output_format='各ケースの答えを順に出力する。',
            constraints='1 <= N <= 2 * 10^5\n3 ケースの合計でも同じ方針で処理すること。',
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
        problem(
            problem_id='algo-004-practice-p4',
            title='深さ優先探索（DFS） を素直に実装する / T ケースをまとめて解く',
            problem_statement='1 行目にケース数 T が与えられる。続く T ケースについて、それぞれ 長さ N の整数列 A と整数 x が与えられる。A に x が含まれるか判定せよ。',
            input_format='1 行目に T。\n続く T ケースについて:\n1 行目に N x。\n2 行目に A1..AN。',
            output_format='各ケースの答えを順に出力する。',
            constraints='1 <= N <= 2 * 10^5\n1 <= T\n全ケースの合計サイズでも同じ方針で処理すること。',
            examples=[
                {
                    'input': '3\n5 3\n1 4 3 7 9\n5 3\n1 4 3 7 9\n5 3\n1 4 3 7 9',
                    'output': 'Yes\nYes\nYes',
                },
            ],
            canonical_reference_solution="import io\nimport sys\nfrom contextlib import redirect_stdout\n\ndef solve_one() -> None:\n    n, x = map(int, input().split())\n    a = list(map(int, input().split()))\n    print('Yes' if x in a else 'No')\n\ndef solve() -> None:\n    t = int(input())\n    outputs = []\n    for _ in range(t):\n        buf = io.StringIO()\n        with redirect_stdout(buf):\n            solve_one()\n        outputs.append(buf.getvalue().rstrip('\\n'))\n    sys.stdout.write('\\n'.join(outputs))\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
        problem(
            problem_id='algo-004-practice-p5',
            title='深さ優先探索（DFS） を素直に実装する / 4 ケースを連続して解く',
            problem_statement='4 ケース分の入力が続けて与えられる。それぞれについて、長さ N の整数列 A と整数 x が与えられる。A に x が含まれるか判定せよ。',
            input_format='1 行目に 4。\n続く 4 ケースについて:\n1 行目に N x。\n2 行目に A1..AN。',
            output_format='各ケースの答えを順に出力する。',
            constraints='1 <= N <= 2 * 10^5\n4 ケースの合計でも同じ方針で処理すること。',
            examples=[
                {
                    'input': '4\n5 3\n1 4 3 7 9\n5 3\n1 4 3 7 9\n5 3\n1 4 3 7 9\n5 3\n1 4 3 7 9',
                    'output': 'Yes\nYes\nYes\nYes',
                },
            ],
            canonical_reference_solution="import io\nimport sys\nfrom contextlib import redirect_stdout\n\ndef solve_one() -> None:\n    n, x = map(int, input().split())\n    a = list(map(int, input().split()))\n    print('Yes' if x in a else 'No')\n\ndef solve() -> None:\n    t = 4\n    outputs = []\n    for _ in range(t):\n        buf = io.StringIO()\n        with redirect_stdout(buf):\n            solve_one()\n        outputs.append(buf.getvalue().rstrip('\\n'))\n    sys.stdout.write('\\n'.join(outputs))\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
        problem(
            problem_id='algo-004-practice-p6',
            title='深さ優先探索（DFS） を素直に実装する / 5 ケースを連続して解く',
            problem_statement='5 ケース分の入力が続けて与えられる。それぞれについて、長さ N の整数列 A と整数 x が与えられる。A に x が含まれるか判定せよ。',
            input_format='1 行目に 5。\n続く 5 ケースについて:\n1 行目に N x。\n2 行目に A1..AN。',
            output_format='各ケースの答えを順に出力する。',
            constraints='1 <= N <= 2 * 10^5\n5 ケースの合計でも同じ方針で処理すること。',
            examples=[
                {
                    'input': '5\n5 3\n1 4 3 7 9\n5 3\n1 4 3 7 9\n5 3\n1 4 3 7 9\n5 3\n1 4 3 7 9\n5 3\n1 4 3 7 9',
                    'output': 'Yes\nYes\nYes\nYes\nYes',
                },
            ],
            canonical_reference_solution="import io\nimport sys\nfrom contextlib import redirect_stdout\n\ndef solve_one() -> None:\n    n, x = map(int, input().split())\n    a = list(map(int, input().split()))\n    print('Yes' if x in a else 'No')\n\ndef solve() -> None:\n    t = 5\n    outputs = []\n    for _ in range(t):\n        buf = io.StringIO()\n        with redirect_stdout(buf):\n            solve_one()\n        outputs.append(buf.getvalue().rstrip('\\n'))\n    sys.stdout.write('\\n'.join(outputs))\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
