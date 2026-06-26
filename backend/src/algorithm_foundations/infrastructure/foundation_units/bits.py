"""Bit-operation family templates."""

from __future__ import annotations

from .common import ProblemTemplate, array_template


def build_problem_template(
    *,
    theme_id: str,
    key: str,
    category: str,
) -> ProblemTemplate | None:
    del category
    if theme_id == "algo-122":
        return array_template(
            statement=(
                "長さ 2^N の配列 A, B が与えられる。"
                " OR 畳み込み C を `C[s] = Σ A[x]B[y] (x OR y = s)` で定義する。"
                " すべての C[s] を求めよ。"
            ),
            input_format="1 行目に N。\n2 行目に A。\n3 行目に B。",
            output_format="C を空白区切りで出力する。",
            constraints="1 <= N <= 17\n0 <= Ai, Bi <= 10^9+7",
            examples=[{"input": "2\n1 2 3 4\n5 6 7 8", "output": "5 28 43 184"}],
            reference_solution=(
                "def zeta(arr: list[int], n: int) -> None:\n"
                "    for bit in range(n):\n"
                "        for mask in range(1 << n):\n"
                "            if not (mask >> bit & 1):\n"
                "                arr[mask | (1 << bit)] += arr[mask]\n\n"
                "def mobius(arr: list[int], n: int) -> None:\n"
                "    for bit in range(n):\n"
                "        for mask in range(1 << n):\n"
                "            if not (mask >> bit & 1):\n"
                "                arr[mask | (1 << bit)] -= arr[mask]\n\n"
                "def solve() -> None:\n"
                "    n = int(input())\n"
                "    a = list(map(int, input().split()))\n"
                "    b = list(map(int, input().split()))\n"
                "    zeta(a, n)\n"
                "    zeta(b, n)\n"
                "    c = [x * y for x, y in zip(a, b, strict=False)]\n"
                "    mobius(c, n)\n"
                "    print(*c)\n\n"
                "if __name__ == '__main__':\n"
                "    solve()\n"
            ),
        )
    if theme_id == "algo-115":
        return array_template(
            statement=(
                "非負整数 X と Q 個の操作が与えられる。"
                " `1 k` は k bit を立てる、`2 k` は k bit を下ろす、`3 k` は k bit が立っていれば 1、そうでなければ 0 を出力せよ。"
            ),
            input_format="1 行目に X Q。\n続く Q 行に操作。",
            output_format="type=3 のたびに答えを 1 行ずつ出力する。",
            constraints="0 <= X < 2^60\n1 <= Q <= 2 * 10^5\n0 <= k < 60",
            examples=[{"input": "0 5\n1 2\n3 2\n2 2\n3 2\n3 1", "output": "1\n0\n0"}],
            reference_solution=(
                "def solve() -> None:\n"
                "    x, q = map(int, input().split())\n"
                "    out = []\n"
                "    for _ in range(q):\n"
                "        t, k = map(int, input().split())\n"
                "        if t == 1:\n"
                "            x |= 1 << k\n"
                "        elif t == 2:\n"
                "            x &= ~(1 << k)\n"
                "        else:\n"
                "            out.append(str((x >> k) & 1))\n"
                "    print('\\n'.join(out))\n\n"
                "if __name__ == '__main__':\n"
                "    solve()\n"
            ),
        )
    if theme_id == "algo-116":
        return array_template(
            statement="長さ N の整数列 A が与えられる。すべての要素の XOR を求めよ。",
            input_format="1 行目に N。\n2 行目に A1..AN。",
            output_format="XOR を出力する。",
            constraints="1 <= N <= 2 * 10^5\n0 <= Ai < 2^60",
            examples=[{"input": "4\n1 2 3 4", "output": "4"}],
            reference_solution=(
                "def solve() -> None:\n"
                "    input()\n"
                "    ans = 0\n"
                "    for value in map(int, input().split()):\n"
                "        ans ^= value\n"
                "    print(ans)\n\n"
                "if __name__ == '__main__':\n"
                "    solve()\n"
            ),
        )
    if theme_id == "algo-118":
        return array_template(
            statement="集合 A, B が与えられる。bit で表現し、和集合と共通部分の要素数を求めよ。",
            input_format="1 行目に NA NB。\n2 行目に A の要素。\n3 行目に B の要素。",
            output_format="1 行に `union_size intersection_size` を出力する。",
            constraints="0 <= 要素 < 60",
            examples=[{"input": "3 3\n1 3 5\n3 4 5", "output": "4 2"}],
            reference_solution=(
                "def build_mask(values: list[int]) -> int:\n"
                "    mask = 0\n"
                "    for value in values:\n"
                "        mask |= 1 << value\n"
                "    return mask\n\n"
                "def solve() -> None:\n"
                "    na, nb = map(int, input().split())\n"
                "    a = list(map(int, input().split())) if na else []\n"
                "    b = list(map(int, input().split())) if nb else []\n"
                "    ma = build_mask(a)\n"
                "    mb = build_mask(b)\n"
                "    print((ma | mb).bit_count(), (ma & mb).bit_count())\n\n"
                "if __name__ == '__main__':\n"
                "    solve()\n"
            ),
        )
    if theme_id == "algo-119":
        return array_template(
            statement="長さ N の整数列 A が与えられる。全部分集合の和を小さい順に出力せよ。",
            input_format="1 行目に N。\n2 行目に A1..AN。",
            output_format="部分集合和を空白区切りで出力する。",
            constraints="1 <= N <= 20",
            examples=[{"input": "2\n1 3", "output": "0 1 3 4"}],
            reference_solution=(
                "def solve() -> None:\n"
                "    n = int(input())\n"
                "    a = list(map(int, input().split()))\n"
                "    sums = []\n"
                "    for mask in range(1 << n):\n"
                "        total = 0\n"
                "        for i in range(n):\n"
                "            if mask >> i & 1:\n"
                "                total += a[i]\n"
                "        sums.append(total)\n"
                "    sums.sort()\n"
                "    print(*sums)\n\n"
                "if __name__ == '__main__':\n"
                "    solve()\n"
            ),
        )
    if theme_id == "algo-120":
        return array_template(
            statement="整数 X と Q 個の操作が与えられる。`1 k` は `X *= 2^k`、`2 k` は `X //= 2^k` とする。最後の X を出力せよ。",
            input_format="1 行目に X Q。\n続く Q 行に操作。",
            output_format="最終的な X を出力する。",
            constraints="0 <= X < 2^60\n1 <= Q <= 2 * 10^5",
            examples=[{"input": "3 3\n1 2\n2 1\n1 1", "output": "12"}],
            reference_solution=(
                "def solve() -> None:\n"
                "    x, q = map(int, input().split())\n"
                "    for _ in range(q):\n"
                "        t, k = map(int, input().split())\n"
                "        if t == 1:\n"
                "            x <<= k\n"
                "        else:\n"
                "            x >>= k\n"
                "    print(x)\n\n"
                "if __name__ == '__main__':\n"
                "    solve()\n"
            ),
        )
    if theme_id == "algo-121":
        return array_template(
            statement="非負整数 X が与えられる。最下位の立っているビットの値を出力せよ。X=0 のときは 0 を出力する。",
            input_format="1 行目に X。",
            output_format="答えを出力する。",
            constraints="0 <= X < 2^60",
            examples=[{"input": "12", "output": "4"}],
            reference_solution=(
                "def solve() -> None:\n"
                "    x = int(input())\n"
                "    print(x & -x if x else 0)\n\n"
                "if __name__ == '__main__':\n"
                "    solve()\n"
            ),
        )
    if any(token in key for token in ("ビット", "XOR", "ポップカウント")):
        return array_template(
            statement="1 つの非負整数 X が与えられる。2 進表現で立っているビット数を求めよ。",
            input_format="1 行目に X。",
            output_format="ビット数を出力する。",
            constraints="0 <= X < 2^60",
            examples=[{"input": "13", "output": "3"}],
            reference_solution=(
                "def solve() -> None:\n"
                "    x = int(input())\n"
                "    print(x.bit_count())\n\n"
                "if __name__ == '__main__':\n"
                "    solve()\n"
            ),
        )
    return None
