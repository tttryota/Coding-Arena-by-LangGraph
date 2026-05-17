import test from "node:test";
import assert from "node:assert/strict";
import { mkdtempSync, mkdirSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { GuardError, HarnessError } from "../../domain/model/types.ts";
import { Boundary } from "../../domain/services/boundary.ts";
import { parseImplGenerationResult, parseTestGenerationResult, ImplFlow } from "./impl-flow.ts";

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

test("impl generation result parsers fail closed on malformed payloads", () => {
  assert.throws(() => parseTestGenerationResult("not-json"), HarnessError);
  assert.throws(
    () => parseTestGenerationResult(JSON.stringify({ decision: "bad", why: [], covered_test_cases: [], updated_test_cases: [], notes: [] })),
    /decision が不正/,
  );
  assert.throws(
    () => parseImplGenerationResult(JSON.stringify({ decision: "noop", why: [1], covered_requirements: [], updated_requirements: [], notes: [] })),
    /why が不正/,
  );
});

test("ImplFlow helper methods resolve criteria, rules, and MSW instructions", () => {
  const root = mkdtempSync(join(tmpdir(), "harness-impl-helpers-"));
  mkdirSync(join(root, ".harness", "rules"), { recursive: true });
  writeFileSync(join(root, ".harness", "review-criteria-common.md"), "# common\n", "utf-8");
  writeFileSync(join(root, ".harness", "review-criteria-backend.md"), "# backend\n", "utf-8");
  writeFileSync(join(root, ".harness", "review-criteria-frontend.md"), "# frontend\n", "utf-8");
  writeFileSync(join(root, ".harness", "rules", "impl.md"), "# impl rules\n", "utf-8");
  writeFileSync(join(root, ".harness", "rules", "logic.md"), "# logic rules\n", "utf-8");

  const profile = {
    reviewCriteria: [],
    criteriaPreset: undefined,
    sourceLayout: {
      sourceDir: "backend/{{category}}",
      testDir: "backend/{{category}}/tests",
      scopePattern: "backend/{{category}}/*",
      additionalAllowedPrefixes: [".harness/reviews/"],
    },
  } as any;
  const boundary = new Boundary(root, profile.sourceLayout, ["ts"], []);
  const flow = new ImplFlow(boundary, {} as never, profile, {} as never, []);

  assert.equal((flow as any).shouldSkip(null, "impl_generate"), false);
  assert.equal((flow as any).shouldSkip("impl_generate", "test_generate"), true);
  assert.deepEqual((flow as any).resolveCriteriaPaths(), [
    join(root, ".harness", "review-criteria-common.md"),
    join(root, ".harness", "review-criteria-backend.md"),
  ]);
  assert.match((flow as any).resolveRulesContent({ type: "impl", profile: "backend" }), /impl rules/);
  assert.match((flow as any).resolveRulesContent({ type: "impl", profile: "frontend" }), /logic rules/);
  assert.equal((flow as any).resolveRuleName({ type: "component", profile: "frontend" }), "component");
  assert.match((flow as any).buildMswInstructions({ msw: true }, "test"), /MSW セットアップ/);
  assert.match((flow as any).buildMswInstructions({ msw: true }, "impl"), /MSW ハンドラ生成/);
  assert.equal((flow as any).buildMswInstructions({ msw: false }, "impl"), "");
});

test("ImplFlow resolveCriteriaPaths rejects missing explicit criteria files", () => {
  const root = mkdtempSync(join(tmpdir(), "harness-impl-criteria-missing-"));
  const profile = {
    reviewCriteria: ["missing.md"],
    criteriaPreset: undefined,
    sourceLayout: {
      sourceDir: "backend/{{category}}",
      testDir: "backend/{{category}}/tests",
      scopePattern: "backend/{{category}}/*",
      additionalAllowedPrefixes: [".harness/reviews/"],
    },
  } as any;
  const boundary = new Boundary(root, profile.sourceLayout, ["ts"], []);
  const flow = new ImplFlow(boundary, {} as never, profile, {} as never, []);

  assert.throws(() => (flow as any).resolveCriteriaPaths(), GuardError);
});
