"""Queue and deque family definitions for algorithm foundations."""

from __future__ import annotations

from typing import Final

from .common import ProblemTemplate, SpecialThemeUnitDef, array_template

SPECIAL_THEME_UNITS: Final[tuple[SpecialThemeUnitDef, ...]] = (
    ("algo-094", 0, "queue-basics", "キューの基本操作", "foundation"),
    ("algo-094", 1, "deque-basics", "デックの基本操作", "foundation"),
)

SPECIAL_UNIT_CONCEPT_OVERVIEWS: Final[dict[str, str]] = {
    "algo-094-queue-basics": "キューは、先に入れたものから先に取り出す入れ物です。まずは末尾に追加し、先頭から取り出す流れを素直に扱えるようにします。",
    "algo-094-deque-basics": "デックは、前後どちらの端にも追加・削除できる入れ物です。どちらの端を使う操作なのかを整理して扱う練習をします。",
}


def build_problem_template(unit_id: str) -> ProblemTemplate | None:
    if unit_id == "algo-094-deque-basics":
        return array_template(
            statement=(
                "Q 個の操作が与えられる。"
                " `1 x` は先頭に追加、`2 x` は末尾に追加、`3` は先頭を出力して削除、`4` は末尾を出力して削除せよ。"
            ),
            input_format="1 行目に Q。\n続く Q 行に操作。",
            output_format="type=3,4 のたびに取り出した値を 1 行ずつ出力する。",
            constraints="1 <= Q <= 2 * 10^5",
            examples=[{"input": "6\n1 3\n2 8\n3\n1 2\n4\n3", "output": "3\n8\n2"}],
            reference_solution=(
                "from collections import deque\n\n"
                "def solve() -> None:\n"
                "    import sys\n"
                "    input = sys.stdin.readline\n"
                "    q = int(input())\n"
                "    dq = deque()\n"
                "    out = []\n"
                "    for _ in range(q):\n"
                "        parts = list(map(int, input().split()))\n"
                "        t = parts[0]\n"
                "        if t == 1:\n"
                "            dq.appendleft(parts[1])\n"
                "        elif t == 2:\n"
                "            dq.append(parts[1])\n"
                "        elif t == 3:\n"
                "            out.append(str(dq.popleft()))\n"
                "        else:\n"
                "            out.append(str(dq.pop()))\n"
                "    sys.stdout.write('\\n'.join(out))\n\n"
                "if __name__ == '__main__':\n"
                "    solve()\n"
            ),
        )
    if unit_id == "algo-094-queue-basics":
        return array_template(
            statement=(
                "Q 個の操作が与えられる。"
                " `1 x` は末尾に x を追加し、`2` は先頭を取り除き、`3` は先頭の値を出力せよ。"
            ),
            input_format="1 行目に Q。\n続く Q 行に操作。",
            output_format="type=3 のたびに先頭の値を 1 行ずつ出力する。",
            constraints="1 <= Q <= 2 * 10^5",
            examples=[{"input": "6\n1 4\n1 7\n3\n2\n1 9\n3", "output": "4\n7"}],
            reference_solution=(
                "from collections import deque\n\n"
                "def solve() -> None:\n"
                "    import sys\n"
                "    input = sys.stdin.readline\n"
                "    q = int(input())\n"
                "    queue = deque()\n"
                "    out = []\n"
                "    for _ in range(q):\n"
                "        parts = list(map(int, input().split()))\n"
                "        if parts[0] == 1:\n"
                "            queue.append(parts[1])\n"
                "        elif parts[0] == 2:\n"
                "            queue.popleft()\n"
                "        else:\n"
                "            out.append(str(queue[0]))\n"
                "    sys.stdout.write('\\n'.join(out))\n\n"
                "if __name__ == '__main__':\n"
                "    solve()\n"
            ),
        )
    return None
