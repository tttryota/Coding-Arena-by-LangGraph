from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('foundation')

UNIT_BANK = unit_bank(
    unit_id='algo-105-basic',
    title='単調デック（スライド最小値） の基本',
    unit_kind='foundation',
    target_skill='単調デック（スライド最小値） の基本',
    concept_overview='デックは、前後どちらの端からも追加・削除できる考え方です。両端を使い分けながら状態を保つ場面で使います。',
    problem_bank=[
        problem(
            problem_id='algo-105-basic-p1',
            title='単調デック（スライド最小値） の基本 / 1 ケースをそのまま解く',
            problem_statement='長さ N の整数列 A と幅 K が与えられる。 各長さ K の連続部分列について最小値を求めよ。',
            input_format='1 行目に N K。\n2 行目に A1..AN。',
            output_format='各区間の最小値を空白区切りで出力する。',
            constraints='1 <= K <= N <= 2 * 10^5',
            examples=[
                {
                    'input': '7 3\n4 2 5 1 6 3 7',
                    'output': '2 1 1 1 3',
                },
            ],
            canonical_reference_solution="from collections import deque\n\ndef solve() -> None:\n    n, k = map(int, input().split())\n    a = list(map(int, input().split()))\n    dq = deque()\n    ans = []\n    for i, value in enumerate(a):\n        while dq and a[dq[-1]] >= value:\n            dq.pop()\n        dq.append(i)\n        if dq[0] <= i - k:\n            dq.popleft()\n        if i >= k - 1:\n            ans.append(a[dq[0]])\n    print(*ans)\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
        problem(
            problem_id='algo-105-basic-p2',
            title='単調デック（スライド最小値） の基本 / 2 ケースを連続して解く',
            problem_statement='2 ケース分の入力が続けて与えられる。それぞれについて、長さ N の整数列 A と幅 K が与えられる。 各長さ K の連続部分列について最小値を求めよ。',
            input_format='1 行目に 2。\n続く 2 ケースについて:\n1 行目に N K。\n2 行目に A1..AN。',
            output_format='各ケースの答えを順に出力する。',
            constraints='1 <= K <= N <= 2 * 10^5\n2 ケースの合計でも同じ方針で処理すること。',
            examples=[
                {
                    'input': '2\n7 3\n4 2 5 1 6 3 7\n7 3\n4 2 5 1 6 3 7',
                    'output': '2 1 1 1 3\n2 1 1 1 3',
                },
            ],
            canonical_reference_solution="import io\nimport sys\nfrom contextlib import redirect_stdout\n\nfrom collections import deque\n\ndef solve_one() -> None:\n    n, k = map(int, input().split())\n    a = list(map(int, input().split()))\n    dq = deque()\n    ans = []\n    for i, value in enumerate(a):\n        while dq and a[dq[-1]] >= value:\n            dq.pop()\n        dq.append(i)\n        if dq[0] <= i - k:\n            dq.popleft()\n        if i >= k - 1:\n            ans.append(a[dq[0]])\n    print(*ans)\n\ndef solve() -> None:\n    t = 2\n    outputs = []\n    for _ in range(t):\n        buf = io.StringIO()\n        with redirect_stdout(buf):\n            solve_one()\n        outputs.append(buf.getvalue().rstrip('\\n'))\n    sys.stdout.write('\\n'.join(outputs))\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
        problem(
            problem_id='algo-105-basic-p3',
            title='単調デック（スライド最小値） の基本 / 3 ケースを連続して解く',
            problem_statement='3 ケース分の入力が続けて与えられる。それぞれについて、長さ N の整数列 A と幅 K が与えられる。 各長さ K の連続部分列について最小値を求めよ。',
            input_format='1 行目に 3。\n続く 3 ケースについて:\n1 行目に N K。\n2 行目に A1..AN。',
            output_format='各ケースの答えを順に出力する。',
            constraints='1 <= K <= N <= 2 * 10^5\n3 ケースの合計でも同じ方針で処理すること。',
            examples=[
                {
                    'input': '3\n7 3\n4 2 5 1 6 3 7\n7 3\n4 2 5 1 6 3 7\n7 3\n4 2 5 1 6 3 7',
                    'output': '2 1 1 1 3\n2 1 1 1 3\n2 1 1 1 3',
                },
            ],
            canonical_reference_solution="import io\nimport sys\nfrom contextlib import redirect_stdout\n\nfrom collections import deque\n\ndef solve_one() -> None:\n    n, k = map(int, input().split())\n    a = list(map(int, input().split()))\n    dq = deque()\n    ans = []\n    for i, value in enumerate(a):\n        while dq and a[dq[-1]] >= value:\n            dq.pop()\n        dq.append(i)\n        if dq[0] <= i - k:\n            dq.popleft()\n        if i >= k - 1:\n            ans.append(a[dq[0]])\n    print(*ans)\n\ndef solve() -> None:\n    t = 3\n    outputs = []\n    for _ in range(t):\n        buf = io.StringIO()\n        with redirect_stdout(buf):\n            solve_one()\n        outputs.append(buf.getvalue().rstrip('\\n'))\n    sys.stdout.write('\\n'.join(outputs))\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
