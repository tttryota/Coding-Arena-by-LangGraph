from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('foundation')

UNIT_BANK = unit_bank(
    unit_id='algo-048-basic',
    title='ゲーム理論DP（Grundy数） の基本',
    unit_kind='foundation',
    target_skill='ゲーム理論DP（Grundy数） の基本',
    concept_overview='ゲーム理論DPの最初の形は、「次の状態に負けがあれば今は勝ち」と判定する勝敗 DP です。まずは 1 山の取り石ゲームで後ろ向きに勝ち負けを埋めます。',
    problem_bank=[
        problem(
            problem_id='algo-048-basic-p1',
            title='ゲーム理論DP（Grundy数） の基本 / 先手後手が最善を尽くすとして、先手が勝つなら First、負けるなら Second を求める',
            problem_statement='石が N 個あり、1 回で 1 個または 3 個取れるゲームを考える。 先手後手が最善を尽くすとして、先手が勝つなら First、負けるなら Second を出力せよ。',
            input_format='1 行目に N。',
            output_format='First / Second を出力する。',
            constraints='1 <= N <= 2 * 10^5',
            examples=[{'input': '2', 'output': 'Second'}],
            canonical_reference_solution="def solve() -> None:\n    n = int(input())\n    win = [False] * (max(4, n + 1))\n    for stones in range(1, n + 1):\n        for move in (1, 3):\n            if stones >= move and not win[stones - move]:\n                win[stones] = True\n                break\n    print('First' if win[n] else 'Second')\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
