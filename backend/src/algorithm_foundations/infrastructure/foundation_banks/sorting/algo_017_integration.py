from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('integration')

UNIT_BANK = unit_bank(
    unit_id='algo-017-integration',
    title='計数ソート（カウンティングソート） の総合演習',
    unit_kind='integration',
    target_skill='計数ソート（カウンティングソート） の総合演習',
    concept_overview='計数ソートでは、累積個数を使うと「同じ key を入力順のまま保つ安定ソート」までできます。ここでは key 付きレコードを安定に並べ替えます。',
    problem_bank=[
        problem(
            problem_id='algo-017-integration-p1',
            title='計数ソート（カウンティングソート） の総合演習 / key で安定にカードを並べる',
            problem_statement='0 以上 K 以下の key を持つ N 枚のカードが与えられる。i 枚目のカードは整数 key_i と名前 name_i を持つ。key の昇順で安定に並べ替えたときの名前列を出力せよ。',
            input_format='1 行目に N K。\n続く N 行に key_i name_i。',
            output_format='並べ替え後の名前を 1 行ずつ出力する。',
            constraints='1 <= N <= 2 * 10^5\n0 <= K <= 10^6\n0 <= key_i <= K\nname_i は英小文字からなる長さ 1 以上 20 以下の文字列',
            examples=[{'input': '5 3\n2 blue\n1 apple\n2 green\n0 zero\n1 berry', 'output': 'zero\napple\nberry\nblue\ngreen'}],
            canonical_reference_solution="def solve() -> None:\n    n, k = map(int, input().split())\n    cards = []\n    cnt = [0] * (k + 1)\n    for _ in range(n):\n        key, name = input().split()\n        key = int(key)\n        cards.append((key, name))\n        cnt[key] += 1\n    for i in range(1, k + 1):\n        cnt[i] += cnt[i - 1]\n    out = [''] * n\n    for key, name in reversed(cards):\n        cnt[key] -= 1\n        out[cnt[key]] = name\n    print('\\n'.join(out))\n\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
