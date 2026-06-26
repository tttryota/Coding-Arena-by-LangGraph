from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('foundation')

UNIT_BANK = unit_bank(
    unit_id='algo-093-stack-brackets',
    title='括弧対応と後入れ先出し',
    unit_kind='foundation',
    target_skill='括弧対応と後入れ先出し',
    concept_overview='開き括弧を積み、閉じ括弧が来たら直前の開き括弧と対応づけるように、直近の情報をあとから取り出す考え方を使います。',
    problem_bank=[
        problem(
            problem_id='algo-093-stack-brackets-p1',
            title='括弧対応と後入れ先出し / 丸括弧列が正しいか判定する',
            problem_statement='括弧列 S が与えられる。対応が正しい括弧列なら Yes、そうでなければ No を出力せよ。',
            input_format='1 行目に S。',
            output_format='Yes / No を出力する。',
            constraints="1 <= |S| <= 2 * 10^5\nS は '(' と ')' からなる",
            examples=[
                {
                    'input': '(()())',
                    'output': 'Yes',
                },
            ],
            canonical_reference_solution="def solve() -> None:\n    s = input().strip()\n    depth = 0\n    for ch in s:\n        if ch == '(':\n            depth += 1\n        else:\n            depth -= 1\n        if depth < 0:\n            print('No')\n            return\n    print('Yes' if depth == 0 else 'No')\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=default_rubric("foundation"),
        ),
        problem(
            problem_id='algo-093-stack-brackets-p2',
            title='括弧対応と後入れ先出し / 対応が崩れる最初の位置を求める',
            problem_statement='括弧列 S が与えられる。左から見てはじめて対応が崩れる 1-indexed の位置を出力せよ。最後まで崩れず、しかも正しい括弧列なら 0 を出力する。最後まで崩れないが開き括弧が余るときは `|S|+1` を出力する。',
            input_format='1 行目に S。',
            output_format='最初に崩れる位置、正しければ 0、開き括弧だけ余るなら |S|+1 を出力する。',
            constraints="1 <= |S| <= 2 * 10^5\nS は '(' と ')' からなる",
            examples=[
                {
                    'input': '())(()',
                    'output': '3',
                },
            ],
            canonical_reference_solution="def solve() -> None:\n    s = input().strip()\n    depth = 0\n    for idx, ch in enumerate(s, start=1):\n        if ch == '(':\n            depth += 1\n        else:\n            depth -= 1\n        if depth < 0:\n            print(idx)\n            return\n    print(0 if depth == 0 else len(s) + 1)\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=default_rubric("foundation"),
        ),
        problem(
            problem_id='algo-093-stack-brackets-p3',
            title='括弧対応と後入れ先出し / 対応している組の数を数える',
            problem_statement='括弧列 S が与えられる。左から見て正しく対応づけられた `()` の組数を数えよ。',
            input_format='1 行目に S。',
            output_format='対応づけられた組数を出力する。',
            constraints="1 <= |S| <= 2 * 10^5\nS は '(' と ')' からなる",
            examples=[
                {
                    'input': '(()())',
                    'output': '3',
                },
            ],
            canonical_reference_solution="def solve() -> None:\n    s = input().strip()\n    depth = 0\n    pairs = 0\n    for ch in s:\n        if ch == '(':\n            depth += 1\n        elif depth > 0:\n            depth -= 1\n            pairs += 1\n    print(pairs)\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=default_rubric("foundation"),
        ),
        problem(
            problem_id='algo-093-stack-brackets-p4',
            title='括弧対応と後入れ先出し / 3 種類の括弧列を正しく判定する',
            problem_statement='括弧列 S が与えられる。`()`、`[]`、`{}` の対応がすべて正しければ Yes、そうでなければ No を出力せよ。',
            input_format='1 行目に S。',
            output_format='Yes / No を出力する。',
            constraints="1 <= |S| <= 2 * 10^5\nS は '()[]{}' からなる",
            examples=[
                {
                    'input': '{[()()]}',
                    'output': 'Yes',
                },
            ],
            canonical_reference_solution="def solve() -> None:\n    s = input().strip()\n    pair = {')': '(', ']': '[', '}': '{'}\n    stack = []\n    for ch in s:\n        if ch in '([{':\n            stack.append(ch)\n        else:\n            if not stack or stack[-1] != pair[ch]:\n                print('No')\n                return\n            stack.pop()\n    print('Yes' if not stack else 'No')\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=default_rubric("foundation"),
        ),
        problem(
            problem_id='algo-093-stack-brackets-p5',
            title='括弧対応と後入れ先出し / 各接頭辞が壊れていないか数える',
            problem_statement='括弧列 S が与えられる。各接頭辞について、対応が途中で壊れていないものの個数を求めよ。',
            input_format='1 行目に S。',
            output_format='条件を満たす接頭辞の個数を出力する。',
            constraints="1 <= |S| <= 2 * 10^5\nS は '(' と ')' からなる",
            examples=[
                {
                    'input': '(()())',
                    'output': '6',
                },
            ],
            canonical_reference_solution="def solve() -> None:\n    s = input().strip()\n    depth = 0\n    ans = 0\n    for ch in s:\n        if ch == '(':\n            depth += 1\n        else:\n            depth -= 1\n        if depth < 0:\n            break\n        ans += 1\n    print(ans)\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=default_rubric("foundation"),
        ),
        problem(
            problem_id='algo-093-stack-brackets-p6',
            title='括弧対応と後入れ先出し / 2 本の括弧列を順に検査する',
            problem_statement='2 本の括弧列 S, T が与えられる。それぞれが正しい括弧列かを判定し、両方正しければ Yes、そうでなければ No を出力せよ。',
            input_format='1 行目に S。\n2 行目に T。',
            output_format='Yes / No を出力する。',
            constraints="1 <= |S|, |T| <= 2 * 10^5\nS, T は '(' と ')' からなる",
            examples=[
                {
                    'input': '(()())\n(())()',
                    'output': 'Yes',
                },
            ],
            canonical_reference_solution="def valid(s: str) -> bool:\n    depth = 0\n    for ch in s:\n        if ch == '(':\n            depth += 1\n        else:\n            depth -= 1\n        if depth < 0:\n            return False\n    return depth == 0\n\ndef solve() -> None:\n    s = input().strip()\n    t = input().strip()\n    print('Yes' if valid(s) and valid(t) else 'No')\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=default_rubric("foundation"),
        ),
    ],
)
