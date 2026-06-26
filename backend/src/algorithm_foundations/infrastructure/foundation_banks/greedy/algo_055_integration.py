from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('integration')

UNIT_BANK = unit_bank(
    unit_id='algo-055-integration',
    title='交換による証明（exchange argument） の総合演習',
    unit_kind='integration',
    target_skill='交換による証明（exchange argument） の総合演習',
    concept_overview='交換による証明は、各仕事に重みが付いた場合にも使えます。2 つの仕事の順序を入れ替えたときの差を比べると、重み付き完了時刻和では `T_i / W_i` の小さい順が有利だと分かります。',
    problem_bank=[
        problem(
            problem_id='algo-055-integration-p1',
            title='交換による証明（exchange argument） の総合演習 / 重み付き完了時刻和を最小にせよ',
            problem_statement='N 個の仕事があり、i 番目の処理時間は T_i、重みは W_i である。1 台の機械で 1 つずつ順番に処理するとき、`Σ W_i * C_i` を最小にせよ。ここで C_i は仕事 i の完了時刻である。',
            input_format='1 行目に N。\n続く N 行に T_i W_i。',
            output_format='重み付き完了時刻和の最小値を出力する。',
            constraints='1 <= N <= 2 * 10^5\n1 <= T_i, W_i <= 10^9',
            examples=[{'input': '3\n3 1\n1 3\n2 2', 'output': '15'}],
            canonical_reference_solution="from functools import cmp_to_key\n\n\ndef cmp(a: tuple[int, int], b: tuple[int, int]) -> int:\n    ta, wa = a\n    tb, wb = b\n    left = ta * wb\n    right = tb * wa\n    if left < right:\n        return -1\n    if left > right:\n        return 1\n    return 0\n\n\ndef solve() -> None:\n    n = int(input())\n    jobs = [tuple(map(int, input().split())) for _ in range(n)]\n    jobs.sort(key=cmp_to_key(cmp))\n    current = 0\n    total = 0\n    for time, weight in jobs:\n        current += time\n        total += weight * current\n    print(total)\n\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
