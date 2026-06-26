"""Stack family definitions for algorithm foundations."""

from __future__ import annotations

from typing import Final

from .common import ProblemTemplate, SpecialThemeUnitDef, array_template

SPECIAL_THEME_UNITS: Final[tuple[SpecialThemeUnitDef, ...]] = (
    ("algo-093", 0, "stack-basics", "スタックの基本操作", "foundation"),
    ("algo-093", 1, "stack-brackets", "括弧対応と後入れ先出し", "foundation"),
    ("algo-093", 2, "stack-cancel", "スタックで消去をシミュレート", "integration"),
)

SPECIAL_UNIT_CONCEPT_OVERVIEWS: Final[dict[str, str]] = {
    "algo-093-stack-basics": "スタックは、最後に入れたものから先に取り出す入れ物です。まずは push・pop・top を順番どおりに扱えるようになることを目指します。",
    "algo-093-stack-brackets": "開き括弧を積み、閉じ括弧が来たら直前の開き括弧と対応づけるように、直近の情報をあとから取り出す考え方を使います。",
    "algo-093-stack-cancel": "文字や値を左から見ながら積み、条件が合ったら直前のものを消す形で、途中状態をそのまま再現する考え方です。",
}


def build_problem_template(unit_id: str) -> ProblemTemplate | None:
    if unit_id == "algo-093-stack-brackets":
        return array_template(
            statement="括弧列 S が与えられる。対応が正しい括弧列なら Yes、そうでなければ No を出力せよ。",
            input_format="1 行目に S。",
            output_format="Yes / No を出力する。",
            constraints="1 <= |S| <= 2 * 10^5\nS は '(' と ')' からなる",
            examples=[{"input": "(()())", "output": "Yes"}],
            reference_solution=(
                "def solve() -> None:\n"
                "    s = input().strip()\n"
                "    depth = 0\n"
                "    for ch in s:\n"
                "        if ch == '(':\n"
                "            depth += 1\n"
                "        else:\n"
                "            depth -= 1\n"
                "        if depth < 0:\n"
                "            print('No')\n"
                "            return\n"
                "    print('Yes' if depth == 0 else 'No')\n\n"
                "if __name__ == '__main__':\n"
                "    solve()\n"
            ),
        )
    if unit_id == "algo-093-stack-cancel":
        return array_template(
            statement=(
                "英小文字からなる文字列 S が与えられる。"
                " 左から順に見て、直前と同じ文字が現れたら 2 文字まとめて消す操作を繰り返した最終文字列を出力せよ。"
            ),
            input_format="1 行目に S。",
            output_format="最終文字列を出力する。",
            constraints="1 <= |S| <= 2 * 10^5",
            examples=[{"input": "abbaca", "output": "ca"}],
            reference_solution=(
                "def solve() -> None:\n"
                "    s = input().strip()\n"
                "    stack = []\n"
                "    for ch in s:\n"
                "        if stack and stack[-1] == ch:\n"
                "            stack.pop()\n"
                "        else:\n"
                "            stack.append(ch)\n"
                "    print(''.join(stack))\n\n"
                "if __name__ == '__main__':\n"
                "    solve()\n"
            ),
        )
    if unit_id == "algo-093-stack-basics":
        return array_template(
            statement=(
                "Q 個の操作が与えられる。"
                " `1 x` は x を積み、`2` は一番上を取り除き、`3` は一番上の値を出力せよ。"
            ),
            input_format="1 行目に Q。\n続く Q 行に操作。",
            output_format="type=3 のたびに一番上の値を 1 行ずつ出力する。",
            constraints="1 <= Q <= 2 * 10^5\ntype=2,3 の時点でスタックは空でない",
            examples=[{"input": "7\n1 3\n1 5\n3\n2\n3\n1 9\n3", "output": "5\n3\n9"}],
            reference_solution=(
                "def solve() -> None:\n"
                "    import sys\n"
                "    input = sys.stdin.readline\n"
                "    q = int(input())\n"
                "    stack = []\n"
                "    out = []\n"
                "    for _ in range(q):\n"
                "        parts = list(map(int, input().split()))\n"
                "        if parts[0] == 1:\n"
                "            stack.append(parts[1])\n"
                "        elif parts[0] == 2:\n"
                "            stack.pop()\n"
                "        else:\n"
                "            out.append(str(stack[-1]))\n"
                "    sys.stdout.write('\\n'.join(out))\n\n"
                "if __name__ == '__main__':\n"
                "    solve()\n"
            ),
        )
    return None
