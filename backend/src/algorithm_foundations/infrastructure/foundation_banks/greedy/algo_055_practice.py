from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('foundation')

UNIT_BANK = unit_bank(
    unit_id='algo-055-practice',
    title='交換による証明（exchange argument） を素直に実装する',
    unit_kind='foundation',
    target_skill='交換による証明（exchange argument） を素直に実装する',
    concept_overview='処理時間の昇順が最適だと分かったら、その順序を土台に「どの仕事を外すと全体がどれだけ軽くなるか」も考えられます。ここでは同じ昇順配置のまま、各仕事の寄与を数えて最善の 1 件を選ぶ練習へ広げます。',
    problem_bank=[
        problem(
            problem_id='algo-055-practice-p1',
            title='交換による証明（exchange argument） を素直に実装する / 1 件だけ取りやめるときの最小完了時刻和を求める',
            problem_statement='N 個の仕事があり、i 番目の処理時間は T_i である。1 台の機械で 1 つずつ順番に処理するが、ちょうど 1 件だけ仕事を取りやめてよい。残りの仕事の完了時刻の総和を最小にせよ。',
            input_format='1 行目に N。\n2 行目に T1..TN。',
            output_format='取りやめ方も含めた最小の完了時刻総和を出力する。',
            constraints='1 <= N <= 2 * 10^5\n1 <= T_i <= 10^9',
            examples=[{'input': '3\n5 1 2', 'output': '4'}],
            canonical_reference_solution="def solve() -> None:\n    input()\n    times = sorted(map(int, input().split()))\n    total = 0\n    n = len(times)\n    prefix = []\n    current = 0\n    for i, time in enumerate(times):\n        current += time\n        prefix.append(current)\n        total += current\n    best = total\n    for i, time in enumerate(times):\n        reduction = prefix[i] + time * (n - i - 1)\n        best = min(best, total - reduction)\n    print(best)\n\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
