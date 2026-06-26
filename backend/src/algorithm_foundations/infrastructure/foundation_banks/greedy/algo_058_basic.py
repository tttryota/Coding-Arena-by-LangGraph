from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('foundation')

UNIT_BANK = unit_bank(
    unit_id='algo-058-basic',
    title='辞書順最小の構成 の基本',
    unit_kind='foundation',
    target_skill='辞書順最小の構成 の基本',
    concept_overview='辞書順最小の構成では、2 つの文字列 a, b について a+b と b+a のどちらが小さいかを比べて順序を決めます。まずは 2 文字列だけの比較から、この規則そのものを確認します。',
    problem_bank=[
        problem(
            problem_id='algo-058-basic-p1',
            title='辞書順最小の構成 の基本 / 2 つの文字列をどちらの順で連結すべきか判定する',
            problem_statement='2 つの文字列 S, T が与えられる。`S + T` と `T + S` のうち辞書順で小さいほうを出力せよ。',
            input_format='1 行目に S。\n2 行目に T。',
            output_format='辞書順で小さい連結結果を出力する。',
            constraints='S, T は英小文字からなる\n1 <= |S| + |T| <= 2 * 10^5',
            examples=[{'input': 'ba\nab', 'output': 'abba'}],
            canonical_reference_solution="def solve() -> None:\n    s = input().strip()\n    t = input().strip()\n    if s + t <= t + s:\n        print(s + t)\n    else:\n        print(t + s)\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
