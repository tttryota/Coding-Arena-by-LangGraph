from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('foundation')

UNIT_BANK = unit_bank(
    unit_id='algo-056-practice',
    title='マッチングの貪欲構成 を素直に実装する',
    unit_kind='foundation',
    target_skill='マッチングの貪欲構成 を素直に実装する',
    concept_overview='貪欲法は、その時点で最もよさそうな選択を順に確定していく考え方です。後戻りせずに決めてよい条件を見抜く基本を学びます。',
    problem_bank=[
        problem(
            problem_id='algo-056-practice-p1',
            title='マッチングの貪欲構成 を素直に実装する / 1 ケースをそのまま解く',
            problem_statement='長さ N の整数列 A と長さ M の整数列 B が与えられる。各 A_i を、自分以上の B_j と高々 1 回ずつ組にできるとする。作れる組数の最大値を求めよ。',
            input_format='1 行目に N M。\n2 行目に A1..AN。\n3 行目に B1..BM。',
            output_format='作れる組数の最大値を出力する。',
            constraints='1 <= N, M <= 2 * 10^5\n0 <= Ai, Bj <= 10^9',
            examples=[
                {
                    'input': '4 5\n2 4 8 9\n1 3 4 10 10',
                    'output': '3',
                },
            ],
            canonical_reference_solution="def solve() -> None:\n    input()\n    a = sorted(map(int, input().split()))\n    b = sorted(map(int, input().split()))\n    i = j = ans = 0\n    while i < len(a) and j < len(b):\n        if b[j] >= a[i]:\n            ans += 1\n            i += 1\n            j += 1\n        else:\n            j += 1\n    print(ans)\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
        problem(
            problem_id='algo-056-practice-p2',
            title='マッチングの貪欲構成 を素直に実装する / 2 ケースを連続して解く',
            problem_statement='2 ケース分の入力が続けて与えられる。それぞれについて、長さ N の整数列 A と長さ M の整数列 B が与えられる。各 A_i を、自分以上の B_j と高々 1 回ずつ組にできるとする。作れる組数の最大値を求めよ。',
            input_format='1 行目に 2。\n続く 2 ケースについて:\n1 行目に N M。\n2 行目に A1..AN。\n3 行目に B1..BM。',
            output_format='各ケースの答えを順に出力する。',
            constraints='1 <= N, M <= 2 * 10^5\n0 <= Ai, Bj <= 10^9\n2 ケースの合計でも同じ方針で処理すること。',
            examples=[
                {
                    'input': '2\n4 5\n2 4 8 9\n1 3 4 10 10\n4 5\n2 4 8 9\n1 3 4 10 10',
                    'output': '3\n3',
                },
            ],
            canonical_reference_solution="import io\nimport sys\nfrom contextlib import redirect_stdout\n\ndef solve_one() -> None:\n    input()\n    a = sorted(map(int, input().split()))\n    b = sorted(map(int, input().split()))\n    i = j = ans = 0\n    while i < len(a) and j < len(b):\n        if b[j] >= a[i]:\n            ans += 1\n            i += 1\n            j += 1\n        else:\n            j += 1\n    print(ans)\n\ndef solve() -> None:\n    t = 2\n    outputs = []\n    for _ in range(t):\n        buf = io.StringIO()\n        with redirect_stdout(buf):\n            solve_one()\n        outputs.append(buf.getvalue().rstrip('\\n'))\n    sys.stdout.write('\\n'.join(outputs))\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
        problem(
            problem_id='algo-056-practice-p3',
            title='マッチングの貪欲構成 を素直に実装する / 3 ケースを連続して解く',
            problem_statement='3 ケース分の入力が続けて与えられる。それぞれについて、長さ N の整数列 A と長さ M の整数列 B が与えられる。各 A_i を、自分以上の B_j と高々 1 回ずつ組にできるとする。作れる組数の最大値を求めよ。',
            input_format='1 行目に 3。\n続く 3 ケースについて:\n1 行目に N M。\n2 行目に A1..AN。\n3 行目に B1..BM。',
            output_format='各ケースの答えを順に出力する。',
            constraints='1 <= N, M <= 2 * 10^5\n0 <= Ai, Bj <= 10^9\n3 ケースの合計でも同じ方針で処理すること。',
            examples=[
                {
                    'input': '3\n4 5\n2 4 8 9\n1 3 4 10 10\n4 5\n2 4 8 9\n1 3 4 10 10\n4 5\n2 4 8 9\n1 3 4 10 10',
                    'output': '3\n3\n3',
                },
            ],
            canonical_reference_solution="import io\nimport sys\nfrom contextlib import redirect_stdout\n\ndef solve_one() -> None:\n    input()\n    a = sorted(map(int, input().split()))\n    b = sorted(map(int, input().split()))\n    i = j = ans = 0\n    while i < len(a) and j < len(b):\n        if b[j] >= a[i]:\n            ans += 1\n            i += 1\n            j += 1\n        else:\n            j += 1\n    print(ans)\n\ndef solve() -> None:\n    t = 3\n    outputs = []\n    for _ in range(t):\n        buf = io.StringIO()\n        with redirect_stdout(buf):\n            solve_one()\n        outputs.append(buf.getvalue().rstrip('\\n'))\n    sys.stdout.write('\\n'.join(outputs))\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
