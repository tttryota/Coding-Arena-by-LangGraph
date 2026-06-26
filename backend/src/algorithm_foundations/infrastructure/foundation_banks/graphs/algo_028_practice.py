from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('foundation')

UNIT_BANK = unit_bank(
    unit_id='algo-028-practice',
    title='Union-Find（素集合データ構造） を素直に実装する',
    unit_kind='foundation',
    target_skill='Union-Find（素集合データ構造） を素直に実装する',
    concept_overview='Union-Find では、連結かどうかだけでなく各グループの大きさも管理できます。ここでは属する連結成分のサイズを答えます。',
    problem_bank=[
        problem(
            problem_id='algo-028-practice-p1',
            title='Union-Find（素集合データ構造） を素直に実装する / 属する連結成分のサイズを求める',
            problem_statement='N 個の頂点と Q 個の操作が与えられる。`1 a b` は a と b を連結し、`2 x` は頂点 x が属する連結成分のサイズを出力せよ。',
            input_format='1 行目に N Q。\n続く Q 行に操作。',
            output_format='type=2 の操作ごとに答えを 1 行ずつ出力する。',
            constraints='1 <= N, Q <= 2 * 10^5\n1 <= a, b, x <= N',
            examples=[{'input': '5 5\n2 1\n1 1 2\n2 2\n1 2 3\n2 1', 'output': '1\n2\n3'}],
            canonical_reference_solution="def solve() -> None:\n    import sys\n    input = sys.stdin.readline\n    n, q = map(int, input().split())\n    parent = list(range(n + 1))\n    size = [1] * (n + 1)\n\n    def find(x: int) -> int:\n        while parent[x] != x:\n            parent[x] = parent[parent[x]]\n            x = parent[x]\n        return x\n\n    def unite(a: int, b: int) -> None:\n        ra = find(a)\n        rb = find(b)\n        if ra == rb:\n            return\n        if size[ra] < size[rb]:\n            ra, rb = rb, ra\n        parent[rb] = ra\n        size[ra] += size[rb]\n\n    out = []\n    for _ in range(q):\n        parts = list(map(int, input().split()))\n        if parts[0] == 1:\n            _, a, b = parts\n            unite(a, b)\n        else:\n            _, x = parts\n            out.append(str(size[find(x)]))\n    sys.stdout.write('\\n'.join(out))\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
