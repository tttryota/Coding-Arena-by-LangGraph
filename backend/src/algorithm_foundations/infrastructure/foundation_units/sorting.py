"""Sorting family templates."""

from __future__ import annotations

from .common import ProblemTemplate, array_template


def build_problem_template(
    *,
    theme_id: str,
    key: str,
    category: str,
) -> ProblemTemplate | None:
    del key
    if theme_id == "algo-011":
        return array_template(
            statement="長さ N の整数列 A が与えられる。バブルソートで昇順に並べ替えて出力せよ。",
            input_format="1 行目に N。\n2 行目に A1..AN。",
            output_format="昇順の列を空白区切りで出力する。",
            constraints="1 <= N <= 2000",
            examples=[{"input": "5\n4 1 5 2 3", "output": "1 2 3 4 5"}],
            reference_solution=(
                "def solve() -> None:\n"
                "    n = int(input())\n"
                "    a = list(map(int, input().split()))\n"
                "    for i in range(n):\n"
                "        for j in range(n - 1 - i):\n"
                "            if a[j] > a[j + 1]:\n"
                "                a[j], a[j + 1] = a[j + 1], a[j]\n"
                "    print(*a)\n\n"
                "if __name__ == '__main__':\n"
                "    solve()\n"
            ),
        )
    if theme_id == "algo-012":
        return array_template(
            statement="長さ N の整数列 A が与えられる。選択ソートで昇順に並べ替えて出力せよ。",
            input_format="1 行目に N。\n2 行目に A1..AN。",
            output_format="昇順の列を空白区切りで出力する。",
            constraints="1 <= N <= 2000",
            examples=[{"input": "5\n4 1 5 2 3", "output": "1 2 3 4 5"}],
            reference_solution=(
                "def solve() -> None:\n"
                "    n = int(input())\n"
                "    a = list(map(int, input().split()))\n"
                "    for i in range(n):\n"
                "        best = i\n"
                "        for j in range(i + 1, n):\n"
                "            if a[j] < a[best]:\n"
                "                best = j\n"
                "        a[i], a[best] = a[best], a[i]\n"
                "    print(*a)\n\n"
                "if __name__ == '__main__':\n"
                "    solve()\n"
            ),
        )
    if theme_id == "algo-013":
        return array_template(
            statement="長さ N の整数列 A が与えられる。挿入ソートで昇順に並べ替えて出力せよ。",
            input_format="1 行目に N。\n2 行目に A1..AN。",
            output_format="昇順の列を空白区切りで出力する。",
            constraints="1 <= N <= 2000",
            examples=[{"input": "5\n4 1 5 2 3", "output": "1 2 3 4 5"}],
            reference_solution=(
                "def solve() -> None:\n"
                "    n = int(input())\n"
                "    a = list(map(int, input().split()))\n"
                "    for i in range(1, n):\n"
                "        value = a[i]\n"
                "        j = i - 1\n"
                "        while j >= 0 and a[j] > value:\n"
                "            a[j + 1] = a[j]\n"
                "            j -= 1\n"
                "        a[j + 1] = value\n"
                "    print(*a)\n\n"
                "if __name__ == '__main__':\n"
                "    solve()\n"
            ),
        )
    if theme_id == "algo-014":
        return array_template(
            statement="長さ N の整数列 A が与えられる。マージソートで昇順に並べ替えて出力せよ。",
            input_format="1 行目に N。\n2 行目に A1..AN。",
            output_format="昇順の列を空白区切りで出力する。",
            constraints="1 <= N <= 2 * 10^5",
            examples=[{"input": "5\n4 1 5 2 3", "output": "1 2 3 4 5"}],
            reference_solution=(
                "def merge_sort(arr: list[int]) -> list[int]:\n"
                "    if len(arr) <= 1:\n"
                "        return arr\n"
                "    mid = len(arr) // 2\n"
                "    left = merge_sort(arr[:mid])\n"
                "    right = merge_sort(arr[mid:])\n"
                "    out = []\n"
                "    i = j = 0\n"
                "    while i < len(left) and j < len(right):\n"
                "        if left[i] <= right[j]:\n"
                "            out.append(left[i]); i += 1\n"
                "        else:\n"
                "            out.append(right[j]); j += 1\n"
                "    out.extend(left[i:])\n"
                "    out.extend(right[j:])\n"
                "    return out\n\n"
                "def solve() -> None:\n"
                "    input()\n"
                "    a = list(map(int, input().split()))\n"
                "    print(*merge_sort(a))\n\n"
                "if __name__ == '__main__':\n"
                "    solve()\n"
            ),
        )
    if theme_id == "algo-015":
        return array_template(
            statement="長さ N の整数列 A が与えられる。クイックソートで昇順に並べ替えて出力せよ。",
            input_format="1 行目に N。\n2 行目に A1..AN。",
            output_format="昇順の列を空白区切りで出力する。",
            constraints="1 <= N <= 2 * 10^5",
            examples=[{"input": "5\n4 1 5 2 3", "output": "1 2 3 4 5"}],
            reference_solution=(
                "def quick_sort(arr: list[int]) -> list[int]:\n"
                "    if len(arr) <= 1:\n"
                "        return arr\n"
                "    pivot = arr[len(arr) // 2]\n"
                "    left = [x for x in arr if x < pivot]\n"
                "    mid = [x for x in arr if x == pivot]\n"
                "    right = [x for x in arr if x > pivot]\n"
                "    return quick_sort(left) + mid + quick_sort(right)\n\n"
                "def solve() -> None:\n"
                "    input()\n"
                "    a = list(map(int, input().split()))\n"
                "    print(*quick_sort(a))\n\n"
                "if __name__ == '__main__':\n"
                "    solve()\n"
            ),
        )
    if theme_id == "algo-016":
        return array_template(
            statement="長さ N の整数列 A が与えられる。ヒープソートで昇順に並べ替えて出力せよ。",
            input_format="1 行目に N。\n2 行目に A1..AN。",
            output_format="昇順の列を空白区切りで出力する。",
            constraints="1 <= N <= 2 * 10^5",
            examples=[{"input": "5\n4 1 5 2 3", "output": "1 2 3 4 5"}],
            reference_solution=(
                "import heapq\n\n"
                "def solve() -> None:\n"
                "    input()\n"
                "    heap = list(map(int, input().split()))\n"
                "    heapq.heapify(heap)\n"
                "    out = [heapq.heappop(heap) for _ in range(len(heap))]\n"
                "    print(*out)\n\n"
                "if __name__ == '__main__':\n"
                "    solve()\n"
            ),
        )
    if theme_id == "algo-017":
        return array_template(
            statement="長さ N の非負整数列 A が与えられる。計数ソートで昇順に並べ替えて出力せよ。",
            input_format="1 行目に N。\n2 行目に A1..AN。",
            output_format="昇順の列を空白区切りで出力する。",
            constraints="1 <= N <= 2 * 10^5\n0 <= Ai <= 10^6",
            examples=[{"input": "5\n4 1 5 2 3", "output": "1 2 3 4 5"}],
            reference_solution=(
                "def solve() -> None:\n"
                "    input()\n"
                "    a = list(map(int, input().split()))\n"
                "    limit = max(a, default=0)\n"
                "    cnt = [0] * (limit + 1)\n"
                "    for value in a:\n"
                "        cnt[value] += 1\n"
                "    out = []\n"
                "    for value, freq in enumerate(cnt):\n"
                "        out.extend([value] * freq)\n"
                "    print(*out)\n\n"
                "if __name__ == '__main__':\n"
                "    solve()\n"
            ),
        )
    if theme_id == "algo-018":
        return array_template(
            statement="長さ N の非負整数列 A が与えられる。基数ソートで昇順に並べ替えて出力せよ。",
            input_format="1 行目に N。\n2 行目に A1..AN。",
            output_format="昇順の列を空白区切りで出力する。",
            constraints="1 <= N <= 2 * 10^5\n0 <= Ai <= 10^9",
            examples=[{"input": "5\n4 1 5 2 3", "output": "1 2 3 4 5"}],
            reference_solution=(
                "def solve() -> None:\n"
                "    input()\n"
                "    a = list(map(int, input().split()))\n"
                "    exp = 1\n"
                "    while True:\n"
                "        buckets = [[] for _ in range(10)]\n"
                "        done = True\n"
                "        for value in a:\n"
                "            digit = (value // exp) % 10\n"
                "            buckets[digit].append(value)\n"
                "            if value // exp >= 10:\n"
                "                done = False\n"
                "        a = [value for bucket in buckets for value in bucket]\n"
                "        if done:\n"
                "            break\n"
                "        exp *= 10\n"
                "    print(*a)\n\n"
                "if __name__ == '__main__':\n"
                "    solve()\n"
            ),
        )
    if category == "ソート":
        return array_template(
            statement="長さ N の整数列 A が与えられる。A を昇順に並べ替えて出力せよ。",
            input_format="1 行目に N。\n2 行目に A1..AN。",
            output_format="昇順に並べた列を空白区切りで出力する。",
            constraints="1 <= N <= 2 * 10^5",
            examples=[{"input": "5\n4 1 5 2 3", "output": "1 2 3 4 5"}],
            reference_solution=(
                "def solve() -> None:\n"
                "    input()\n"
                "    a = list(map(int, input().split()))\n"
                "    a.sort()\n"
                "    print(*a)\n\n"
                "if __name__ == '__main__':\n"
                "    solve()\n"
            ),
        )
    return None
