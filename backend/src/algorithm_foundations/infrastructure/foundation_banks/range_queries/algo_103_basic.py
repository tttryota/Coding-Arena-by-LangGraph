from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('foundation')

UNIT_BANK = unit_bank(
    unit_id='algo-103-basic',
    title='スパーステーブル（RMQ） の基本',
    unit_kind='foundation',
    target_skill='スパーステーブル（RMQ） の基本',
    concept_overview='スパーステーブルは、動かない配列に対して区間最小値などを何度も聞かれるときに、前計算で問い合わせを速くする知識です。『更新なし・問い合わせ多数』の形を見抜く基本を学びます。',
    problem_bank=[
        problem(
            problem_id='algo-103-basic-p1',
            title='スパーステーブル（RMQ） の基本 / 1 ケースをそのまま解く',
            problem_statement='長さ N の整数列 A と Q 個の区間 [L, R] が与えられる。前処理を行い、各区間の最小値を求めよ。',
            input_format='1 行目に N Q。\n2 行目に A1..AN。\n続く Q 行に L R。',
            output_format='各問い合わせの最小値を 1 行ずつ出力する。',
            constraints='1 <= N, Q <= 2 * 10^5',
            examples=[
                {
                    'input': '5 3\n5 2 8 1 4\n1 3\n2 5\n4 4',
                    'output': '2\n1\n1',
                },
            ],
            canonical_reference_solution="def solve() -> None:\n    import sys\n    input = sys.stdin.readline\n    n, q = map(int, input().split())\n    a = list(map(int, input().split()))\n    log = [0] * (n + 1)\n    for i in range(2, n + 1):\n        log[i] = log[i // 2] + 1\n    st = [a[:]]\n    j = 1\n    while (1 << j) <= n:\n        prev = st[-1]\n        width = 1 << j\n        half = width >> 1\n        row = [0] * (n - width + 1)\n        for i in range(n - width + 1):\n            row[i] = min(prev[i], prev[i + half])\n        st.append(row)\n        j += 1\n    out = []\n    for _ in range(q):\n        l, r = map(int, input().split())\n        l -= 1\n        r -= 1\n        length = r - l + 1\n        j = log[length]\n        out.append(str(min(st[j][l], st[j][r - (1 << j) + 1])))\n    sys.stdout.write('\\n'.join(out))\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
        problem(
            problem_id='algo-103-basic-p2',
            title='スパーステーブル（RMQ） の基本 / 2 ケースを連続して解く',
            problem_statement='2 ケース分の入力が続けて与えられる。それぞれについて、長さ N の整数列 A と Q 個の区間 [L, R] が与えられる。前処理を行い、各区間の最小値を求めよ。',
            input_format='1 行目に 2。\n続く 2 ケースについて:\n1 行目に N Q。\n2 行目に A1..AN。\n続く Q 行に L R。',
            output_format='各ケースの答えを順に出力する。',
            constraints='1 <= N, Q <= 2 * 10^5\n2 ケースの合計でも同じ方針で処理すること。',
            examples=[
                {
                    'input': '2\n5 3\n5 2 8 1 4\n1 3\n2 5\n4 4\n5 3\n5 2 8 1 4\n1 3\n2 5\n4 4',
                    'output': '2\n1\n1\n2\n1\n1',
                },
            ],
            canonical_reference_solution="import io\nimport sys\nfrom contextlib import redirect_stdout\n\ndef solve_one() -> None:\n    import sys\n    input = sys.stdin.readline\n    n, q = map(int, input().split())\n    a = list(map(int, input().split()))\n    log = [0] * (n + 1)\n    for i in range(2, n + 1):\n        log[i] = log[i // 2] + 1\n    st = [a[:]]\n    j = 1\n    while (1 << j) <= n:\n        prev = st[-1]\n        width = 1 << j\n        half = width >> 1\n        row = [0] * (n - width + 1)\n        for i in range(n - width + 1):\n            row[i] = min(prev[i], prev[i + half])\n        st.append(row)\n        j += 1\n    out = []\n    for _ in range(q):\n        l, r = map(int, input().split())\n        l -= 1\n        r -= 1\n        length = r - l + 1\n        j = log[length]\n        out.append(str(min(st[j][l], st[j][r - (1 << j) + 1])))\n    sys.stdout.write('\\n'.join(out))\n\ndef solve() -> None:\n    t = 2\n    outputs = []\n    for _ in range(t):\n        buf = io.StringIO()\n        with redirect_stdout(buf):\n            solve_one()\n        outputs.append(buf.getvalue().rstrip('\\n'))\n    sys.stdout.write('\\n'.join(outputs))\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
        problem(
            problem_id='algo-103-basic-p3',
            title='スパーステーブル（RMQ） の基本 / 3 ケースを連続して解く',
            problem_statement='3 ケース分の入力が続けて与えられる。それぞれについて、長さ N の整数列 A と Q 個の区間 [L, R] が与えられる。前処理を行い、各区間の最小値を求めよ。',
            input_format='1 行目に 3。\n続く 3 ケースについて:\n1 行目に N Q。\n2 行目に A1..AN。\n続く Q 行に L R。',
            output_format='各ケースの答えを順に出力する。',
            constraints='1 <= N, Q <= 2 * 10^5\n3 ケースの合計でも同じ方針で処理すること。',
            examples=[
                {
                    'input': '3\n5 3\n5 2 8 1 4\n1 3\n2 5\n4 4\n5 3\n5 2 8 1 4\n1 3\n2 5\n4 4\n5 3\n5 2 8 1 4\n1 3\n2 5\n4 4',
                    'output': '2\n1\n1\n2\n1\n1\n2\n1\n1',
                },
            ],
            canonical_reference_solution="import io\nimport sys\nfrom contextlib import redirect_stdout\n\ndef solve_one() -> None:\n    import sys\n    input = sys.stdin.readline\n    n, q = map(int, input().split())\n    a = list(map(int, input().split()))\n    log = [0] * (n + 1)\n    for i in range(2, n + 1):\n        log[i] = log[i // 2] + 1\n    st = [a[:]]\n    j = 1\n    while (1 << j) <= n:\n        prev = st[-1]\n        width = 1 << j\n        half = width >> 1\n        row = [0] * (n - width + 1)\n        for i in range(n - width + 1):\n            row[i] = min(prev[i], prev[i + half])\n        st.append(row)\n        j += 1\n    out = []\n    for _ in range(q):\n        l, r = map(int, input().split())\n        l -= 1\n        r -= 1\n        length = r - l + 1\n        j = log[length]\n        out.append(str(min(st[j][l], st[j][r - (1 << j) + 1])))\n    sys.stdout.write('\\n'.join(out))\n\ndef solve() -> None:\n    t = 3\n    outputs = []\n    for _ in range(t):\n        buf = io.StringIO()\n        with redirect_stdout(buf):\n            solve_one()\n        outputs.append(buf.getvalue().rstrip('\\n'))\n    sys.stdout.write('\\n'.join(outputs))\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
