from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('foundation')

UNIT_BANK = unit_bank(
    unit_id='algo-037-practice',
    title='最長増加部分列（LIS） を素直に実装する',
    unit_kind='foundation',
    target_skill='最長増加部分列（LIS） を素直に実装する',
    concept_overview='動的計画法は、小さい状態の答えを先に求め、その結果を使って大きい状態の答えを作る考え方です。状態・遷移・初期値を整理する基本を身につけます。',
    problem_bank=[
        problem(
            problem_id='algo-037-practice-p1',
            title='最長増加部分列（LIS） を素直に実装する / 1 ケースをそのまま解く',
            problem_statement='長さ N の整数列 A が与えられる。最長増加部分列の長さを求めよ。',
            input_format='1 行目に N。\n2 行目に A1..AN。',
            output_format='LIS の長さを出力する。',
            constraints='1 <= N <= 2 * 10^5',
            examples=[
                {
                    'input': '6\n3 1 4 1 5 9',
                    'output': '4',
                },
            ],
            canonical_reference_solution="from bisect import bisect_left\n\ndef solve() -> None:\n    import sys\n    input = sys.stdin.readline\n    _ = int(input())\n    a = list(map(int, input().split()))\n    dp = []\n    for value in a:\n        i = bisect_left(dp, value)\n        if i == len(dp):\n            dp.append(value)\n        else:\n            dp[i] = value\n    print(len(dp))\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
        problem(
            problem_id='algo-037-practice-p2',
            title='最長増加部分列（LIS） を素直に実装する / 2 ケースを連続して解く',
            problem_statement='2 ケース分の入力が続けて与えられる。それぞれについて、長さ N の整数列 A が与えられる。最長増加部分列の長さを求めよ。',
            input_format='1 行目に 2。\n続く 2 ケースについて:\n1 行目に N。\n2 行目に A1..AN。',
            output_format='各ケースの答えを順に出力する。',
            constraints='1 <= N <= 2 * 10^5\n2 ケースの合計でも同じ方針で処理すること。',
            examples=[
                {
                    'input': '2\n6\n3 1 4 1 5 9\n6\n3 1 4 1 5 9',
                    'output': '4\n4',
                },
            ],
            canonical_reference_solution="import io\nimport sys\nfrom contextlib import redirect_stdout\n\nfrom bisect import bisect_left\n\ndef solve_one() -> None:\n    import sys\n    input = sys.stdin.readline\n    _ = int(input())\n    a = list(map(int, input().split()))\n    dp = []\n    for value in a:\n        i = bisect_left(dp, value)\n        if i == len(dp):\n            dp.append(value)\n        else:\n            dp[i] = value\n    print(len(dp))\n\ndef solve() -> None:\n    t = 2\n    outputs = []\n    for _ in range(t):\n        buf = io.StringIO()\n        with redirect_stdout(buf):\n            solve_one()\n        outputs.append(buf.getvalue().rstrip('\\n'))\n    sys.stdout.write('\\n'.join(outputs))\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
        problem(
            problem_id='algo-037-practice-p3',
            title='最長増加部分列（LIS） を素直に実装する / 3 ケースを連続して解く',
            problem_statement='3 ケース分の入力が続けて与えられる。それぞれについて、長さ N の整数列 A が与えられる。最長増加部分列の長さを求めよ。',
            input_format='1 行目に 3。\n続く 3 ケースについて:\n1 行目に N。\n2 行目に A1..AN。',
            output_format='各ケースの答えを順に出力する。',
            constraints='1 <= N <= 2 * 10^5\n3 ケースの合計でも同じ方針で処理すること。',
            examples=[
                {
                    'input': '3\n6\n3 1 4 1 5 9\n6\n3 1 4 1 5 9\n6\n3 1 4 1 5 9',
                    'output': '4\n4\n4',
                },
            ],
            canonical_reference_solution="import io\nimport sys\nfrom contextlib import redirect_stdout\n\nfrom bisect import bisect_left\n\ndef solve_one() -> None:\n    import sys\n    input = sys.stdin.readline\n    _ = int(input())\n    a = list(map(int, input().split()))\n    dp = []\n    for value in a:\n        i = bisect_left(dp, value)\n        if i == len(dp):\n            dp.append(value)\n        else:\n            dp[i] = value\n    print(len(dp))\n\ndef solve() -> None:\n    t = 3\n    outputs = []\n    for _ in range(t):\n        buf = io.StringIO()\n        with redirect_stdout(buf):\n            solve_one()\n        outputs.append(buf.getvalue().rstrip('\\n'))\n    sys.stdout.write('\\n'.join(outputs))\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
        problem(
            problem_id='algo-037-practice-p4',
            title='最長増加部分列（LIS） を素直に実装する / T ケースをまとめて解く',
            problem_statement='1 行目にケース数 T が与えられる。続く T ケースについて、それぞれ 長さ N の整数列 A が与えられる。最長増加部分列の長さを求めよ。',
            input_format='1 行目に T。\n続く T ケースについて:\n1 行目に N。\n2 行目に A1..AN。',
            output_format='各ケースの答えを順に出力する。',
            constraints='1 <= N <= 2 * 10^5\n1 <= T\n全ケースの合計サイズでも同じ方針で処理すること。',
            examples=[
                {
                    'input': '3\n6\n3 1 4 1 5 9\n6\n3 1 4 1 5 9\n6\n3 1 4 1 5 9',
                    'output': '4\n4\n4',
                },
            ],
            canonical_reference_solution="import io\nimport sys\nfrom contextlib import redirect_stdout\n\nfrom bisect import bisect_left\n\ndef solve_one() -> None:\n    import sys\n    input = sys.stdin.readline\n    _ = int(input())\n    a = list(map(int, input().split()))\n    dp = []\n    for value in a:\n        i = bisect_left(dp, value)\n        if i == len(dp):\n            dp.append(value)\n        else:\n            dp[i] = value\n    print(len(dp))\n\ndef solve() -> None:\n    t = int(input())\n    outputs = []\n    for _ in range(t):\n        buf = io.StringIO()\n        with redirect_stdout(buf):\n            solve_one()\n        outputs.append(buf.getvalue().rstrip('\\n'))\n    sys.stdout.write('\\n'.join(outputs))\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
        problem(
            problem_id='algo-037-practice-p5',
            title='最長増加部分列（LIS） を素直に実装する / 4 ケースを連続して解く',
            problem_statement='4 ケース分の入力が続けて与えられる。それぞれについて、長さ N の整数列 A が与えられる。最長増加部分列の長さを求めよ。',
            input_format='1 行目に 4。\n続く 4 ケースについて:\n1 行目に N。\n2 行目に A1..AN。',
            output_format='各ケースの答えを順に出力する。',
            constraints='1 <= N <= 2 * 10^5\n4 ケースの合計でも同じ方針で処理すること。',
            examples=[
                {
                    'input': '4\n6\n3 1 4 1 5 9\n6\n3 1 4 1 5 9\n6\n3 1 4 1 5 9\n6\n3 1 4 1 5 9',
                    'output': '4\n4\n4\n4',
                },
            ],
            canonical_reference_solution="import io\nimport sys\nfrom contextlib import redirect_stdout\n\nfrom bisect import bisect_left\n\ndef solve_one() -> None:\n    import sys\n    input = sys.stdin.readline\n    _ = int(input())\n    a = list(map(int, input().split()))\n    dp = []\n    for value in a:\n        i = bisect_left(dp, value)\n        if i == len(dp):\n            dp.append(value)\n        else:\n            dp[i] = value\n    print(len(dp))\n\ndef solve() -> None:\n    t = 4\n    outputs = []\n    for _ in range(t):\n        buf = io.StringIO()\n        with redirect_stdout(buf):\n            solve_one()\n        outputs.append(buf.getvalue().rstrip('\\n'))\n    sys.stdout.write('\\n'.join(outputs))\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
        problem(
            problem_id='algo-037-practice-p6',
            title='最長増加部分列（LIS） を素直に実装する / 5 ケースを連続して解く',
            problem_statement='5 ケース分の入力が続けて与えられる。それぞれについて、長さ N の整数列 A が与えられる。最長増加部分列の長さを求めよ。',
            input_format='1 行目に 5。\n続く 5 ケースについて:\n1 行目に N。\n2 行目に A1..AN。',
            output_format='各ケースの答えを順に出力する。',
            constraints='1 <= N <= 2 * 10^5\n5 ケースの合計でも同じ方針で処理すること。',
            examples=[
                {
                    'input': '5\n6\n3 1 4 1 5 9\n6\n3 1 4 1 5 9\n6\n3 1 4 1 5 9\n6\n3 1 4 1 5 9\n6\n3 1 4 1 5 9',
                    'output': '4\n4\n4\n4\n4',
                },
            ],
            canonical_reference_solution="import io\nimport sys\nfrom contextlib import redirect_stdout\n\nfrom bisect import bisect_left\n\ndef solve_one() -> None:\n    import sys\n    input = sys.stdin.readline\n    _ = int(input())\n    a = list(map(int, input().split()))\n    dp = []\n    for value in a:\n        i = bisect_left(dp, value)\n        if i == len(dp):\n            dp.append(value)\n        else:\n            dp[i] = value\n    print(len(dp))\n\ndef solve() -> None:\n    t = 5\n    outputs = []\n    for _ in range(t):\n        buf = io.StringIO()\n        with redirect_stdout(buf):\n            solve_one()\n        outputs.append(buf.getvalue().rstrip('\\n'))\n    sys.stdout.write('\\n'.join(outputs))\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
