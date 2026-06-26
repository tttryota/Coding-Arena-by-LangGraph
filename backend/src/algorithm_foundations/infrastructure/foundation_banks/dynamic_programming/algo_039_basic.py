from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('foundation')

UNIT_BANK = unit_bank(
    unit_id='algo-039-basic',
    title='編集距離（レーベンシュタイン距離） の基本',
    unit_kind='foundation',
    target_skill='編集距離（レーベンシュタイン距離） の基本',
    concept_overview='動的計画法は、小さい状態の答えを先に求め、その結果を使って大きい状態の答えを作る考え方です。状態・遷移・初期値を整理する基本を身につけます。',
    problem_bank=[
        problem(
            problem_id='algo-039-basic-p1',
            title='編集距離（レーベンシュタイン距離） の基本 / 1 ケースをそのまま解く',
            problem_statement='2 つの文字列 S, T が与えられる。編集距離を求めよ。',
            input_format='1 行目に S。\n2 行目に T。',
            output_format='編集距離を出力する。',
            constraints='1 <= |S|, |T| <= 2000',
            examples=[
                {
                    'input': 'kitten\nsitting',
                    'output': '3',
                },
            ],
            canonical_reference_solution="def solve() -> None:\n    s = input().strip()\n    t = input().strip()\n    dp = [[0] * (len(t) + 1) for _ in range(len(s) + 1)]\n    for i in range(len(s) + 1):\n        dp[i][0] = i\n    for j in range(len(t) + 1):\n        dp[0][j] = j\n    for i, ch in enumerate(s, start=1):\n        for j, tch in enumerate(t, start=1):\n            cost = 0 if ch == tch else 1\n            dp[i][j] = min(dp[i - 1][j] + 1, dp[i][j - 1] + 1, dp[i - 1][j - 1] + cost)\n    print(dp[-1][-1])\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
        problem(
            problem_id='algo-039-basic-p2',
            title='編集距離（レーベンシュタイン距離） の基本 / 2 ケースを連続して解く',
            problem_statement='2 ケース分の入力が続けて与えられる。それぞれについて、2 つの文字列 S, T が与えられる。編集距離を求めよ。',
            input_format='1 行目に 2。\n続く 2 ケースについて:\n1 行目に S。\n2 行目に T。',
            output_format='各ケースの答えを順に出力する。',
            constraints='1 <= |S|, |T| <= 2000\n2 ケースの合計でも同じ方針で処理すること。',
            examples=[
                {
                    'input': '2\nkitten\nsitting\nkitten\nsitting',
                    'output': '3\n3',
                },
            ],
            canonical_reference_solution="import io\nimport sys\nfrom contextlib import redirect_stdout\n\ndef solve_one() -> None:\n    s = input().strip()\n    t = input().strip()\n    dp = [[0] * (len(t) + 1) for _ in range(len(s) + 1)]\n    for i in range(len(s) + 1):\n        dp[i][0] = i\n    for j in range(len(t) + 1):\n        dp[0][j] = j\n    for i, ch in enumerate(s, start=1):\n        for j, tch in enumerate(t, start=1):\n            cost = 0 if ch == tch else 1\n            dp[i][j] = min(dp[i - 1][j] + 1, dp[i][j - 1] + 1, dp[i - 1][j - 1] + cost)\n    print(dp[-1][-1])\n\ndef solve() -> None:\n    t = 2\n    outputs = []\n    for _ in range(t):\n        buf = io.StringIO()\n        with redirect_stdout(buf):\n            solve_one()\n        outputs.append(buf.getvalue().rstrip('\\n'))\n    sys.stdout.write('\\n'.join(outputs))\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
        problem(
            problem_id='algo-039-basic-p3',
            title='編集距離（レーベンシュタイン距離） の基本 / 3 ケースを連続して解く',
            problem_statement='3 ケース分の入力が続けて与えられる。それぞれについて、2 つの文字列 S, T が与えられる。編集距離を求めよ。',
            input_format='1 行目に 3。\n続く 3 ケースについて:\n1 行目に S。\n2 行目に T。',
            output_format='各ケースの答えを順に出力する。',
            constraints='1 <= |S|, |T| <= 2000\n3 ケースの合計でも同じ方針で処理すること。',
            examples=[
                {
                    'input': '3\nkitten\nsitting\nkitten\nsitting\nkitten\nsitting',
                    'output': '3\n3\n3',
                },
            ],
            canonical_reference_solution="import io\nimport sys\nfrom contextlib import redirect_stdout\n\ndef solve_one() -> None:\n    s = input().strip()\n    t = input().strip()\n    dp = [[0] * (len(t) + 1) for _ in range(len(s) + 1)]\n    for i in range(len(s) + 1):\n        dp[i][0] = i\n    for j in range(len(t) + 1):\n        dp[0][j] = j\n    for i, ch in enumerate(s, start=1):\n        for j, tch in enumerate(t, start=1):\n            cost = 0 if ch == tch else 1\n            dp[i][j] = min(dp[i - 1][j] + 1, dp[i][j - 1] + 1, dp[i - 1][j - 1] + cost)\n    print(dp[-1][-1])\n\ndef solve() -> None:\n    t = 3\n    outputs = []\n    for _ in range(t):\n        buf = io.StringIO()\n        with redirect_stdout(buf):\n            solve_one()\n        outputs.append(buf.getvalue().rstrip('\\n'))\n    sys.stdout.write('\\n'.join(outputs))\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
