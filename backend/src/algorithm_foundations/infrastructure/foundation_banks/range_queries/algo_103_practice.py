from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('foundation')

UNIT_BANK = unit_bank(
    unit_id='algo-103-practice',
    title='スパーステーブル（RMQ） を素直に実装する',
    unit_kind='foundation',
    target_skill='スパーステーブル（RMQ） を素直に実装する',
    concept_overview='スパーステーブルでは、値そのものだけでなく「どこで最小になっているか」も一緒に持たせられます。ここでは区間最小値を取る最左位置を答えます。',
    problem_bank=[
        problem(
            problem_id='algo-103-practice-p1',
            title='スパーステーブル（RMQ） を素直に実装する / 前処理を行い、各区間で最小値を取る最左位置を求める',
            problem_statement='長さ N の整数列 A と Q 個の区間 [L, R] が与えられる。前処理を行い、各区間で最小値を取る位置を 1-indexed で求めよ。最小値が複数あるときは最も左の位置を答えよ。',
            input_format='1 行目に N Q。\n2 行目に A1..AN。\n続く Q 行に L R。',
            output_format='各問い合わせの答えを 1 行ずつ出力する。',
            constraints='1 <= N, Q <= 2 * 10^5\n-10^18 <= A_i <= 10^18\n1 <= L <= R <= N',
            examples=[{'input': '5 3\n5 2 8 1 1\n1 3\n2 5\n4 5', 'output': '2\n4\n4'}],
            canonical_reference_solution="def solve() -> None:\n    import sys\n    input = sys.stdin.readline\n    n, q = map(int, input().split())\n    a = list(map(int, input().split()))\n    log = [0] * (n + 1)\n    for i in range(2, n + 1):\n        log[i] = log[i // 2] + 1\n    st = [[(value, idx) for idx, value in enumerate(a)]]\n    j = 1\n    while (1 << j) <= n:\n        prev = st[-1]\n        width = 1 << j\n        half = width >> 1\n        row = [None] * (n - width + 1)\n        for i in range(n - width + 1):\n            left = prev[i]\n            right = prev[i + half]\n            row[i] = left if left[0] < right[0] or (left[0] == right[0] and left[1] < right[1]) else right\n        st.append(row)\n        j += 1\n    out = []\n    for _ in range(q):\n        l, r = map(int, input().split())\n        l -= 1\n        r -= 1\n        length = r - l + 1\n        j = log[length]\n        left = st[j][l]\n        right = st[j][r - (1 << j) + 1]\n        ans = left if left[0] < right[0] or (left[0] == right[0] and left[1] < right[1]) else right\n        out.append(str(ans[1] + 1))\n    sys.stdout.write('\\n'.join(out))\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
        problem(
            problem_id='algo-103-practice-p2',
            title='スパーステーブル（RMQ） を素直に実装する / 前処理を行い、各区間の gcd を求める',
            problem_statement='長さ N の正整数列 A と Q 個の区間 [L, R] が与えられる。前処理を行い、各区間に含まれる値の最大公約数を求めよ。',
            input_format='1 行目に N Q。\n2 行目に A1..AN。\n続く Q 行に L R。',
            output_format='各問い合わせの gcd を 1 行ずつ出力する。',
            constraints='1 <= N, Q <= 2 * 10^5\n1 <= A_i <= 10^18\n1 <= L <= R <= N',
            examples=[{'input': '5 3\n12 18 6 15 9\n1 3\n2 5\n4 5', 'output': '6\n3\n3'}],
            canonical_reference_solution="from math import gcd\n\n\ndef solve() -> None:\n    import sys\n    input = sys.stdin.readline\n    n, q = map(int, input().split())\n    a = list(map(int, input().split()))\n    log = [0] * (n + 1)\n    for i in range(2, n + 1):\n        log[i] = log[i // 2] + 1\n    st = [a[:]]\n    j = 1\n    while (1 << j) <= n:\n        prev = st[-1]\n        width = 1 << j\n        half = width >> 1\n        row = [0] * (n - width + 1)\n        for i in range(n - width + 1):\n            row[i] = gcd(prev[i], prev[i + half])\n        st.append(row)\n        j += 1\n    out = []\n    for _ in range(q):\n        l, r = map(int, input().split())\n        l -= 1\n        r -= 1\n        length = r - l + 1\n        j = log[length]\n        out.append(str(gcd(st[j][l], st[j][r - (1 << j) + 1])))\n    sys.stdout.write('\\n'.join(out))\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
