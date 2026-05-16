import test from "node:test";
import assert from "node:assert/strict";
import { parseTestGenerationResult } from "./impl-flow.ts";

test("parseTestGenerationResult accepts noop result", () => {
  const result = parseTestGenerationResult(JSON.stringify({
    decision: "noop",
    why: ["covered by existing tests"],
    covered_test_cases: ["case 1", "case 2"],
    updated_test_cases: [],
    notes: [],
  }));

  assert.equal(result.decision, "noop");
  assert.deepEqual(result.coveredTestCases, ["case 1", "case 2"]);
});

test("parseTestGenerationResult accepts updated result", () => {
  const result = parseTestGenerationResult(JSON.stringify({
    decision: "updated",
    why: ["case 3 was missing"],
    covered_test_cases: ["case 1", "case 2", "case 3"],
    updated_test_cases: ["case 3"],
    notes: ["added a direct assertion"],
  }));

  assert.equal(result.decision, "updated");
  assert.deepEqual(result.updatedTestCases, ["case 3"]);
});
