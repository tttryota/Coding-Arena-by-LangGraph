from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('foundation')

UNIT_BANK = unit_bank(
    unit_id='algo-060-practice',
    title='イベントソートによる走査 を素直に実装する',
    unit_kind='foundation',
    target_skill='イベントソートによる走査 を素直に実装する',
    concept_overview='開始・終了イベントに加えて「この時刻の状態を知りたい」という問い合わせも、同じ時間軸の上で処理できます。半開区間 [L, R) では、時刻 t の答えは t にある増減を反映した直後の状態になります。',
    problem_bank=[
        problem(
            problem_id='algo-060-practice-p1',
            title='イベントソートによる走査 を素直に実装する / 各問い合わせ時刻に存在するイベント数を求める',
            problem_statement='N 個のイベントの開始時刻 L_i と終了時刻 R_i、および M 個の問い合わせ時刻 T_j が与えられる。各イベントは区間 [L_i, R_i) の間だけ存在する。各 T_j について、その時刻に存在するイベント数を求めよ。',
            input_format='1 行目に N M。\n続く N 行に L_i R_i。\n続く M 行に T_j。',
            output_format='各問い合わせの答えを 1 行ずつ出力する。',
            constraints='1 <= N, M <= 2 * 10^5\n0 <= L_i < R_i <= 10^9\n0 <= T_j <= 10^9',
            examples=[{'input': '4 5\n1 4\n2 5\n5 7\n6 8\n1\n4\n5\n6\n8', 'output': '1\n1\n1\n2\n0'}],
            canonical_reference_solution="def solve() -> None:\n    import sys\n\n    input = sys.stdin.readline\n    n, m = map(int, input().split())\n    diff = {}\n    for _ in range(n):\n        l, r = map(int, input().split())\n        diff[l] = diff.get(l, 0) + 1\n        diff[r] = diff.get(r, 0) - 1\n\n    queries = [int(input()) for _ in range(m)]\n    times = sorted(diff)\n    ordered_queries = sorted((time, idx) for idx, time in enumerate(queries))\n\n    ans = [0] * m\n    current = 0\n    ptr = 0\n    for time, idx in ordered_queries:\n        while ptr < len(times) and times[ptr] <= time:\n            current += diff[times[ptr]]\n            ptr += 1\n        ans[idx] = current\n\n    sys.stdout.write('\\n'.join(map(str, ans)))\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
