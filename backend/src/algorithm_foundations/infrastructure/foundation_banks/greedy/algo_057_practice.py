from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('foundation')

UNIT_BANK = unit_bank(
    unit_id='algo-057-practice',
    title='最小コスト巡回（貪欲近似） を素直に実装する',
    unit_kind='foundation',
    target_skill='最小コスト巡回（貪欲近似） で始点依存を比較する',
    concept_overview='最近傍法は局所的に最も近い頂点を選ぶだけなので、どこから出発するかで結果が変わります。ここでは全頂点を始点に試し、どの開始位置が最も短い巡回を生むかを比較します。',
    problem_bank=[
        problem(
            problem_id='algo-057-practice-p1',
            title='最小コスト巡回（貪欲近似） で始点依存を比較する / 全始点で最近傍法を試して最良を選ぶ',
            problem_statement='N 頂点の完全グラフの距離行列 D が与えられる。各頂点 s を始点として、毎回「まだ訪れていない頂点のうち最も距離が短いもの」へ進み、最後に s へ戻る最近傍法を行う。得られる巡回長が最小になる始点番号と、その巡回長を求めよ。最小値を達成する始点が複数あるなら、番号が最小のものを選べ。距離が同じ候補頂点が複数あるときも、番号が小さい頂点を選べ。',
            input_format='1 行目に N。\n続く N 行に距離行列 D。',
            output_format='始点番号と、その始点で得られる最小巡回長を空白区切りで出力する。',
            constraints='2 <= N <= 300\n0 <= Dij <= 10^9\nDii = 0',
            examples=[{'input': '4\n0 2 9 10\n1 0 6 4\n15 7 0 8\n6 3 12 0', 'output': '2 21'}],
            canonical_reference_solution="def tour_length(start: int, d: list[list[int]]) -> int:\n    n = len(d)\n    used = [False] * n\n    cur = start\n    used[cur] = True\n    total = 0\n    for _ in range(n - 1):\n        nxt = -1\n        best = 10 ** 18\n        for v in range(n):\n            if used[v]:\n                continue\n            if d[cur][v] < best or (d[cur][v] == best and (nxt == -1 or v < nxt)):\n                best = d[cur][v]\n                nxt = v\n        total += best\n        cur = nxt\n        used[cur] = True\n    total += d[cur][start]\n    return total\n\n\ndef solve() -> None:\n    n = int(input())\n    d = [list(map(int, input().split())) for _ in range(n)]\n    best_start = 0\n    best_value = 10 ** 18\n    for start in range(n):\n        value = tour_length(start, d)\n        if value < best_value:\n            best_value = value\n            best_start = start\n    print(best_start + 1, best_value)\n\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
