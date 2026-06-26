from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('foundation')

UNIT_BANK = unit_bank(
    unit_id='algo-071-basic',
    title='Z-algorithm の基本',
    unit_kind='foundation',
    target_skill='Z-algorithm の基本',
    concept_overview='文字列検索アルゴリズムは、一致しなかった場所の情報を使い回し、比較を最初からやり直さない考え方です。文字列の自己一致を利用する基本を学びます。',
    problem_bank=[
        problem(
            problem_id='algo-071-basic-p1',
            title='Z-algorithm の基本 / 1 ケースをそのまま解く',
            problem_statement='文字列 S と T が与えられる。Z-algorithm を用いて、T が S に何回現れるかを求めよ（重なりも数える）。',
            input_format='1 行目に S。\n2 行目に T。',
            output_format='出現回数を出力する。',
            constraints='1 <= |S| <= 2 * 10^5\n1 <= |T| <= |S|',
            examples=[
                {
                    'input': 'aaaa\naa',
                    'output': '3',
                },
            ],
            canonical_reference_solution="def z_algorithm(text: str) -> list[int]:\n    z = [0] * len(text)\n    left = right = 0\n    for i in range(1, len(text)):\n        if i <= right:\n            z[i] = min(right - i + 1, z[i - left])\n        while i + z[i] < len(text) and text[z[i]] == text[i + z[i]]:\n            z[i] += 1\n        if i + z[i] - 1 > right:\n            left = i\n            right = i + z[i] - 1\n    z[0] = len(text)\n    return z\n\ndef solve() -> None:\n    s = input().strip()\n    t = input().strip()\n    merged = t + '$' + s\n    z = z_algorithm(merged)\n    ans = 0\n    m = len(t)\n    for value in z[m + 1:]:\n        if value >= m:\n            ans += 1\n    print(ans)\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
        problem(
            problem_id='algo-071-basic-p2',
            title='Z-algorithm の基本 / 2 ケースを連続して解く',
            problem_statement='2 ケース分の入力が続けて与えられる。それぞれについて、文字列 S と T が与えられる。Z-algorithm を用いて、T が S に何回現れるかを求めよ（重なりも数える）。',
            input_format='1 行目に 2。\n続く 2 ケースについて:\n1 行目に S。\n2 行目に T。',
            output_format='各ケースの答えを順に出力する。',
            constraints='1 <= |S| <= 2 * 10^5\n1 <= |T| <= |S|\n2 ケースの合計でも同じ方針で処理すること。',
            examples=[
                {
                    'input': '2\naaaa\naa\naaaa\naa',
                    'output': '3\n3',
                },
            ],
            canonical_reference_solution="import io\nimport sys\nfrom contextlib import redirect_stdout\n\ndef z_algorithm(text: str) -> list[int]:\n    z = [0] * len(text)\n    left = right = 0\n    for i in range(1, len(text)):\n        if i <= right:\n            z[i] = min(right - i + 1, z[i - left])\n        while i + z[i] < len(text) and text[z[i]] == text[i + z[i]]:\n            z[i] += 1\n        if i + z[i] - 1 > right:\n            left = i\n            right = i + z[i] - 1\n    z[0] = len(text)\n    return z\n\ndef solve_one() -> None:\n    s = input().strip()\n    t = input().strip()\n    merged = t + '$' + s\n    z = z_algorithm(merged)\n    ans = 0\n    m = len(t)\n    for value in z[m + 1:]:\n        if value >= m:\n            ans += 1\n    print(ans)\n\ndef solve() -> None:\n    t = 2\n    outputs = []\n    for _ in range(t):\n        buf = io.StringIO()\n        with redirect_stdout(buf):\n            solve_one()\n        outputs.append(buf.getvalue().rstrip('\\n'))\n    sys.stdout.write('\\n'.join(outputs))\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
        problem(
            problem_id='algo-071-basic-p3',
            title='Z-algorithm の基本 / 3 ケースを連続して解く',
            problem_statement='3 ケース分の入力が続けて与えられる。それぞれについて、文字列 S と T が与えられる。Z-algorithm を用いて、T が S に何回現れるかを求めよ（重なりも数える）。',
            input_format='1 行目に 3。\n続く 3 ケースについて:\n1 行目に S。\n2 行目に T。',
            output_format='各ケースの答えを順に出力する。',
            constraints='1 <= |S| <= 2 * 10^5\n1 <= |T| <= |S|\n3 ケースの合計でも同じ方針で処理すること。',
            examples=[
                {
                    'input': '3\naaaa\naa\naaaa\naa\naaaa\naa',
                    'output': '3\n3\n3',
                },
            ],
            canonical_reference_solution="import io\nimport sys\nfrom contextlib import redirect_stdout\n\ndef z_algorithm(text: str) -> list[int]:\n    z = [0] * len(text)\n    left = right = 0\n    for i in range(1, len(text)):\n        if i <= right:\n            z[i] = min(right - i + 1, z[i - left])\n        while i + z[i] < len(text) and text[z[i]] == text[i + z[i]]:\n            z[i] += 1\n        if i + z[i] - 1 > right:\n            left = i\n            right = i + z[i] - 1\n    z[0] = len(text)\n    return z\n\ndef solve_one() -> None:\n    s = input().strip()\n    t = input().strip()\n    merged = t + '$' + s\n    z = z_algorithm(merged)\n    ans = 0\n    m = len(t)\n    for value in z[m + 1:]:\n        if value >= m:\n            ans += 1\n    print(ans)\n\ndef solve() -> None:\n    t = 3\n    outputs = []\n    for _ in range(t):\n        buf = io.StringIO()\n        with redirect_stdout(buf):\n            solve_one()\n        outputs.append(buf.getvalue().rstrip('\\n'))\n    sys.stdout.write('\\n'.join(outputs))\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
