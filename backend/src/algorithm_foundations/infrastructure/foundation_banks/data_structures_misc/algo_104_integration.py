from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('integration')

UNIT_BANK = unit_bank(
    unit_id='algo-104-integration',
    title='単調スタック の総合演習',
    unit_kind='integration',
    target_skill='単調スタック の総合演習',
    concept_overview='スタックは、最後に入れたものを先に取り出す考え方です。直前の状態や未処理の情報をあとから回収したい場面で使います。 この unit では、既習の 単調スタック の基本 と 単調スタック を素直に実装する を順に使いながら、1 問を分けて解く流れまで確認します。',
    problem_bank=[
        problem(
            problem_id='algo-104-integration-p1',
            title='単調スタック の総合演習 / 1 ケースをそのまま解く',
            problem_statement='長さ N の整数列 A が与えられる。各 i について、i より左で `A_j < A_i` を満たす最も近い位置 j を求め、 存在しなければ -1 を出力せよ。\n\nこの問題では、前提 unit までで扱った知識だけを順に使えば解ける。',
            input_format='1 行目に N。\n2 行目に A1..AN。',
            output_format='N 個の答えを空白区切りで出力する。',
            constraints='1 <= N <= 2 * 10^5\n使う知識は前提 unit までに限定すること。',
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
            problem_id='algo-104-integration-p2',
            title='単調スタック の総合演習 / 2 ケースを連続して解く',
            problem_statement='2 ケース分の入力が続けて与えられる。それぞれについて、長さ N の整数列 A が与えられる。各 i について、i より左で `A_j < A_i` を満たす最も近い位置 j を求め、 存在しなければ -1 を出力せよ。\n\nこの問題では、前提 unit までで扱った知識だけを順に使えば解ける。',
            input_format='1 行目に 2。\n続く 2 ケースについて:\n1 行目に N。\n2 行目に A1..AN。',
            output_format='各ケースの答えを順に出力する。',
            constraints='1 <= N <= 2 * 10^5\n使う知識は前提 unit までに限定すること。\n2 ケースの合計でも同じ方針で処理すること。',
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
            problem_id='algo-104-integration-p3',
            title='単調スタック の総合演習 / 3 ケースを連続して解く',
            problem_statement='3 ケース分の入力が続けて与えられる。それぞれについて、長さ N の整数列 A が与えられる。各 i について、i より左で `A_j < A_i` を満たす最も近い位置 j を求め、 存在しなければ -1 を出力せよ。\n\nこの問題では、前提 unit までで扱った知識だけを順に使えば解ける。',
            input_format='1 行目に 3。\n続く 3 ケースについて:\n1 行目に N。\n2 行目に A1..AN。',
            output_format='各ケースの答えを順に出力する。',
            constraints='1 <= N <= 2 * 10^5\n使う知識は前提 unit までに限定すること。\n3 ケースの合計でも同じ方針で処理すること。',
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
    ],
)
