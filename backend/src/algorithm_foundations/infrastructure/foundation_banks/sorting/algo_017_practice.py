from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('foundation')

UNIT_BANK = unit_bank(
    unit_id='algo-017-practice',
    title='計数ソート（カウンティングソート） を素直に実装する',
    unit_kind='foundation',
    target_skill='計数ソート（カウンティングソート） を素直に実装する',
    concept_overview='計数ソートでは、頻度配列を作ったあと、小さい値から順に書き戻して整列結果を復元します。数える段階と復元する段階をつないで完成形を出します。',
    problem_bank=[
        problem(
            problem_id='algo-017-practice-p1',
            title='計数ソート（カウンティングソート） を素直に実装する / 値域 K を使って昇順に復元する',
            problem_statement='0 以上 K 以下の整数からなる長さ N の列 A が与えられる。計数ソートで A を昇順に並べ替えて出力せよ。',
            input_format='1 行目に N K。\n2 行目に A1..AN。',
            output_format='昇順の列を空白区切りで出力する。',
            constraints='1 <= N <= 2 * 10^5\n0 <= K <= 10^6\n0 <= Ai <= K',
            examples=[{'input': '6 7\n4 1 7 2 4 0', 'output': '0 1 2 4 4 7'}],
            canonical_reference_solution="def solve() -> None:\n    n, k = map(int, input().split())\n    a = list(map(int, input().split()))\n    cnt = [0] * (k + 1)\n    for value in a:\n        cnt[value] += 1\n    out = []\n    for value, freq in enumerate(cnt):\n        out.extend([value] * freq)\n    print(*out)\n\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
