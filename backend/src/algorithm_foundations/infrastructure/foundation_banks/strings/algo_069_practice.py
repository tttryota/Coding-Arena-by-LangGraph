from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('foundation')

UNIT_BANK = unit_bank(
    unit_id='algo-069-practice',
    title='文字列のハッシュ（ローリングハッシュ） を素直に実装する',
    unit_kind='foundation',
    target_skill='文字列のハッシュ（ローリングハッシュ） を素直に実装する',
    concept_overview='ハッシュは、値をキーにして必要な情報へすぐたどる考え方です。『探す』を『表から引く』に置き換えて、判定や数え上げを高速化します。',
    problem_bank=[
        problem(
            problem_id='algo-069-practice-p1',
            title='文字列のハッシュ（ローリングハッシュ） を素直に実装する / 1 ケースをそのまま解く',
            problem_statement='文字列 S と T が与えられる。ローリングハッシュを用いて、T が S に何回現れるかを求めよ。',
            input_format='1 行目に S。\n2 行目に T。',
            output_format='出現回数を出力する。',
            constraints='1 <= |S| <= 2 * 10^5\n1 <= |T| <= |S|',
            examples=[
                {
                    'input': 'aaaa\naa',
                    'output': '3',
                },
            ],
            canonical_reference_solution="def solve() -> None:\n    s = input().strip()\n    t = input().strip()\n    base = 911382323\n    mod = 972663749\n    n = len(s)\n    m = len(t)\n    power = [1] * (n + 1)\n    prefix = [0] * (n + 1)\n    for i, ch in enumerate(s, start=1):\n        power[i] = power[i - 1] * base % mod\n        prefix[i] = (prefix[i - 1] * base + ord(ch)) % mod\n    target = 0\n    for ch in t:\n        target = (target * base + ord(ch)) % mod\n    ans = 0\n    for left in range(n - m + 1):\n        right = left + m\n        value = (prefix[right] - prefix[left] * power[m]) % mod\n        if value == target and s[left:right] == t:\n            ans += 1\n    print(ans)\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
        problem(
            problem_id='algo-069-practice-p2',
            title='文字列のハッシュ（ローリングハッシュ） を素直に実装する / 2 ケースを連続して解く',
            problem_statement='2 ケース分の入力が続けて与えられる。それぞれについて、文字列 S と T が与えられる。ローリングハッシュを用いて、T が S に何回現れるかを求めよ。',
            input_format='1 行目に 2。\n続く 2 ケースについて:\n1 行目に S。\n2 行目に T。',
            output_format='各ケースの答えを順に出力する。',
            constraints='1 <= |S| <= 2 * 10^5\n1 <= |T| <= |S|\n2 ケースの合計でも同じ方針で処理すること。',
            examples=[
                {
                    'input': '2\naaaa\naa\naaaa\naa',
                    'output': '3\n3',
                },
            ],
            canonical_reference_solution="import io\nimport sys\nfrom contextlib import redirect_stdout\n\ndef solve_one() -> None:\n    s = input().strip()\n    t = input().strip()\n    base = 911382323\n    mod = 972663749\n    n = len(s)\n    m = len(t)\n    power = [1] * (n + 1)\n    prefix = [0] * (n + 1)\n    for i, ch in enumerate(s, start=1):\n        power[i] = power[i - 1] * base % mod\n        prefix[i] = (prefix[i - 1] * base + ord(ch)) % mod\n    target = 0\n    for ch in t:\n        target = (target * base + ord(ch)) % mod\n    ans = 0\n    for left in range(n - m + 1):\n        right = left + m\n        value = (prefix[right] - prefix[left] * power[m]) % mod\n        if value == target and s[left:right] == t:\n            ans += 1\n    print(ans)\n\ndef solve() -> None:\n    t = 2\n    outputs = []\n    for _ in range(t):\n        buf = io.StringIO()\n        with redirect_stdout(buf):\n            solve_one()\n        outputs.append(buf.getvalue().rstrip('\\n'))\n    sys.stdout.write('\\n'.join(outputs))\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
        problem(
            problem_id='algo-069-practice-p3',
            title='文字列のハッシュ（ローリングハッシュ） を素直に実装する / 3 ケースを連続して解く',
            problem_statement='3 ケース分の入力が続けて与えられる。それぞれについて、文字列 S と T が与えられる。ローリングハッシュを用いて、T が S に何回現れるかを求めよ。',
            input_format='1 行目に 3。\n続く 3 ケースについて:\n1 行目に S。\n2 行目に T。',
            output_format='各ケースの答えを順に出力する。',
            constraints='1 <= |S| <= 2 * 10^5\n1 <= |T| <= |S|\n3 ケースの合計でも同じ方針で処理すること。',
            examples=[
                {
                    'input': '3\naaaa\naa\naaaa\naa\naaaa\naa',
                    'output': '3\n3\n3',
                },
            ],
            canonical_reference_solution="import io\nimport sys\nfrom contextlib import redirect_stdout\n\ndef solve_one() -> None:\n    s = input().strip()\n    t = input().strip()\n    base = 911382323\n    mod = 972663749\n    n = len(s)\n    m = len(t)\n    power = [1] * (n + 1)\n    prefix = [0] * (n + 1)\n    for i, ch in enumerate(s, start=1):\n        power[i] = power[i - 1] * base % mod\n        prefix[i] = (prefix[i - 1] * base + ord(ch)) % mod\n    target = 0\n    for ch in t:\n        target = (target * base + ord(ch)) % mod\n    ans = 0\n    for left in range(n - m + 1):\n        right = left + m\n        value = (prefix[right] - prefix[left] * power[m]) % mod\n        if value == target and s[left:right] == t:\n            ans += 1\n    print(ans)\n\ndef solve() -> None:\n    t = 3\n    outputs = []\n    for _ in range(t):\n        buf = io.StringIO()\n        with redirect_stdout(buf):\n            solve_one()\n        outputs.append(buf.getvalue().rstrip('\\n'))\n    sys.stdout.write('\\n'.join(outputs))\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
