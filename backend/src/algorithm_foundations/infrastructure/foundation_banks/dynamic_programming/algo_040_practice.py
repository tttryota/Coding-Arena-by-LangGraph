from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('foundation')

UNIT_BANK = unit_bank(
    unit_id='algo-040-practice',
    title='区間DP を素直に実装する',
    unit_kind='foundation',
    target_skill='区間DP を素直に実装する',
    concept_overview='動的計画法は、小さい状態の答えを先に求め、その結果を使って大きい状態の答えを作る考え方です。状態・遷移・初期値を整理する基本を身につけます。',
    problem_bank=[
        problem(
            problem_id='algo-040-practice-p1',
            title='区間DP を素直に実装する / 1 ケースをそのまま解く',
            problem_statement='長さ N の正整数列 A が与えられる。 隣り合う区間を順に併合するとき、併合コストを区間和とする。 列全体を 1 つにする最小コストを求めよ。',
            input_format='1 行目に N。\n2 行目に A1..AN。',
            output_format='最小コストを出力する。',
            constraints='1 <= N <= 400\n1 <= Ai <= 10^9',
            examples=[
                {
                    'input': '4\n4 1 3 2',
                    'output': '20',
                },
            ],
            canonical_reference_solution="def solve() -> None:\n    import sys\n    input = sys.stdin.readline\n    n = int(input())\n    a = list(map(int, input().split()))\n    prefix = [0]\n    for value in a:\n        prefix.append(prefix[-1] + value)\n    dp = [[0] * n for _ in range(n)]\n    for length in range(2, n + 1):\n        for left in range(n - length + 1):\n            right = left + length - 1\n            total = prefix[right + 1] - prefix[left]\n            best = 10 ** 30\n            for mid in range(left, right):\n                best = min(best, dp[left][mid] + dp[mid + 1][right] + total)\n            dp[left][right] = best\n    print(dp[0][n - 1])\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
        problem(
            problem_id='algo-040-practice-p2',
            title='区間DP を素直に実装する / 2 ケースを連続して解く',
            problem_statement='2 ケース分の入力が続けて与えられる。それぞれについて、長さ N の正整数列 A が与えられる。 隣り合う区間を順に併合するとき、併合コストを区間和とする。 列全体を 1 つにする最小コストを求めよ。',
            input_format='1 行目に 2。\n続く 2 ケースについて:\n1 行目に N。\n2 行目に A1..AN。',
            output_format='各ケースの答えを順に出力する。',
            constraints='1 <= N <= 400\n1 <= Ai <= 10^9\n2 ケースの合計でも同じ方針で処理すること。',
            examples=[
                {
                    'input': '2\n4\n4 1 3 2\n4\n4 1 3 2',
                    'output': '20\n20',
                },
            ],
            canonical_reference_solution="import io\nimport sys\nfrom contextlib import redirect_stdout\n\ndef solve_one() -> None:\n    import sys\n    input = sys.stdin.readline\n    n = int(input())\n    a = list(map(int, input().split()))\n    prefix = [0]\n    for value in a:\n        prefix.append(prefix[-1] + value)\n    dp = [[0] * n for _ in range(n)]\n    for length in range(2, n + 1):\n        for left in range(n - length + 1):\n            right = left + length - 1\n            total = prefix[right + 1] - prefix[left]\n            best = 10 ** 30\n            for mid in range(left, right):\n                best = min(best, dp[left][mid] + dp[mid + 1][right] + total)\n            dp[left][right] = best\n    print(dp[0][n - 1])\n\ndef solve() -> None:\n    t = 2\n    outputs = []\n    for _ in range(t):\n        buf = io.StringIO()\n        with redirect_stdout(buf):\n            solve_one()\n        outputs.append(buf.getvalue().rstrip('\\n'))\n    sys.stdout.write('\\n'.join(outputs))\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
        problem(
            problem_id='algo-040-practice-p3',
            title='区間DP を素直に実装する / 3 ケースを連続して解く',
            problem_statement='3 ケース分の入力が続けて与えられる。それぞれについて、長さ N の正整数列 A が与えられる。 隣り合う区間を順に併合するとき、併合コストを区間和とする。 列全体を 1 つにする最小コストを求めよ。',
            input_format='1 行目に 3。\n続く 3 ケースについて:\n1 行目に N。\n2 行目に A1..AN。',
            output_format='各ケースの答えを順に出力する。',
            constraints='1 <= N <= 400\n1 <= Ai <= 10^9\n3 ケースの合計でも同じ方針で処理すること。',
            examples=[
                {
                    'input': '3\n4\n4 1 3 2\n4\n4 1 3 2\n4\n4 1 3 2',
                    'output': '20\n20\n20',
                },
            ],
            canonical_reference_solution="import io\nimport sys\nfrom contextlib import redirect_stdout\n\ndef solve_one() -> None:\n    import sys\n    input = sys.stdin.readline\n    n = int(input())\n    a = list(map(int, input().split()))\n    prefix = [0]\n    for value in a:\n        prefix.append(prefix[-1] + value)\n    dp = [[0] * n for _ in range(n)]\n    for length in range(2, n + 1):\n        for left in range(n - length + 1):\n            right = left + length - 1\n            total = prefix[right + 1] - prefix[left]\n            best = 10 ** 30\n            for mid in range(left, right):\n                best = min(best, dp[left][mid] + dp[mid + 1][right] + total)\n            dp[left][right] = best\n    print(dp[0][n - 1])\n\ndef solve() -> None:\n    t = 3\n    outputs = []\n    for _ in range(t):\n        buf = io.StringIO()\n        with redirect_stdout(buf):\n            solve_one()\n        outputs.append(buf.getvalue().rstrip('\\n'))\n    sys.stdout.write('\\n'.join(outputs))\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
