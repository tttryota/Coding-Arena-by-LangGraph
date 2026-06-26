from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('foundation')

UNIT_BANK = unit_bank(
    unit_id='algo-104-practice',
    title='単調スタック を素直に実装する',
    unit_kind='foundation',
    target_skill='単調スタック を素直に実装する',
    concept_overview='スタックは、最後に入れたものを先に取り出す考え方です。直前の状態や未処理の情報をあとから回収したい場面で使います。',
    problem_bank=[
        problem(
            problem_id='algo-104-practice-p1',
            title='単調スタック を素直に実装する / 1 ケースをそのまま解く',
            problem_statement='長さ N の整数列 A が与えられる。各 i について、i より左で `A_j < A_i` を満たす最も近い位置 j を求め、 存在しなければ -1 を出力せよ。',
            input_format='1 行目に N。\n2 行目に A1..AN。',
            output_format='N 個の答えを空白区切りで出力する。',
            constraints='1 <= N <= 2 * 10^5',
            examples=[
                {
                    'input': '5\n3 7 4 6 2',
                    'output': '-1 1 1 3 -1',
                },
            ],
            canonical_reference_solution="def solve() -> None:\n    input()\n    a = list(map(int, input().split()))\n    stack = []\n    ans = []\n    for i, value in enumerate(a, start=1):\n        while stack and stack[-1][0] >= value:\n            stack.pop()\n        ans.append(stack[-1][1] if stack else -1)\n        stack.append((value, i))\n    print(*ans)\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
        problem(
            problem_id='algo-104-practice-p2',
            title='単調スタック を素直に実装する / 2 ケースを連続して解く',
            problem_statement='2 ケース分の入力が続けて与えられる。それぞれについて、長さ N の整数列 A が与えられる。各 i について、i より左で `A_j < A_i` を満たす最も近い位置 j を求め、 存在しなければ -1 を出力せよ。',
            input_format='1 行目に 2。\n続く 2 ケースについて:\n1 行目に N。\n2 行目に A1..AN。',
            output_format='各ケースの答えを順に出力する。',
            constraints='1 <= N <= 2 * 10^5\n2 ケースの合計でも同じ方針で処理すること。',
            examples=[
                {
                    'input': '2\n5\n3 7 4 6 2\n5\n3 7 4 6 2',
                    'output': '-1 1 1 3 -1\n-1 1 1 3 -1',
                },
            ],
            canonical_reference_solution="import io\nimport sys\nfrom contextlib import redirect_stdout\n\ndef solve_one() -> None:\n    input()\n    a = list(map(int, input().split()))\n    stack = []\n    ans = []\n    for i, value in enumerate(a, start=1):\n        while stack and stack[-1][0] >= value:\n            stack.pop()\n        ans.append(stack[-1][1] if stack else -1)\n        stack.append((value, i))\n    print(*ans)\n\ndef solve() -> None:\n    t = 2\n    outputs = []\n    for _ in range(t):\n        buf = io.StringIO()\n        with redirect_stdout(buf):\n            solve_one()\n        outputs.append(buf.getvalue().rstrip('\\n'))\n    sys.stdout.write('\\n'.join(outputs))\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
        problem(
            problem_id='algo-104-practice-p3',
            title='単調スタック を素直に実装する / 3 ケースを連続して解く',
            problem_statement='3 ケース分の入力が続けて与えられる。それぞれについて、長さ N の整数列 A が与えられる。各 i について、i より左で `A_j < A_i` を満たす最も近い位置 j を求め、 存在しなければ -1 を出力せよ。',
            input_format='1 行目に 3。\n続く 3 ケースについて:\n1 行目に N。\n2 行目に A1..AN。',
            output_format='各ケースの答えを順に出力する。',
            constraints='1 <= N <= 2 * 10^5\n3 ケースの合計でも同じ方針で処理すること。',
            examples=[
                {
                    'input': '3\n5\n3 7 4 6 2\n5\n3 7 4 6 2\n5\n3 7 4 6 2',
                    'output': '-1 1 1 3 -1\n-1 1 1 3 -1\n-1 1 1 3 -1',
                },
            ],
            canonical_reference_solution="import io\nimport sys\nfrom contextlib import redirect_stdout\n\ndef solve_one() -> None:\n    input()\n    a = list(map(int, input().split()))\n    stack = []\n    ans = []\n    for i, value in enumerate(a, start=1):\n        while stack and stack[-1][0] >= value:\n            stack.pop()\n        ans.append(stack[-1][1] if stack else -1)\n        stack.append((value, i))\n    print(*ans)\n\ndef solve() -> None:\n    t = 3\n    outputs = []\n    for _ in range(t):\n        buf = io.StringIO()\n        with redirect_stdout(buf):\n            solve_one()\n        outputs.append(buf.getvalue().rstrip('\\n'))\n    sys.stdout.write('\\n'.join(outputs))\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
        problem(
            problem_id='algo-104-practice-p4',
            title='単調スタック を素直に実装する / T ケースをまとめて解く',
            problem_statement='1 行目にケース数 T が与えられる。続く T ケースについて、それぞれ 長さ N の整数列 A が与えられる。各 i について、i より左で `A_j < A_i` を満たす最も近い位置 j を求め、 存在しなければ -1 を出力せよ。',
            input_format='1 行目に T。\n続く T ケースについて:\n1 行目に N。\n2 行目に A1..AN。',
            output_format='各ケースの答えを順に出力する。',
            constraints='1 <= N <= 2 * 10^5\n1 <= T\n全ケースの合計サイズでも同じ方針で処理すること。',
            examples=[
                {
                    'input': '3\n5\n3 7 4 6 2\n5\n3 7 4 6 2\n5\n3 7 4 6 2',
                    'output': '-1 1 1 3 -1\n-1 1 1 3 -1\n-1 1 1 3 -1',
                },
            ],
            canonical_reference_solution="import io\nimport sys\nfrom contextlib import redirect_stdout\n\ndef solve_one() -> None:\n    input()\n    a = list(map(int, input().split()))\n    stack = []\n    ans = []\n    for i, value in enumerate(a, start=1):\n        while stack and stack[-1][0] >= value:\n            stack.pop()\n        ans.append(stack[-1][1] if stack else -1)\n        stack.append((value, i))\n    print(*ans)\n\ndef solve() -> None:\n    t = int(input())\n    outputs = []\n    for _ in range(t):\n        buf = io.StringIO()\n        with redirect_stdout(buf):\n            solve_one()\n        outputs.append(buf.getvalue().rstrip('\\n'))\n    sys.stdout.write('\\n'.join(outputs))\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
        problem(
            problem_id='algo-104-practice-p5',
            title='単調スタック を素直に実装する / 4 ケースを連続して解く',
            problem_statement='4 ケース分の入力が続けて与えられる。それぞれについて、長さ N の整数列 A が与えられる。各 i について、i より左で `A_j < A_i` を満たす最も近い位置 j を求め、 存在しなければ -1 を出力せよ。',
            input_format='1 行目に 4。\n続く 4 ケースについて:\n1 行目に N。\n2 行目に A1..AN。',
            output_format='各ケースの答えを順に出力する。',
            constraints='1 <= N <= 2 * 10^5\n4 ケースの合計でも同じ方針で処理すること。',
            examples=[
                {
                    'input': '4\n5\n3 7 4 6 2\n5\n3 7 4 6 2\n5\n3 7 4 6 2\n5\n3 7 4 6 2',
                    'output': '-1 1 1 3 -1\n-1 1 1 3 -1\n-1 1 1 3 -1\n-1 1 1 3 -1',
                },
            ],
            canonical_reference_solution="import io\nimport sys\nfrom contextlib import redirect_stdout\n\ndef solve_one() -> None:\n    input()\n    a = list(map(int, input().split()))\n    stack = []\n    ans = []\n    for i, value in enumerate(a, start=1):\n        while stack and stack[-1][0] >= value:\n            stack.pop()\n        ans.append(stack[-1][1] if stack else -1)\n        stack.append((value, i))\n    print(*ans)\n\ndef solve() -> None:\n    t = 4\n    outputs = []\n    for _ in range(t):\n        buf = io.StringIO()\n        with redirect_stdout(buf):\n            solve_one()\n        outputs.append(buf.getvalue().rstrip('\\n'))\n    sys.stdout.write('\\n'.join(outputs))\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
        problem(
            problem_id='algo-104-practice-p6',
            title='単調スタック を素直に実装する / 5 ケースを連続して解く',
            problem_statement='5 ケース分の入力が続けて与えられる。それぞれについて、長さ N の整数列 A が与えられる。各 i について、i より左で `A_j < A_i` を満たす最も近い位置 j を求め、 存在しなければ -1 を出力せよ。',
            input_format='1 行目に 5。\n続く 5 ケースについて:\n1 行目に N。\n2 行目に A1..AN。',
            output_format='各ケースの答えを順に出力する。',
            constraints='1 <= N <= 2 * 10^5\n5 ケースの合計でも同じ方針で処理すること。',
            examples=[
                {
                    'input': '5\n5\n3 7 4 6 2\n5\n3 7 4 6 2\n5\n3 7 4 6 2\n5\n3 7 4 6 2\n5\n3 7 4 6 2',
                    'output': '-1 1 1 3 -1\n-1 1 1 3 -1\n-1 1 1 3 -1\n-1 1 1 3 -1\n-1 1 1 3 -1',
                },
            ],
            canonical_reference_solution="import io\nimport sys\nfrom contextlib import redirect_stdout\n\ndef solve_one() -> None:\n    input()\n    a = list(map(int, input().split()))\n    stack = []\n    ans = []\n    for i, value in enumerate(a, start=1):\n        while stack and stack[-1][0] >= value:\n            stack.pop()\n        ans.append(stack[-1][1] if stack else -1)\n        stack.append((value, i))\n    print(*ans)\n\ndef solve() -> None:\n    t = 5\n    outputs = []\n    for _ in range(t):\n        buf = io.StringIO()\n        with redirect_stdout(buf):\n            solve_one()\n        outputs.append(buf.getvalue().rstrip('\\n'))\n    sys.stdout.write('\\n'.join(outputs))\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
