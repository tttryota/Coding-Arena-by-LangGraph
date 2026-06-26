from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('integration')

UNIT_BANK = unit_bank(
    unit_id='algo-093-stack-cancel',
    title='スタックで消去をシミュレート',
    unit_kind='integration',
    target_skill='スタックで消去をシミュレート',
    concept_overview='文字や値を左から見ながら積み、条件が合ったら直前のものを消す形で、途中状態をそのまま再現する考え方です。',
    problem_bank=[
        problem(
            problem_id='algo-093-stack-cancel-p1',
            title='スタックで消去をシミュレート / 同じ文字の連続消去を行う',
            problem_statement='英小文字からなる文字列 S が与えられる。左から順に見て、直前と同じ文字が現れたら 2 文字まとめて消す操作を繰り返した最終文字列を出力せよ。',
            input_format='1 行目に S。',
            output_format='最終文字列を出力する。',
            constraints='1 <= |S| <= 2 * 10^5',
            examples=[
                {
                    'input': 'abbaca',
                    'output': 'ca',
                },
            ],
            canonical_reference_solution="def solve() -> None:\n    s = input().strip()\n    stack = []\n    for ch in s:\n        if stack and stack[-1] == ch:\n            stack.pop()\n        else:\n            stack.append(ch)\n    print(''.join(stack))\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=default_rubric("integration"),
        ),
        problem(
            problem_id='algo-093-stack-cancel-p2',
            title='スタックで消去をシミュレート / backspace を含む文字列を再現する',
            problem_statement='文字列 S が与えられる。英小文字はそのまま追加し、`#` は 1 文字削除するとみなしたとき、最後に残る文字列を出力せよ。',
            input_format='1 行目に S。',
            output_format='最終文字列を出力する。',
            constraints="1 <= |S| <= 2 * 10^5\n'#' が現れる時点で削除対象は存在する",
            examples=[
                {
                    'input': 'ab#c##de',
                    'output': 'de',
                },
            ],
            canonical_reference_solution="def solve() -> None:\n    s = input().strip()\n    stack = []\n    for ch in s:\n        if ch == '#':\n            stack.pop()\n        else:\n            stack.append(ch)\n    print(''.join(stack))\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=default_rubric("integration"),
        ),
        problem(
            problem_id='algo-093-stack-cancel-p3',
            title='スタックで消去をシミュレート / AB がそろったら消す処理を行う',
            problem_statement='文字列 S が与えられる。左から順に見て、末尾が `A` のときに次の文字が `B` なら `AB` をまとめて消す。これを最後まで行った結果を出力せよ。',
            input_format='1 行目に S。',
            output_format='最終文字列を出力する。',
            constraints='1 <= |S| <= 2 * 10^5\nS は英大文字からなる',
            examples=[
                {
                    'input': 'CABABB',
                    'output': 'C',
                },
            ],
            canonical_reference_solution="def solve() -> None:\n    s = input().strip()\n    stack = []\n    for ch in s:\n        if stack and stack[-1] == 'A' and ch == 'B':\n            stack.pop()\n        else:\n            stack.append(ch)\n    print(''.join(stack))\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=default_rubric("integration"),
        ),
    ],
)
