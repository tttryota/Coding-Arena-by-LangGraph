from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('foundation')

UNIT_BANK = unit_bank(
    unit_id='algo-068-practice',
    title='マージソートで転倒数 を素直に実装する',
    unit_kind='foundation',
    target_skill='マージソートで転倒数 を素直に実装する',
    concept_overview='転倒数は、順序が逆になっている組の個数を数える知識です。『何個後ろに小さいものがあるか』を効率よく数える形を学びます。',
    problem_bank=[
        problem(
            problem_id='algo-068-practice-p1',
            title='マージソートで転倒数 を素直に実装する / 1 ケースをそのまま解く',
            problem_statement='長さ N の整数列 A が与えられる。転倒数を求めよ。',
            input_format='1 行目に N。\n2 行目に A1..AN。',
            output_format='転倒数を出力する。',
            constraints='1 <= N <= 2 * 10^5',
            examples=[
                {
                    'input': '4\n3 1 4 2',
                    'output': '3',
                },
            ],
            canonical_reference_solution="def merge_count(arr: list[int]) -> tuple[list[int], int]:\n    if len(arr) <= 1:\n        return arr, 0\n    mid = len(arr) // 2\n    left, lc = merge_count(arr[:mid])\n    right, rc = merge_count(arr[mid:])\n    merged = []\n    i = j = 0\n    inv = lc + rc\n    while i < len(left) and j < len(right):\n        if left[i] <= right[j]:\n            merged.append(left[i]); i += 1\n        else:\n            merged.append(right[j]); j += 1\n            inv += len(left) - i\n    merged.extend(left[i:])\n    merged.extend(right[j:])\n    return merged, inv\n\ndef solve() -> None:\n    input()\n    a = list(map(int, input().split()))\n    print(merge_count(a)[1])\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
        problem(
            problem_id='algo-068-practice-p2',
            title='マージソートで転倒数 を素直に実装する / 2 ケースを連続して解く',
            problem_statement='2 ケース分の入力が続けて与えられる。それぞれについて、長さ N の整数列 A が与えられる。転倒数を求めよ。',
            input_format='1 行目に 2。\n続く 2 ケースについて:\n1 行目に N。\n2 行目に A1..AN。',
            output_format='各ケースの答えを順に出力する。',
            constraints='1 <= N <= 2 * 10^5\n2 ケースの合計でも同じ方針で処理すること。',
            examples=[
                {
                    'input': '2\n4\n3 1 4 2\n4\n3 1 4 2',
                    'output': '3\n3',
                },
            ],
            canonical_reference_solution="import io\nimport sys\nfrom contextlib import redirect_stdout\n\ndef merge_count(arr: list[int]) -> tuple[list[int], int]:\n    if len(arr) <= 1:\n        return arr, 0\n    mid = len(arr) // 2\n    left, lc = merge_count(arr[:mid])\n    right, rc = merge_count(arr[mid:])\n    merged = []\n    i = j = 0\n    inv = lc + rc\n    while i < len(left) and j < len(right):\n        if left[i] <= right[j]:\n            merged.append(left[i]); i += 1\n        else:\n            merged.append(right[j]); j += 1\n            inv += len(left) - i\n    merged.extend(left[i:])\n    merged.extend(right[j:])\n    return merged, inv\n\ndef solve_one() -> None:\n    input()\n    a = list(map(int, input().split()))\n    print(merge_count(a)[1])\n\ndef solve() -> None:\n    t = 2\n    outputs = []\n    for _ in range(t):\n        buf = io.StringIO()\n        with redirect_stdout(buf):\n            solve_one()\n        outputs.append(buf.getvalue().rstrip('\\n'))\n    sys.stdout.write('\\n'.join(outputs))\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
        problem(
            problem_id='algo-068-practice-p3',
            title='マージソートで転倒数 を素直に実装する / 3 ケースを連続して解く',
            problem_statement='3 ケース分の入力が続けて与えられる。それぞれについて、長さ N の整数列 A が与えられる。転倒数を求めよ。',
            input_format='1 行目に 3。\n続く 3 ケースについて:\n1 行目に N。\n2 行目に A1..AN。',
            output_format='各ケースの答えを順に出力する。',
            constraints='1 <= N <= 2 * 10^5\n3 ケースの合計でも同じ方針で処理すること。',
            examples=[
                {
                    'input': '3\n4\n3 1 4 2\n4\n3 1 4 2\n4\n3 1 4 2',
                    'output': '3\n3\n3',
                },
            ],
            canonical_reference_solution="import io\nimport sys\nfrom contextlib import redirect_stdout\n\ndef merge_count(arr: list[int]) -> tuple[list[int], int]:\n    if len(arr) <= 1:\n        return arr, 0\n    mid = len(arr) // 2\n    left, lc = merge_count(arr[:mid])\n    right, rc = merge_count(arr[mid:])\n    merged = []\n    i = j = 0\n    inv = lc + rc\n    while i < len(left) and j < len(right):\n        if left[i] <= right[j]:\n            merged.append(left[i]); i += 1\n        else:\n            merged.append(right[j]); j += 1\n            inv += len(left) - i\n    merged.extend(left[i:])\n    merged.extend(right[j:])\n    return merged, inv\n\ndef solve_one() -> None:\n    input()\n    a = list(map(int, input().split()))\n    print(merge_count(a)[1])\n\ndef solve() -> None:\n    t = 3\n    outputs = []\n    for _ in range(t):\n        buf = io.StringIO()\n        with redirect_stdout(buf):\n            solve_one()\n        outputs.append(buf.getvalue().rstrip('\\n'))\n    sys.stdout.write('\\n'.join(outputs))\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
