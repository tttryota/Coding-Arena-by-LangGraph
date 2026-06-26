from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('integration')

UNIT_BANK = unit_bank(
    unit_id='algo-054-integration',
    title='分数ナップサック問題 の総合演習',
    unit_kind='integration',
    target_skill='分数ナップサック問題 の総合演習',
    concept_overview='価値/重さの大きい順に取る最大化と対になる形で、コスト/重さの小さい順に取れば必要量を最安で満たせます。密度順の貪欲を双対側の目的関数へ移した総合演習です。',
    problem_bank=[
        problem(
            problem_id='algo-054-integration-p1',
            title='分数ナップサック問題 の総合演習 / 必要重量 W を満たす最小コストを求める',
            problem_statement='N 種類の素材があり、i 番目は 1 単位あたりのコストが Ci、最大で Wi だけ使える。合計重量が W 以上になるように素材を選ぶ。素材は分割してよいとき、必要重量を満たす最小コストを求めよ。不可能なら -1 を出力せよ。',
            input_format='1 行目に N W。\n続く N 行に Ci Wi。',
            output_format='最小コストを出力する。不可能なら -1 を出力する。絶対誤差または相対誤差 10^-6 まで許す。',
            constraints='1 <= N <= 2 * 10^5\n1 <= W <= 10^18\n1 <= Ci, Wi <= 10^9',
            examples=[{'input': '3 6\n5 2\n3 3\n4 4', 'output': '21.0'}],
            canonical_reference_solution="def solve() -> None:\n    import sys\n    input = sys.stdin.readline\n    n, need = map(int, input().split())\n    items = [tuple(map(int, input().split())) for _ in range(n)]\n    items.sort(key=lambda item: item[0])\n    total = 0.0\n    for cost, weight in items:\n        if need == 0:\n            break\n        take = min(need, weight)\n        total += cost * take\n        need -= take\n    print(total if need == 0 else -1)\n\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
