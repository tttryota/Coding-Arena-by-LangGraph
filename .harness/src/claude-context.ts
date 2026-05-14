import { existsSync, readFileSync } from "node:fs";
import { join } from "node:path";
import type { ResolvedConfig, ResolvedProfileConfig } from "./config.ts";
import type { RunnerRequest } from "./runner.ts";
import type { FlowStep } from "./steps.ts";
import { GuardError } from "./types.ts";

export type ClaudeStepContext = {
  agent?: string;
  skillBundles: string[];
  skillNames: string[];
  mcpBundles: string[];
  mcpConfigs: string[];
};

export function applyClaudeStepContext(
  request: RunnerRequest,
  config: ResolvedConfig,
  profile: ResolvedProfileConfig | undefined,
  step: FlowStep,
  projectRoot: string,
): RunnerRequest {
  const context = resolveClaudeStepContext(config, profile, step, projectRoot);
  return {
    ...request,
    agent: context.agent ?? request.agent,
    mcpConfigs: uniqueStrings([...(request.mcpConfigs ?? []), ...context.mcpConfigs]),
    appendSystemPrompt: joinPromptSections([
      context.skillNames.length > 0 ? loadSkillPrompt(projectRoot, context.skillNames) : "",
      request.appendSystemPrompt,
    ]),
  };
}

export function resolveClaudeStepContext(
  config: ResolvedConfig,
  profile: ResolvedProfileConfig | undefined,
  step: FlowStep,
  projectRoot: string,
): ClaudeStepContext {
  const profileClaude = profile?.claude;
  const stepOverride = profileClaude?.stepOverrides[step];
  const skillBundles = uniqueStrings([
    ...(profileClaude?.defaultSkillBundles ?? []),
    ...(stepOverride?.skillBundles ?? []),
  ]);
  const mcpBundles = uniqueStrings([
    ...(profileClaude?.defaultMcpBundles ?? []),
    ...(stepOverride?.mcpBundles ?? []),
  ]);

  return {
    agent: stepOverride?.agent ?? profileClaude?.defaultAgent,
    skillBundles,
    skillNames: expandBundles(skillBundles, config.claude.skillBundles),
    mcpBundles,
    mcpConfigs: expandBundles(mcpBundles, config.claude.mcpBundles),
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
    const skillPath = join(projectRoot, ".claude", "skills", skillName, "SKILL.md");
    if (!existsSync(skillPath)) {
      throw new GuardError(`Claude skill not found: .claude/skills/${skillName}/SKILL.md`);
    }
    const content = readFileSync(skillPath, "utf-8").trim();
    return `## Loaded Skill: ${skillName}\n${content}`;
  });

  return [
    "## Harness-loaded skills",
    "Use the following project-local skills as authoritative task guidance for this step.",
    ...sections,
  ].join("\n\n");
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
