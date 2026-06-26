from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('foundation')

UNIT_BANK = unit_bank(
    unit_id='algo-019-practice',
    title='座標圧縮 を素直に実装する',
    unit_kind='foundation',
    target_skill='座標圧縮 を素直に実装する',
    concept_overview='座標圧縮では、1 本の列だけでなく複数の列から値を集めて同じ軸で圧縮することも重要です。ここでは区間の左右端をまとめて圧縮します。',
    problem_bank=[
        problem(
            problem_id='algo-019-practice-p1',
            title='座標圧縮 を素直に実装する / 区間の左右端を同じ軸で圧縮する',
            problem_statement='N 個の区間 [L_i, R_i] が与えられる。すべての端点を 1 つの軸として座標圧縮し、各区間の圧縮後の端点 L_i\', R_i\' を入力順に出力せよ。',
            input_format='1 行目に N。\n続く N 行に L_i R_i。',
            output_format='各区間について、圧縮後の L_i\' と R_i\' を 1 行ずつ出力する。',
            constraints='1 <= N <= 2 * 10^5\n-10^18 <= L_i <= R_i <= 10^18',
            examples=[{'input': '3\n100 200\n50 100\n200 300', 'output': '1 2\n0 1\n2 3'}],
            canonical_reference_solution="def solve() -> None:\n    import sys\n    input = sys.stdin.readline\n    n = int(input())\n    segments = [tuple(map(int, input().split())) for _ in range(n)]\n    values = []\n    for left, right in segments:\n        values.append(left)\n        values.append(right)\n    comp = {value: idx for idx, value in enumerate(sorted(set(values)))}\n    out = [f\"{comp[left]} {comp[right]}\" for left, right in segments]\n    sys.stdout.write('\\n'.join(out))\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
