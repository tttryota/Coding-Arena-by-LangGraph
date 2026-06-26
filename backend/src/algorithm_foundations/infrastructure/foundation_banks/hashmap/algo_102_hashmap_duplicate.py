from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('foundation')

UNIT_BANK = unit_bank(
    unit_id='algo-102-hashmap-duplicate',
    title='重複検出をハッシュで行う',
    unit_kind='foundation',
    target_skill='重複検出をハッシュで行う',
    concept_overview='見た値をハッシュ集合に入れながら進み、すでに入っているかで重複を判定する考え方です。1 回の走査で重複を見つける流れを押さえます。',
    problem_bank=[
        problem(
            problem_id='algo-102-hashmap-duplicate-p1',
            title='重複検出をハッシュで行う / 同じ値が 2 回以上出るか判定する',
            problem_statement='長さ N の整数列 A が与えられる。同じ値が 2 回以上現れるなら Yes、そうでなければ No を出力せよ。',
            input_format='1 行目に N。\n2 行目に A1..AN。',
            output_format='Yes / No を出力する。',
            constraints='1 <= N <= 2 * 10^5\n0 <= Ai <= 10^9',
            examples=[
                {
                    'input': '5\n1 4 2 4 7',
                    'output': 'Yes',
                },
            ],
            canonical_reference_solution="def solve() -> None:\n    input()\n    a = list(map(int, input().split()))\n    seen = set()\n    for value in a:\n        if value in seen:\n            print('Yes')\n            return\n        seen.add(value)\n    print('No')\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
        problem(
            problem_id='algo-102-hashmap-duplicate-p2',
            title='重複検出をハッシュで行う / 最初に再登場した値を出力する',
            problem_statement='長さ N の整数列 A が与えられる。左から見て、はじめて「2 回目の出現」になった値を出力せよ。そのような値がなければ -1 を出力する。',
            input_format='1 行目に N。\n2 行目に A1..AN。',
            output_format='条件を満たす値、なければ -1 を出力する。',
            constraints='1 <= N <= 2 * 10^5\n0 <= Ai <= 10^9',
            examples=[
                {
                    'input': '7\n8 3 5 3 8 1 5',
                    'output': '3',
                },
            ],
            canonical_reference_solution="def solve() -> None:\n    input()\n    seen = set()\n    for value in map(int, input().split()):\n        if value in seen:\n            print(value)\n            return\n        seen.add(value)\n    print(-1)\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
        problem(
            problem_id='algo-102-hashmap-duplicate-p3',
            title='重複検出をハッシュで行う / 最初に重複した位置を出力する',
            problem_statement='長さ N の整数列 A が与えられる。左から見て、はじめて既出の値が現れた 1-indexed の位置を出力せよ。重複がなければ -1 を出力する。',
            input_format='1 行目に N。\n2 行目に A1..AN。',
            output_format='条件を満たす位置、なければ -1 を出力する。',
            constraints='1 <= N <= 2 * 10^5\n0 <= Ai <= 10^9',
            examples=[
                {
                    'input': '7\n8 3 5 3 8 1 5',
                    'output': '4',
                },
            ],
            canonical_reference_solution="def solve() -> None:\n    input()\n    seen = set()\n    for idx, value in enumerate(map(int, input().split()), start=1):\n        if value in seen:\n            print(idx)\n            return\n        seen.add(value)\n    print(-1)\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
        problem(
            problem_id='algo-102-hashmap-duplicate-p4',
            title='重複検出をハッシュで行う / 2 回以上現れる値の種類数を数える',
            problem_statement='長さ N の整数列 A が与えられる。2 回以上現れる値の種類数を求めよ。',
            input_format='1 行目に N。\n2 行目に A1..AN。',
            output_format='条件を満たす値の種類数を出力する。',
            constraints='1 <= N <= 2 * 10^5\n0 <= Ai <= 10^9',
            examples=[
                {
                    'input': '8\n1 4 2 4 7 2 1 9',
                    'output': '3',
                },
            ],
            canonical_reference_solution="from collections import Counter\n\ndef solve() -> None:\n    input()\n    counter = Counter(map(int, input().split()))\n    print(sum(1 for count in counter.values() if count >= 2))\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
        problem(
            problem_id='algo-102-hashmap-duplicate-p5',
            title='重複検出をハッシュで行う / 重複している値だけを小さい順に並べる',
            problem_statement='長さ N の整数列 A が与えられる。2 回以上現れる値だけを小さい順に並べて出力せよ。存在しなければ `None` を出力する。',
            input_format='1 行目に N。\n2 行目に A1..AN。',
            output_format='条件を満たす値を空白区切りで、存在しなければ None を出力する。',
            constraints='1 <= N <= 2 * 10^5\n0 <= Ai <= 10^9',
            examples=[
                {
                    'input': '8\n1 4 2 4 7 2 1 9',
                    'output': '1 2 4',
                },
            ],
            canonical_reference_solution="from collections import Counter\n\ndef solve() -> None:\n    input()\n    counter = Counter(map(int, input().split()))\n    ans = [str(value) for value, count in sorted(counter.items()) if count >= 2]\n    print(' '.join(ans) if ans else 'None')\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
        problem(
            problem_id='algo-102-hashmap-duplicate-p6',
            title='重複検出をハッシュで行う / 重複を含む接頭辞の個数を数える',
            problem_statement='長さ N の整数列 A が与えられる。接頭辞 `A1..Ai` の中に重複があるような i の個数を求めよ。',
            input_format='1 行目に N。\n2 行目に A1..AN。',
            output_format='条件を満たす i の個数を出力する。',
            constraints='1 <= N <= 2 * 10^5\n0 <= Ai <= 10^9',
            examples=[
                {
                    'input': '6\n1 2 3 2 5 1',
                    'output': '3',
                },
            ],
            canonical_reference_solution="def solve() -> None:\n    input()\n    seen = set()\n    has_duplicate = False\n    ans = 0\n    for value in map(int, input().split()):\n        if value in seen:\n            has_duplicate = True\n        seen.add(value)\n        if has_duplicate:\n            ans += 1\n    print(ans)\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
