from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('integration')

UNIT_BANK = unit_bank(
    unit_id='algo-058-integration',
    title='辞書順最小の構成 の総合演習',
    unit_kind='integration',
    target_skill='辞書順最小の構成 の総合演習',
    concept_overview='貪欲法は、その時点で最もよさそうな選択を順に確定していく考え方です。後戻りせずに決めてよい条件を見抜く基本を学びます。 この unit では、既習の 辞書順最小の構成 の基本 と 辞書順最小の構成 を素直に実装する を順に使いながら、1 問を分けて解く流れまで確認します。',
    problem_bank=[
        problem(
            problem_id='algo-058-integration-p1',
            title='辞書順最小の構成 の総合演習 / 1 ケースをそのまま解く',
            problem_statement='N 個の文字列 S_i が与えられる。並べる順番を自由に選んで連結するとき、得られる文字列が辞書順で最小になるようにせよ。その最小の文字列を出力する。',
            input_format='1 行目に N。\n続く N 行に S_i。',
            output_format='辞書順最小の連結結果を出力する。',
            constraints='1 <= N <= 2 * 10^5\n各 S_i は英小文字からなる',
            examples=[
                {
                    'input': '3\nba\nb\nab',
                    'output': 'abbab',
                },
            ],
            canonical_reference_solution="from functools import cmp_to_key\n\ndef cmp(a: str, b: str) -> int:\n    if a + b < b + a:\n        return -1\n    if a + b > b + a:\n        return 1\n    return 0\n\ndef solve() -> None:\n    n = int(input())\n    strings = [input().strip() for _ in range(n)]\n    strings.sort(key=cmp_to_key(cmp))\n    print(''.join(strings))\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
        problem(
            problem_id='algo-058-integration-p2',
            title='辞書順最小の構成 の総合演習 / 2 ケースを連続して解く',
            problem_statement='2 ケース分の入力が続けて与えられる。それぞれについて、N 個の文字列 S_i が与えられる。並べる順番を自由に選んで連結するとき、得られる文字列が辞書順で最小になるようにせよ。その最小の文字列を出力する。',
            input_format='1 行目に 2。\n続く 2 ケースについて:\n1 行目に N。\n続く N 行に S_i。',
            output_format='各ケースの答えを順に出力する。',
            constraints='1 <= N <= 2 * 10^5\n各 S_i は英小文字からなる\n2 ケースの合計でも同じ方針で処理すること。',
            examples=[
                {
                    'input': '2\n3\nba\nb\nab\n3\nba\nb\nab',
                    'output': 'abbab\nabbab',
                },
            ],
            canonical_reference_solution="import io\nimport sys\nfrom contextlib import redirect_stdout\n\nfrom functools import cmp_to_key\n\ndef cmp(a: str, b: str) -> int:\n    if a + b < b + a:\n        return -1\n    if a + b > b + a:\n        return 1\n    return 0\n\ndef solve_one() -> None:\n    n = int(input())\n    strings = [input().strip() for _ in range(n)]\n    strings.sort(key=cmp_to_key(cmp))\n    print(''.join(strings))\n\ndef solve() -> None:\n    t = 2\n    outputs = []\n    for _ in range(t):\n        buf = io.StringIO()\n        with redirect_stdout(buf):\n            solve_one()\n        outputs.append(buf.getvalue().rstrip('\\n'))\n    sys.stdout.write('\\n'.join(outputs))\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
        problem(
            problem_id='algo-058-integration-p3',
            title='辞書順最小の構成 の総合演習 / 3 ケースを連続して解く',
            problem_statement='3 ケース分の入力が続けて与えられる。それぞれについて、N 個の文字列 S_i が与えられる。並べる順番を自由に選んで連結するとき、得られる文字列が辞書順で最小になるようにせよ。その最小の文字列を出力する。',
            input_format='1 行目に 3。\n続く 3 ケースについて:\n1 行目に N。\n続く N 行に S_i。',
            output_format='各ケースの答えを順に出力する。',
            constraints='1 <= N <= 2 * 10^5\n各 S_i は英小文字からなる\n3 ケースの合計でも同じ方針で処理すること。',
            examples=[
                {
                    'input': '3\n3\nba\nb\nab\n3\nba\nb\nab\n3\nba\nb\nab',
                    'output': 'abbab\nabbab\nabbab',
                },
            ],
            canonical_reference_solution="import io\nimport sys\nfrom contextlib import redirect_stdout\n\nfrom functools import cmp_to_key\n\ndef cmp(a: str, b: str) -> int:\n    if a + b < b + a:\n        return -1\n    if a + b > b + a:\n        return 1\n    return 0\n\ndef solve_one() -> None:\n    n = int(input())\n    strings = [input().strip() for _ in range(n)]\n    strings.sort(key=cmp_to_key(cmp))\n    print(''.join(strings))\n\ndef solve() -> None:\n    t = 3\n    outputs = []\n    for _ in range(t):\n        buf = io.StringIO()\n        with redirect_stdout(buf):\n            solve_one()\n        outputs.append(buf.getvalue().rstrip('\\n'))\n    sys.stdout.write('\\n'.join(outputs))\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
