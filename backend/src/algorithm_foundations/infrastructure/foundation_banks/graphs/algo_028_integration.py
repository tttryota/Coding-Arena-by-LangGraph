from __future__ import annotations

from algorithm_foundations.infrastructure.foundation_banks.common import (
    default_rubric,
    problem,
    unit_bank,
)

RUBRIC = default_rubric('integration')

UNIT_BANK = unit_bank(
    unit_id='algo-028-integration',
    title='Union-Find（素集合データ構造） の総合演習',
    unit_kind='integration',
    target_skill='Union-Find（素集合データ構造） の総合演習',
    concept_overview='Union-Find は、要素どうしが同じグループかを管理し、グループをくっつける操作を高速に行う考え方です。連結性をまとめて扱う基本を学びます。 この unit では、既習の Union-Find（素集合データ構造） の基本 と Union-Find（素集合データ構造） を素直に実装する を順に使いながら、1 問を分けて解く流れまで確認します。',
    problem_bank=[
        problem(
            problem_id='algo-028-integration-p1',
            title='Union-Find（素集合データ構造） の総合演習 / 1 ケースをそのまま解く',
            problem_statement='N 個の頂点と Q 個の操作が与えられる。 `1 a b` は a と b を連結し、`2 a b` は同じ連結成分なら Yes そうでなければ No を出力せよ。\n\nこの問題では、前提 unit までで扱った知識だけを順に使えば解ける。',
            input_format='1 行目に N Q。\n続く Q 行に type a b。',
            output_format='type=2 の操作ごとに Yes / No を出力する。',
            constraints='1 <= N, Q <= 2 * 10^5\n使う知識は前提 unit までに限定すること。',
            examples=[
                {
                    'input': '4 5\n1 1 2\n2 1 2\n2 1 3\n1 2 3\n2 1 3',
                    'output': 'Yes\nNo\nYes',
                },
            ],
            canonical_reference_solution="def solve() -> None:\n    import sys\n    input = sys.stdin.readline\n    n, q = map(int, input().split())\n    parent = list(range(n + 1))\n    size = [1] * (n + 1)\n    def find(x: int) -> int:\n        while parent[x] != x:\n            parent[x] = parent[parent[x]]\n            x = parent[x]\n        return x\n    def unite(a: int, b: int) -> None:\n        ra = find(a)\n        rb = find(b)\n        if ra == rb:\n            return\n        if size[ra] < size[rb]:\n            ra, rb = rb, ra\n        parent[rb] = ra\n        size[ra] += size[rb]\n    out = []\n    for _ in range(q):\n        t, a, b = map(int, input().split())\n        if t == 1:\n            unite(a, b)\n        else:\n            out.append('Yes' if find(a) == find(b) else 'No')\n    sys.stdout.write('\\n'.join(out))\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
        problem(
            problem_id='algo-028-integration-p2',
            title='Union-Find（素集合データ構造） の総合演習 / 2 ケースを連続して解く',
            problem_statement='2 ケース分の入力が続けて与えられる。それぞれについて、N 個の頂点と Q 個の操作が与えられる。 `1 a b` は a と b を連結し、`2 a b` は同じ連結成分なら Yes そうでなければ No を出力せよ。\n\nこの問題では、前提 unit までで扱った知識だけを順に使えば解ける。',
            input_format='1 行目に 2。\n続く 2 ケースについて:\n1 行目に N Q。\n続く Q 行に type a b。',
            output_format='各ケースの答えを順に出力する。',
            constraints='1 <= N, Q <= 2 * 10^5\n使う知識は前提 unit までに限定すること。\n2 ケースの合計でも同じ方針で処理すること。',
            examples=[
                {
                    'input': '2\n4 5\n1 1 2\n2 1 2\n2 1 3\n1 2 3\n2 1 3\n4 5\n1 1 2\n2 1 2\n2 1 3\n1 2 3\n2 1 3',
                    'output': 'Yes\nNo\nYes\nYes\nNo\nYes',
                },
            ],
            canonical_reference_solution="import io\nimport sys\nfrom contextlib import redirect_stdout\n\ndef solve_one() -> None:\n    import sys\n    input = sys.stdin.readline\n    n, q = map(int, input().split())\n    parent = list(range(n + 1))\n    size = [1] * (n + 1)\n    def find(x: int) -> int:\n        while parent[x] != x:\n            parent[x] = parent[parent[x]]\n            x = parent[x]\n        return x\n    def unite(a: int, b: int) -> None:\n        ra = find(a)\n        rb = find(b)\n        if ra == rb:\n            return\n        if size[ra] < size[rb]:\n            ra, rb = rb, ra\n        parent[rb] = ra\n        size[ra] += size[rb]\n    out = []\n    for _ in range(q):\n        t, a, b = map(int, input().split())\n        if t == 1:\n            unite(a, b)\n        else:\n            out.append('Yes' if find(a) == find(b) else 'No')\n    sys.stdout.write('\\n'.join(out))\n\ndef solve() -> None:\n    t = 2\n    outputs = []\n    for _ in range(t):\n        buf = io.StringIO()\n        with redirect_stdout(buf):\n            solve_one()\n        outputs.append(buf.getvalue().rstrip('\\n'))\n    sys.stdout.write('\\n'.join(outputs))\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
        problem(
            problem_id='algo-028-integration-p3',
            title='Union-Find（素集合データ構造） の総合演習 / 3 ケースを連続して解く',
            problem_statement='3 ケース分の入力が続けて与えられる。それぞれについて、N 個の頂点と Q 個の操作が与えられる。 `1 a b` は a と b を連結し、`2 a b` は同じ連結成分なら Yes そうでなければ No を出力せよ。\n\nこの問題では、前提 unit までで扱った知識だけを順に使えば解ける。',
            input_format='1 行目に 3。\n続く 3 ケースについて:\n1 行目に N Q。\n続く Q 行に type a b。',
            output_format='各ケースの答えを順に出力する。',
            constraints='1 <= N, Q <= 2 * 10^5\n使う知識は前提 unit までに限定すること。\n3 ケースの合計でも同じ方針で処理すること。',
            examples=[
                {
                    'input': '3\n4 5\n1 1 2\n2 1 2\n2 1 3\n1 2 3\n2 1 3\n4 5\n1 1 2\n2 1 2\n2 1 3\n1 2 3\n2 1 3\n4 5\n1 1 2\n2 1 2\n2 1 3\n1 2 3\n2 1 3',
                    'output': 'Yes\nNo\nYes\nYes\nNo\nYes\nYes\nNo\nYes',
                },
            ],
            canonical_reference_solution="import io\nimport sys\nfrom contextlib import redirect_stdout\n\ndef solve_one() -> None:\n    import sys\n    input = sys.stdin.readline\n    n, q = map(int, input().split())\n    parent = list(range(n + 1))\n    size = [1] * (n + 1)\n    def find(x: int) -> int:\n        while parent[x] != x:\n            parent[x] = parent[parent[x]]\n            x = parent[x]\n        return x\n    def unite(a: int, b: int) -> None:\n        ra = find(a)\n        rb = find(b)\n        if ra == rb:\n            return\n        if size[ra] < size[rb]:\n            ra, rb = rb, ra\n        parent[rb] = ra\n        size[ra] += size[rb]\n    out = []\n    for _ in range(q):\n        t, a, b = map(int, input().split())\n        if t == 1:\n            unite(a, b)\n        else:\n            out.append('Yes' if find(a) == find(b) else 'No')\n    sys.stdout.write('\\n'.join(out))\n\ndef solve() -> None:\n    t = 3\n    outputs = []\n    for _ in range(t):\n        buf = io.StringIO()\n        with redirect_stdout(buf):\n            solve_one()\n        outputs.append(buf.getvalue().rstrip('\\n'))\n    sys.stdout.write('\\n'.join(outputs))\n\nif __name__ == '__main__':\n    solve()\n",
            canonical_language='python',
            grading_rubric=RUBRIC,
        ),
    ],
)
