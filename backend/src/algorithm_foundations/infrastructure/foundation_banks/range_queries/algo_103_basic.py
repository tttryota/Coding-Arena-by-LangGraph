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
    concept_overview='スパーステーブルは、動かない配列に対して区間最小値などを何度も聞かれるときに、前計算で問い合わせを速くする知識です。まずは区間最小値そのものを高速に答える基本形を押さえます。',
    problem_bank=[
        problem(
            problem_id='algo-103-basic-p1',
            title='スパーステーブル（RMQ） の基本 / 前処理を行い、各区間の最小値を求める',
            problem_statement='長さ N の整数列 A と Q 個の区間 [L, R] が与えられる。前処理を行い、各区間の最小値を求めよ。',
            input_format='1 行目に N Q。\n2 行目に A1..AN。\n続く Q 行に L R。',
            output_format='各問い合わせの最小値を 1 行ずつ出力する。',
            constraints='1 <= N, Q <= 2 * 10^5\n-10^18 <= A_i <= 10^18\n1 <= L <= R <= N',
            examples=[{'input': '5 3\n5 2 8 1 4\n1 3\n2 5\n4 4', 'output': '2\n1\n1'}],
            canonical_reference_solution="def solve() -> None:\n    import sys\n    input = sys.stdin.readline\n    n, q = map(int, input().split())\n    a = list(map(int, input().split()))\n    log = [0] * (n + 1)\n    for i in range(2, n + 1):\n        log[i] = log[i // 2] + 1\n    st = [a[:]]\n    j = 1\n    while (1 << j) <= n:\n        prev = st[-1]\n        width = 1 << j\n        half = width >> 1\n        row = [0] * (n - width + 1)\n        for i in range(n - width + 1):\n            row[i] = min(prev[i], prev[i + half])\n        st.append(row)\n        j += 1\n    out = []\n    for _ in range(q):\n        l, r = map(int, input().split())\n        l -= 1\n        r -= 1\n        length = r - l + 1\n        j = log[length]\n        out.append(str(min(st[j][l], st[j][r - (1 << j) + 1])))\n    sys.stdout.write('\\n'.join(out))\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
