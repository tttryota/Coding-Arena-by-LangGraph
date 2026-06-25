"""Greedy-family templates."""

from __future__ import annotations

from .common import ProblemTemplate, array_template


def build_problem_template(
    *,
    theme_id: str,
    key: str,
    category: str,
) -> ProblemTemplate | None:
    del theme_id, key
    if category == "貪欲法":
        return array_template(
            statement="N 個の区間 [Li, Ri] が与えられる。互いに重ならないように選べる区間数の最大値を求めよ。",
            input_format="1 行目に N。\n続く N 行に Li Ri。",
            output_format="選べる区間数の最大値を出力する。",
            constraints="1 <= N <= 2 * 10^5",
            examples=[{"input": "4\n1 3\n2 5\n4 6\n6 7", "output": "3"}],
            reference_solution=(
                "def solve() -> None:\n"
                "    import sys\n"
                "    input = sys.stdin.readline\n"
                "    n = int(input())\n"
                "    intervals = [tuple(map(int, input().split())) for _ in range(n)]\n"
                "    intervals.sort(key=lambda item: item[1])\n"
                "    ans = 0\n"
                "    current_end = -10 ** 18\n"
                "    for left, right in intervals:\n"
                "        if left < current_end:\n"
                "            continue\n"
                "        ans += 1\n"
                "        current_end = right\n"
                "    print(ans)\n\n"
                "if __name__ == '__main__':\n"
                "    solve()\n"
            ),
        )
    return None
