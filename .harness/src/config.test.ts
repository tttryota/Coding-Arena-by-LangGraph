import test from "node:test";
import assert from "node:assert/strict";
import { mkdtempSync, mkdirSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { loadConfig } from "./config.ts";
import { GuardError } from "./types.ts";

function writeConfig(workspace: string, body: string): void {
  mkdirSync(join(workspace, ".harness"), { recursive: true });
  writeFileSync(join(workspace, ".harness", "harness.yml"), body, "utf-8");
}

function baseYaml(): string {
  return `profiles:
  backend:
    flow: full
    fallbackRunner: codex
    steps:
      test_generate: codex
      test_self_quality: codex
      test_external_review: claude
      impl_generate: codex
      impl_self_criteria: codex
      impl_self_quality: codex
      impl_external_review: claude
      lint_fix: codex
      apply_fixes: codex
      judgment_summary: codex
      judge_minor: codex
      spec_generate: codex
      test_case_generate: codex
      component_generate: codex
      component_self_review: codex
      page_generate: codex
      page_review_design: codex
      page_review_behavior: codex
      page_review_code: codex
      page_browser_verify: codex
    lint: [ruff, mypy]
    test: pytest
    toolRoot: backend
    criteriaPreset: backend
    context:
      defaultSkills: [backend-review]
      stepOverrides:
        impl_external_review:
          agent: harness-backend-reviewer
          skills: [backend-review-quality]
runners:
  claude:
    type: claude
  codex:
    type: codex
    sandbox: workspace-write
`;
}

test("loadConfig resolves profile-centric runner mapping and context", () => {
  const workspace = mkdtempSync(join(tmpdir(), "harness-config-"));
  writeConfig(workspace, baseYaml());

  const config = loadConfig(workspace);

  assert.deepEqual(Object.keys(config.profiles), ["backend"]);
  assert.equal(config.profiles.backend.flow, "full");
  assert.equal(config.profiles.backend.fallbackRunner, "codex");
  assert.equal(config.profiles.backend.steps.impl_external_review, "claude");
  assert.deepEqual(config.profiles.backend.context?.defaultSkills, ["backend-review"]);
  assert.deepEqual(
    config.profiles.backend.context?.stepOverrides.impl_external_review?.skills,
    ["backend-review-quality"],
  );
});

test("loadConfig rejects missing profile step assignments", () => {
  const workspace = mkdtempSync(join(tmpdir(), "harness-config-missing-step-"));
  writeConfig(
    workspace,
    baseYaml().replace("      page_review_code: codex\n", ""),
  );

  assert.throws(
    () => loadConfig(workspace),
    (error: unknown) =>
      error instanceof GuardError &&
      error.message.includes("profile \"backend\".steps に不足している step"),
  );
});

test("loadConfig rejects legacy top-level runner fields", () => {
  const workspace = mkdtempSync(join(tmpdir(), "harness-config-legacy-top-"));
  writeConfig(
    workspace,
    `${baseYaml()}flow: full\n`,
  );

  assert.throws(
    () => loadConfig(workspace),
    (error: unknown) =>
      error instanceof GuardError &&
      error.message.includes("flow はトップレベルでは使えません"),
  );
});

test("loadConfig rejects legacy profile.claude config", () => {
  const workspace = mkdtempSync(join(tmpdir(), "harness-config-legacy-profile-"));
  writeConfig(
    workspace,
    `profiles:
  backend:
    flow: full
    fallbackRunner: claude
    steps:
      test_generate: claude
      test_self_quality: claude
      test_external_review: claude
      impl_generate: claude
      impl_self_criteria: claude
      impl_self_quality: claude
      impl_external_review: claude
      lint_fix: claude
      apply_fixes: claude
      judgment_summary: claude
      judge_minor: claude
      spec_generate: claude
      test_case_generate: claude
      component_generate: claude
      component_self_review: claude
      page_generate: claude
      page_review_design: claude
      page_review_behavior: claude
      page_review_code: claude
      page_browser_verify: claude
    claude:
      defaultAgent: old
runners:
  claude:
    type: claude
`,
  );

  assert.throws(
    () => loadConfig(workspace),
    (error: unknown) =>
      error instanceof GuardError &&
      error.message.includes("profile \"backend\".claude は廃止されました"),
  );
});
