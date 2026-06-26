from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('integration')

UNIT_BANK = unit_bank(
    unit_id='algo-060-integration',
    title='イベントソートによる走査 の総合演習',
    unit_kind='integration',
    target_skill='イベントソートによる走査 の総合演習',
    concept_overview='イベントソートで時刻ごとの人数変化が分かれば、ある時点の個数だけでなく、その状態がどれだけの長さ続いたかも数えられます。隣り合うイベント時刻の差を使って、しきい値以上の総時間へ広げます。',
    problem_bank=[
        problem(
            problem_id='algo-060-integration-p1',
            title='イベントソートによる走査 の総合演習 / K 個以上のイベントが同時に存在する総時間を求める',
            problem_statement='N 個のイベントの開始時刻 L_i と終了時刻 R_i、および整数 K が与えられる。各イベントは区間 [L_i, R_i) の間だけ存在する。少なくとも K 個のイベントが同時に存在する時間の総和を求めよ。',
            input_format='1 行目に N K。\n続く N 行に L_i R_i。',
            output_format='条件を満たす総時間を出力する。',
            constraints='1 <= N <= 2 * 10^5\n1 <= K <= N\n0 <= L_i < R_i <= 10^9',
            examples=[{'input': '4 2\n1 4\n2 5\n5 7\n6 8', 'output': '3'}],
            canonical_reference_solution="def solve() -> None:\n    n, k = map(int, input().split())\n    diff = {}\n    for _ in range(n):\n        l, r = map(int, input().split())\n        diff[l] = diff.get(l, 0) + 1\n        diff[r] = diff.get(r, 0) - 1\n    times = sorted(diff)\n    current = 0\n    total = 0\n    for i, time in enumerate(times):\n        current += diff[time]\n        if i + 1 == len(times):\n            continue\n        next_time = times[i + 1]\n        if current >= k:\n            total += next_time - time\n    print(total)\n\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
