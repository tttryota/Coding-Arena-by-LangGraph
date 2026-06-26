"""Search-family templates."""

from __future__ import annotations

from .common import ProblemTemplate, array_template


def build_problem_template(
    *,
    theme_id: str,
    key: str,
    category: str,
) -> ProblemTemplate | None:
    if theme_id == "algo-003":
        return array_template(
            statement="下に凸な数列 A が与えられる。最小値を求めよ。",
            input_format="1 行目に N。\n2 行目に A1..AN。",
            output_format="最小値を出力する。",
            constraints="3 <= N <= 2 * 10^5\nA は下に凸",
            examples=[{"input": "7\n9 6 4 2 3 5 8", "output": "2"}],
            reference_solution=(
                "def solve() -> None:\n"
                "    n = int(input())\n"
                "    a = list(map(int, input().split()))\n"
                "    left, right = 0, n - 1\n"
                "    while right - left > 3:\n"
                "        m1 = left + (right - left) // 3\n"
                "        m2 = right - (right - left) // 3\n"
                "        if a[m1] <= a[m2]:\n"
                "            right = m2 - 1\n"
                "        else:\n"
                "            left = m1 + 1\n"
                "    print(min(a[left:right + 1]))\n\n"
                "if __name__ == '__main__':\n"
                "    solve()\n"
            ),
        )
    if theme_id == "algo-006":
        return array_template(
            statement="長さ N の整数列 A と目標値 S が与えられる。bit 全探索で部分集合の和が S になるか判定せよ。",
            input_format="1 行目に N S。\n2 行目に A1..AN。",
            output_format="Yes / No を出力する。",
            constraints="1 <= N <= 20",
            examples=[{"input": "4 11\n2 5 9 4", "output": "Yes"}],
            reference_solution=(
                "def solve() -> None:\n"
                "    n, s = map(int, input().split())\n"
                "    a = list(map(int, input().split()))\n"
                "    for mask in range(1 << n):\n"
                "        total = 0\n"
                "        for i in range(n):\n"
                "            if mask >> i & 1:\n"
                "                total += a[i]\n"
                "        if total == s:\n"
                "            print('Yes')\n"
                "            return\n"
                "    print('No')\n\n"
                "if __name__ == '__main__':\n"
                "    solve()\n"
            ),
        )
    if theme_id == "algo-007":
        return array_template(
            statement=(
                "N 頂点の完全グラフの重み行列が与えられる。"
                " 頂点 1 から始めて残りを 1 回ずつ訪れる順列の中で、移動コスト合計の最小値を求めよ。"
            ),
            input_format="1 行目に N。\n続く N 行に重み行列。",
            output_format="最小コストを出力する。",
            constraints="2 <= N <= 8",
            examples=[{"input": "3\n0 2 5\n2 0 4\n5 4 0", "output": "6"}],
            reference_solution=(
                "from itertools import permutations\n\n"
                "def solve() -> None:\n"
                "    n = int(input())\n"
                "    cost = [list(map(int, input().split())) for _ in range(n)]\n"
                "    ans = 10 ** 18\n"
                "    for order in permutations(range(1, n)):\n"
                "        total = 0\n"
                "        prev = 0\n"
                "        for nxt in order:\n"
                "            total += cost[prev][nxt]\n"
                "            prev = nxt\n"
                "        ans = min(ans, total)\n"
                "    print(ans)\n\n"
                "if __name__ == '__main__':\n"
                "    solve()\n"
            ),
        )
    if theme_id == "algo-008":
        return array_template(
            statement="長さ N の整数列 A と目標値 S が与えられる。半分全列挙で部分集合の和が S になるか判定せよ。",
            input_format="1 行目に N S。\n2 行目に A1..AN。",
            output_format="Yes / No を出力する。",
            constraints="1 <= N <= 40",
            examples=[{"input": "4 11\n2 5 9 4", "output": "Yes"}],
            reference_solution=(
                "from bisect import bisect_left\n\n"
                "def sums(values: list[int]) -> list[int]:\n"
                "    out = [0]\n"
                "    for value in values:\n"
                "        out += [cur + value for cur in out]\n"
                "    return out\n\n"
                "def solve() -> None:\n"
                "    n, s = map(int, input().split())\n"
                "    a = list(map(int, input().split()))\n"
                "    mid = n // 2\n"
                "    left = sums(a[:mid])\n"
                "    right = sorted(sums(a[mid:]))\n"
                "    for value in left:\n"
                "        need = s - value\n"
                "        idx = bisect_left(right, need)\n"
                "        if idx < len(right) and right[idx] == need:\n"
                "            print('Yes')\n"
                "            return\n"
                "    print('No')\n\n"
                "if __name__ == '__main__':\n"
                "    solve()\n"
            ),
        )
    if theme_id == "algo-009":
        return array_template(
            statement=(
                "長さ N の正整数列 A と整数 S が与えられる。"
                " 総和が S 以上となる連続部分列のうち、長さの最小値を求めよ。存在しなければ 0 を出力せよ。"
            ),
            input_format="1 行目に N S。\n2 行目に A1..AN。",
            output_format="最小長を出力する。",
            constraints="1 <= N <= 2 * 10^5\n1 <= Ai, S <= 10^9",
            examples=[{"input": "6 11\n2 3 1 2 4 3", "output": "3"}],
            reference_solution=(
                "def solve() -> None:\n"
                "    n, s = map(int, input().split())\n"
                "    a = list(map(int, input().split()))\n"
                "    ans = n + 1\n"
                "    total = 0\n"
                "    left = 0\n"
                "    for right, value in enumerate(a):\n"
                "        total += value\n"
                "        while total >= s:\n"
                "            ans = min(ans, right - left + 1)\n"
                "            total -= a[left]\n"
                "            left += 1\n"
                "    print(0 if ans == n + 1 else ans)\n\n"
                "if __name__ == '__main__':\n"
                "    solve()\n"
            ),
        )
    if theme_id == "algo-010":
        return array_template(
            statement=(
                "整数 N と目標値 T が与えられる。乱数 seed=0 を用いて 5000 回 0..N をランダムに試し、"
                " T に最も近い値を出力せよ。差が同じなら小さい方を採用する。"
            ),
            input_format="1 行目に N T。",
            output_format="選ばれた値を出力する。",
            constraints="1 <= N <= 10^9",
            examples=[{"input": "10 7", "output": "7"}],
            reference_solution=(
                "import random\n\n"
                "def solve() -> None:\n"
                "    n, target = map(int, input().split())\n"
                "    random.seed(0)\n"
                "    best = 0\n"
                "    best_diff = abs(target)\n"
                "    for _ in range(5000):\n"
                "        cand = random.randint(0, n)\n"
                "        diff = abs(cand - target)\n"
                "        if diff < best_diff or (diff == best_diff and cand < best):\n"
                "            best = cand\n"
                "            best_diff = diff\n"
                "    print(best)\n\n"
                "if __name__ == '__main__':\n"
                "    solve()\n"
            ),
        )
    if "二分探索" in key:
        return array_template(
            statement=(
                "昇順に並んだ長さ N の整数列 A と Q 個の値 x が与えられる。"
                " 各 x について、A の中で x 以上となる最初の位置を 1-indexed で求め、"
                " 存在しない場合は -1 を出力せよ。"
            ),
            input_format="1 行目に N Q。\n2 行目に A1..AN。\n続く Q 行に x。",
            output_format="各問い合わせの答えを 1 行ずつ出力する。",
            constraints="1 <= N, Q <= 2 * 10^5\nA は昇順",
            examples=[{"input": "5 3\n1 3 5 8 13\n4\n13\n20", "output": "3\n5\n-1"}],
            reference_solution=(
                "from bisect import bisect_left\n\n"
                "def solve() -> None:\n"
                "    import sys\n"
                "    input = sys.stdin.readline\n"
                "    n, q = map(int, input().split())\n"
                "    a = list(map(int, input().split()))\n"
                "    out = []\n"
                "    for _ in range(q):\n"
                "        x = int(input())\n"
                "        idx = bisect_left(a, x)\n"
                "        out.append(str(idx + 1) if idx < n else '-1')\n"
                "    sys.stdout.write('\\n'.join(out))\n\n"
                "if __name__ == '__main__':\n"
                "    solve()\n"
            ),
        )
    if any(token in key for token in ("全探索", "bit全探索", "順列全探索", "半分全列挙", "三分探索", "尺取り法")):
        return array_template(
            statement=(
                "長さ N の整数列 A と目標値 S が与えられる。"
                " 連続部分列または要素の選び方を工夫して、条件を満たすものが存在するか判定せよ。"
            ),
            input_format="1 行目に N S。\n2 行目に A1..AN。",
            output_format="条件を満たすなら Yes、そうでなければ No を出力する。",
            constraints="1 <= N <= 40",
            examples=[{"input": "4 11\n2 5 9 4", "output": "Yes"}],
            reference_solution=(
                "def solve() -> None:\n"
                "    n, s = map(int, input().split())\n"
                "    a = list(map(int, input().split()))\n"
                "    for mask in range(1 << n):\n"
                "        total = 0\n"
                "        for i in range(n):\n"
                "            if mask >> i & 1:\n"
                "                total += a[i]\n"
                "        if total == s:\n"
                "            print('Yes')\n"
                "            return\n"
                "    print('No')\n\n"
                "if __name__ == '__main__':\n"
                "    solve()\n"
            ),
        )
    if category == "探索":
        return array_template(
            statement="長さ N の整数列 A と整数 x が与えられる。A に x が含まれるか判定せよ。",
            input_format="1 行目に N x。\n2 行目に A1..AN。",
            output_format="含まれるなら Yes、そうでなければ No。",
            constraints="1 <= N <= 2 * 10^5",
            examples=[{"input": "5 3\n1 4 3 7 9", "output": "Yes"}],
            reference_solution=(
                "def solve() -> None:\n"
                "    n, x = map(int, input().split())\n"
                "    a = list(map(int, input().split()))\n"
                "    print('Yes' if x in a else 'No')\n\n"
                "if __name__ == '__main__':\n"
                "    solve()\n"
            ),
        )
    return None
