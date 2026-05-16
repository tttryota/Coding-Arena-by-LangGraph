import test from "node:test";
import assert from "node:assert/strict";
import { parseImplGenerationResult, parseTestGenerationResult } from "./impl-flow.ts";

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

test("parseImplGenerationResult accepts noop result", () => {
  const result = parseImplGenerationResult(JSON.stringify({
    decision: "noop",
    why: ["existing implementation already satisfies spec and tests"],
    covered_requirements: ["requirement 1", "requirement 2"],
    updated_requirements: [],
    notes: [],
  }));

  assert.equal(result.decision, "noop");
  assert.deepEqual(result.coveredRequirements, ["requirement 1", "requirement 2"]);
});

test("parseImplGenerationResult accepts updated result", () => {
  const result = parseImplGenerationResult(JSON.stringify({
    decision: "updated",
    why: ["implemented missing boundary handling"],
    covered_requirements: ["requirement 1", "requirement 2", "requirement 3"],
    updated_requirements: ["requirement 3"],
    notes: ["kept the existing interface unchanged"],
  }));

  assert.equal(result.decision, "updated");
  assert.deepEqual(result.updatedRequirements, ["requirement 3"]);
});
