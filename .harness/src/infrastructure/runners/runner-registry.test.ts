import test from "node:test";
import assert from "node:assert/strict";
import { createRunnerRegistry } from "./runner-registry.ts";
import { FLOW_STEP } from "../../domain/model/steps.ts";
import type { HarnessConfig, ResolvedProfileConfig } from "../config/config.ts";

test("runner registry preserves review API on wrapped runners", () => {
  const steps = Object.fromEntries(
    Object.values(FLOW_STEP).map((step) => [step, "codexReviewer"]),
  ) as Record<(typeof FLOW_STEP)[keyof typeof FLOW_STEP], string>;
  const config: HarnessConfig = {
    runners: {
      codexReviewer: {
        type: "codex",
        sandbox: "read-only",
      },
    },
    templates: {},
    profiles: {},
  };
  const profile: ResolvedProfileConfig = {
    flow: "full",
    steps,
    fallbackRunner: "codexReviewer",
    lint: ["ruff", "mypy"],
    test: "pytest",
    sourceLayout: {
      sourceDir: "backend/{{category}}",
      testDir: "backend/{{category}}/tests",
      scopePattern: "backend/{{category}}/*",
      additionalAllowedPrefixes: [".harness/reviews/"],
    },
    exec: [],
    toolRoot: "/tmp/project",
    reviewCriteria: [],
    criteriaPreset: "backend",
  };

  const registry = createRunnerRegistry(config, "/tmp/project", profile);
  const runner = registry.getRunner(FLOW_STEP.IMPL_EXTERNAL_REVIEW);

  assert.equal(typeof runner.review, "function");
});
