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
    concept_overview='最適順が決まれば、得られる最小連結文字列そのものを材料として別の問いにも答えられます。ここでは最小連結文字列を 1 度作ってから、その中の指定位置の文字を答えます。',
    problem_bank=[
        problem(
            problem_id='algo-058-integration-p1',
            title='辞書順最小の構成 の総合演習 / 最小連結文字列の指定位置の文字を答える',
            problem_statement='N 個の文字列 S_i と Q 個の問い合わせ K_j が与えられる。文字列を並べ替えて連結したとき、得られる文字列が辞書順で最小になるようにせよ。各問い合わせについて、その最小連結文字列の K_j 文字目を答えよ。',
            input_format='1 行目に N Q。\n続く N 行に S_i。\n続く Q 行に K_j。',
            output_format='各問い合わせの答えを 1 行ずつ出力する。',
            constraints='1 <= N, Q <= 2 * 10^5\n各 S_i は英小文字からなる\n文字列長の総和は 2 * 10^5 以下\n1 <= K_j <= 最小連結文字列の長さ',
            examples=[{'input': '3 4\nba\nb\nab\n1\n3\n4\n5', 'output': 'a\nb\na\nb'}],
            canonical_reference_solution="from functools import cmp_to_key\n\n\ndef cmp(a: str, b: str) -> int:\n    if a + b < b + a:\n        return -1\n    if a + b > b + a:\n        return 1\n    return 0\n\n\ndef solve() -> None:\n    import sys\n\n    input = sys.stdin.readline\n    n, q = map(int, input().split())\n    strings = [input().strip() for _ in range(n)]\n    strings.sort(key=cmp_to_key(cmp))\n    result = ''.join(strings)\n    out = []\n    for _ in range(q):\n        k = int(input())\n        out.append(result[k - 1])\n    sys.stdout.write('\\n'.join(out))\n\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
