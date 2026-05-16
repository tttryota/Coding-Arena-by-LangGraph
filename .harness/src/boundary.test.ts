import test from "node:test";
import assert from "node:assert/strict";
import { mkdtempSync, mkdirSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { Boundary } from "./boundary.ts";

test("Boundary finds misplaced test files outside configured testDir", async () => {
  const root = mkdtempSync(join(tmpdir(), "harness-boundary-"));
  mkdirSync(join(root, "backend/benchmark/tests"), { recursive: true });
  writeFileSync(join(root, "backend/benchmark/tests/test_expected.py"), "def test_ok():\n    pass\n");
  writeFileSync(join(root, "backend/benchmark/test_markdown_toc.py"), "def test_wrong_place():\n    pass\n");

  const boundary = new Boundary(
    root,
    {
      sourceDir: "backend/{{category}}",
      testDir: "backend/{{category}}/tests",
      scopePattern: "backend/{{category}}/*",
      additionalAllowedPrefixes: [],
    },
    ["py"],
    ["__pycache__", ".venv"],
  );

  const misplaced = await boundary.findMisplacedTestFiles("benchmark/markdown-toc");
  assert.deepEqual(
    misplaced,
    [join(root, "backend/benchmark/test_markdown_toc.py")],
  );
});
