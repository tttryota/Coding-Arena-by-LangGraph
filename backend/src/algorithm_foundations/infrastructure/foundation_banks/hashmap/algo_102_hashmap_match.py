from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('integration')

UNIT_BANK = unit_bank(
    unit_id='algo-102-hashmap-match',
    title='2配列の照合をハッシュで処理',
    unit_kind='integration',
    target_skill='2配列の照合をハッシュで処理',
    concept_overview='片方の情報をハッシュにまとめ、もう片方を見ながら一致や不足を判定する考え方です。照合を全組合せではなく表引きで処理する形を学びます。',
    problem_bank=[
        problem(
            problem_id='algo-102-hashmap-match-p1',
            title='2配列の照合をハッシュで処理 / 並べ替えたら一致するか判定する',
            problem_statement='長さ N の整数列 A, B が与えられる。並べ替えると一致するなら Yes、そうでなければ No を出力せよ。',
            input_format='1 行目に N。\n2 行目に A1..AN。\n3 行目に B1..BN。',
            output_format='Yes / No を出力する。',
            constraints='1 <= N <= 2 * 10^5\n0 <= Ai, Bi <= 10^9',
            examples=[
                {
                    'input': '4\n1 2 2 5\n2 5 1 2',
                    'output': 'Yes',
                },
            ],
            canonical_reference_solution="from collections import Counter\n\ndef solve() -> None:\n    input()\n    a = Counter(map(int, input().split()))\n    b = Counter(map(int, input().split()))\n    print('Yes' if a == b else 'No')\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
        problem(
            problem_id='algo-102-hashmap-match-p2',
            title='2配列の照合をハッシュで処理 / B を A の中から作れるか判定する',
            problem_statement='長さ N の整数列 A と長さ M の整数列 B が与えられる。A の各要素は 1 回ずつしか使えないものとして、B の全要素を A から取り出せるなら Yes、そうでなければ No を出力せよ。',
            input_format='1 行目に N M。\n2 行目に A1..AN。\n3 行目に B1..BM。',
            output_format='Yes / No を出力する。',
            constraints='1 <= M <= N <= 2 * 10^5\n0 <= Ai, Bi <= 10^9',
            examples=[
                {
                    'input': '6 4\n1 2 2 5 7 7\n2 7 1 7',
                    'output': 'Yes',
                },
            ],
            canonical_reference_solution="from collections import Counter\n\ndef solve() -> None:\n    input()\n    a = Counter(map(int, input().split()))\n    for value, count in Counter(map(int, input().split())).items():\n        if a[value] < count:\n            print('No')\n            return\n    print('Yes')\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
        problem(
            problem_id='algo-102-hashmap-match-p3',
            title='2配列の照合をハッシュで処理 / 共通に作れる組数を数える',
            problem_statement='長さ N の整数列 A と長さ M の整数列 B が与えられる。同じ値どうしを 1 回ずつ組にするとき、作れる組の最大数を求めよ。',
            input_format='1 行目に N M。\n2 行目に A1..AN。\n3 行目に B1..BM。',
            output_format='作れる組数を出力する。',
            constraints='1 <= N, M <= 2 * 10^5\n0 <= Ai, Bi <= 10^9',
            examples=[
                {
                    'input': '6 5\n1 2 2 5 7 7\n2 7 1 7 7',
                    'output': '4',
                },
            ],
            canonical_reference_solution="from collections import Counter\n\ndef solve() -> None:\n    input()\n    a = Counter(map(int, input().split()))\n    b = Counter(map(int, input().split()))\n    ans = 0\n    for value, count in a.items():\n        ans += min(count, b.get(value, 0))\n    print(ans)\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
