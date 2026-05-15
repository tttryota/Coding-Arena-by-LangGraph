import { existsSync, readFileSync } from "node:fs";
import { join } from "node:path";
import type { ProfileContextConfig, ResolvedConfig, ResolvedProfileConfig } from "./config.ts";
import type { ExecutionRequest } from "./runner.ts";
import type { FlowStep } from "./steps.ts";
import { GuardError } from "./types.ts";

export type StepContext = {
  contextBundles: string[];
  skillNames: string[];
  mcpBundles: string[];
  mcpConfigs: string[];
  rolePrompt?: string;
};

const STEP_ROLE_PROMPTS: Partial<Record<FlowStep, string>> = {
  spec_generate: "Draft a concise, implementable spec. Capture behavior, constraints, and concrete acceptance criteria without hand-waving.",
  test_case_generate: "Write task-facing test cases that make edge conditions explicit and verifiable.",
  test_generate: "Generate tests first. Encode only the approved test cases faithfully, avoid speculative coverage, and keep the output lint-safe.",
  test_self_quality: "Review generated tests for gaps, ambiguity, and weak assertions. Strengthen coverage without changing scope.",
  test_external_review: "Review the tests as an external reviewer. Focus on missing cases, false positives, and spec mismatch.",
  impl_generate: "Implement only what is required to satisfy the approved tests and spec. Prefer straightforward, maintainable, lint-safe code over cleverness.",
  impl_self_criteria: "Review the implementation against hard requirements and clear failure modes. Flag only concrete contract violations.",
  impl_self_quality: "Review the implementation for maintainability, regression risk, edge handling, and test adequacy.",
  impl_external_review: "Review the implementation as an external reviewer. Focus on correctness, boundary conditions, and non-obvious regressions.",
  lint_fix: "Fix only the reported lint or type issues without broad refactors.",
  apply_fixes: "Apply the requested review fixes exactly, keep the scope tight, and leave the touched files lint-safe.",
  judgment_summary: "Summarize review findings and fix outcomes precisely for a human reader.",
  judge_minor: "Judge whether the remaining minor findings are safe to accept. Be conservative and evidence-based.",
  component_generate: "Implement the requested component and story files with the agreed scope only.",
  component_self_review: "Review the component implementation for design fidelity, API clarity, and test or story adequacy.",
  page_generate: "Implement the requested page behavior and structure with strict scope control.",
  page_review_design: "Review the page for design fidelity and visual contract mismatches.",
  page_review_behavior: "Review the page for user-facing behavior and browser flow correctness.",
  page_review_code: "Review the page implementation for maintainability and regression risk.",
  page_browser_verify: "Verify the page in the browser against the documented scenarios and expected outcomes.",
};

const SCOPE_DISCIPLINE_PROMPT = `## Scope Discipline
- Treat the approved spec, test cases, and explicit scope-out sections as authoritative and closed.
- Do not import broader framework, language, or standards behavior unless the spec or approved test cases require it.
- Do not propose feature expansion just because a more complete or more general implementation is possible.
- For benchmark tasks, exact fidelity to the written contract beats generic best-practice completeness.`;

export function applyStepContext(
  request: ExecutionRequest,
  config: ResolvedConfig,
  profile: ResolvedProfileConfig | undefined,
  step: FlowStep,
  projectRoot: string,
  _providerName?: string,
): ExecutionRequest {
  const context = resolveStepContext(config, profile, step);
  const mcpConfigs = uniqueStrings([...(request.mcpConfigs ?? []), ...context.mcpConfigs]);
  const appendSystemPrompt = joinPromptSections([
    SCOPE_DISCIPLINE_PROMPT,
    context.rolePrompt ? `## Step Role\n${context.rolePrompt}` : "",
    context.skillNames.length > 0 ? loadSkillPrompt(projectRoot, context.skillNames) : "",
    request.appendSystemPrompt,
  ]);
  return {
    ...request,
    mcpConfigs: mcpConfigs.length > 0 ? mcpConfigs : undefined,
    appendSystemPrompt,
  };
}

export function resolveStepContext(
  config: ResolvedConfig,
  profile: ResolvedProfileConfig | undefined,
  step: FlowStep,
): StepContext {
  const profileContext = profile?.context;
  const stepOverride = profileContext?.stepOverrides[step];
  const contextBundles = uniqueStrings([
    ...(profileContext?.defaultContextBundles ?? []),
    ...(stepOverride?.contextBundles ?? []),
  ]);
  const mcpBundles = uniqueStrings([
    ...(profileContext?.defaultMcpBundles ?? []),
    ...(stepOverride?.mcpBundles ?? []),
  ]);

  return {
    contextBundles,
    skillNames: expandBundles(contextBundles, config.context.contextBundles),
    mcpBundles,
    mcpConfigs: expandBundles(mcpBundles, config.context.mcpBundles),
    rolePrompt: STEP_ROLE_PROMPTS[step],
  };
}

export function joinPromptSections(sections: Array<string | undefined>): string | undefined {
  const normalized = sections
    .map((section) => section?.trim())
    .filter((section): section is string => Boolean(section));
  if (normalized.length === 0) return undefined;
  return normalized.join("\n\n");
}

function loadSkillPrompt(projectRoot: string, skillNames: string[]): string {
  const sections = skillNames.map((skillName) => {
    const skillPath = resolveSkillPath(projectRoot, skillName);
    const content = readFileSync(skillPath, "utf-8").trim();
    return `## Loaded Skill: ${skillName}\n${content}`;
  });

  return [
    "## Harness-loaded skills",
    "Use the following project-local skills as authoritative task guidance for this step.",
    ...sections,
  ].join("\n\n");
}

function resolveSkillPath(projectRoot: string, skillName: string): string {
  const candidates = [
    join(projectRoot, ".codex", "skills", skillName, "SKILL.md"),
    join(projectRoot, ".claude", "skills", skillName, "SKILL.md"),
    join(projectRoot, ".github", "skills", skillName, "SKILL.md"),
    join(projectRoot, ".agents", "skills", skillName, "SKILL.md"),
  ];

  for (const skillPath of candidates) {
    if (existsSync(skillPath)) {
      return skillPath;
    }
  }

  throw new GuardError(
    `Skill not found: ${skillName}. Checked .codex/skills, .claude/skills, .github/skills, .agents/skills.`,
  );
}

function expandBundles(
  bundleNames: string[],
  bundleMap: Record<string, string[]>,
): string[] {
  const values: string[] = [];
  for (const bundleName of bundleNames) {
    const entries = bundleMap[bundleName];
    if (!entries) continue;
    values.push(...entries);
  }
  return uniqueStrings(values);
}

function uniqueStrings(values: string[]): string[] {
  const seen = new Set<string>();
  const result: string[] = [];
  for (const value of values) {
    if (seen.has(value)) continue;
    seen.add(value);
    result.push(value);
  }
  return result;
}
