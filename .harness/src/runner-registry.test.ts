import test from "node:test";
import assert from "node:assert/strict";
import { createRunnerRegistry } from "./runner-registry.ts";
import { FLOW_STEP } from "./steps.ts";
import type { HarnessConfig } from "./config.ts";

test("runner registry preserves review API on wrapped runners", () => {
  const config: HarnessConfig = {
    runners: {
      codexReviewer: {
        type: "codex",
        sandbox: "read-only",
      },
    },
    fallbackRunner: "codexReviewer",
    steps: {
      ...Object.fromEntries(
        Object.values(FLOW_STEP).map((step) => [step, "codexReviewer"]),
      ),
    } as HarnessConfig["steps"],
    flow: "full",
    templates: {},
    profiles: {},
    claude: {
      skillBundles: {},
      mcpBundles: {},
    },
  };

  const registry = createRunnerRegistry(config, "/tmp/project");
  const runner = registry.getRunner(FLOW_STEP.IMPL_EXTERNAL_REVIEW);

  assert.equal(typeof runner.review, "function");
});
