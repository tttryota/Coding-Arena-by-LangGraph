from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('integration')

UNIT_BANK = unit_bank(
    unit_id='algo-018-integration',
    title='基数ソート の総合演習',
    unit_kind='integration',
    target_skill='基数ソート の総合演習',
    concept_overview='基数ソートは、固定長の数字列を辞書順に並べるときにも、そのまま使えます。右端から左へ安定に並べて、文字列全体の順序を作ります。',
    problem_bank=[
        problem(
            problem_id='algo-018-integration-p1',
            title='基数ソート の総合演習 / 固定長 ID を辞書順に並べる',
            problem_statement='長さ L の数字列からなる ID が N 個与えられる。すべての ID は長さがちょうど L で、0 埋めも含まれる。右端の桁から左端の桁へ向かって基数ソートを行い、ID を辞書順に並べて出力せよ。',
            input_format='1 行目に N L。\n続く N 行に ID_i。',
            output_format='並べ替え後の ID を 1 行ずつ出力する。',
            constraints='1 <= N <= 2 * 10^5\n1 <= L <= 12\n各 ID_i は数字のみからなる長さ L の文字列',
            examples=[{'input': '5 3\n310\n002\n120\n305\n099', 'output': '002\n099\n120\n305\n310'}],
            canonical_reference_solution="def solve() -> None:\n    n, l = map(int, input().split())\n    ids = [input().strip() for _ in range(n)]\n    for pos in range(l - 1, -1, -1):\n        buckets = [[] for _ in range(10)]\n        for value in ids:\n            buckets[ord(value[pos]) - ord('0')].append(value)\n        ids = [value for bucket in buckets for value in bucket]\n    print('\\n'.join(ids))\n\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
