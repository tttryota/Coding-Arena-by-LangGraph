#!/usr/bin/env node
import { readFileSync } from "node:fs";
import { join } from "node:path";
import { pathToFileURL } from "node:url";
import { HarnessLogger, DEFAULT_LOG_BASE_DIR } from "../infrastructure/logging/logger.ts";
import { HarnessError } from "../domain/model/types.ts";
import { Boundary } from "../domain/services/boundary.ts";
import { DesignFlow } from "../application/flows/design-flow.ts";
import { ComponentFlow } from "../application/flows/component-flow.ts";
import { ImplFlow } from "../application/flows/impl-flow.ts";
import { PageFlow } from "../application/flows/page-flow.ts";
import { loadConfig, inferProfile, resolveProfile } from "../infrastructure/config/config.ts";
import { createRunnerRegistry } from "../infrastructure/runners/runner-registry.ts";
import { interactiveRunnerAssignment } from "./interactive.ts";
import { parsePlan } from "../domain/services/plan-parser.ts";
import { resolveLintAdapter, resolveTestAdapter } from "../infrastructure/tooling/tool-adapter.ts";
import type {
  BaseAdapter,
  LintAdapter,
  TestAdapter,
} from "../infrastructure/tooling/tool-adapter.ts";
import type { FlowMode, FlowStep } from "../domain/model/steps.ts";
import { renderBenchmarkSummary } from "../application/diagnostics/benchmark-summary.ts";
import { renderBenchmarkDiagnose } from "../application/diagnostics/benchmark-diagnose.ts";
import type { HarnessConfig, ResolvedProfileConfig } from "../infrastructure/config/config.ts";
import type { RunnerRegistry } from "../infrastructure/runners/runner-registry.ts";
import type { TaskPlan } from "../domain/model/types.ts";

export const LOCAL_CLI_NAME = "./.harness/harness";

export type CliRuntime = {
  cwd: () => string;
  isTTY: boolean;
  readGuide: (path: string) => string;
  writeStdout: (line: string) => void;
  writeStderr: (line: string) => void;
};

type FlowResources = {
  boundary: Boundary;
  registry: RunnerRegistry;
  profile: ResolvedProfileConfig;
  lintAdapters: LintAdapter[];
  testAdapter: TestAdapter;
  effectiveFlow: FlowMode;
  overrides?: Partial<Record<FlowStep, string>>;
};

export type CliDeps = {
  loadConfig: typeof loadConfig;
  inferProfile: typeof inferProfile;
  resolveProfile: typeof resolveProfile;
  parsePlan: typeof parsePlan;
  resolveLintAdapter: typeof resolveLintAdapter;
  resolveTestAdapter: typeof resolveTestAdapter;
  createRunnerRegistry: typeof createRunnerRegistry;
  interactiveRunnerAssignment: typeof interactiveRunnerAssignment;
  createBoundary: (projectRoot: string, profile: ResolvedProfileConfig, adapters: BaseAdapter[]) => Boundary;
  createImplFlow: (
    boundary: Boundary,
    registry: RunnerRegistry,
    profile: ResolvedProfileConfig,
    testAdapter: TestAdapter,
    lintAdapters: LintAdapter[],
  ) => ImplFlow;
  createPageFlow: (
    boundary: Boundary,
    registry: RunnerRegistry,
    profile: ResolvedProfileConfig,
    testAdapter: TestAdapter,
    lintAdapters: LintAdapter[],
  ) => PageFlow;
  createComponentFlow: (
    boundary: Boundary,
    registry: RunnerRegistry,
    profile: ResolvedProfileConfig,
    testAdapter: TestAdapter,
    lintAdapters: LintAdapter[],
  ) => ComponentFlow;
  createDesignFlow: (
    boundary: Boundary,
    registry: RunnerRegistry,
    profile?: ResolvedProfileConfig,
  ) => DesignFlow;
  createLogger: (featureName: string, projectRoot: string) => HarnessLogger;
  renderBenchmarkSummary: typeof renderBenchmarkSummary;
  renderBenchmarkDiagnose: typeof renderBenchmarkDiagnose;
};

const defaultRuntime: CliRuntime = {
  cwd: () => process.cwd(),
  isTTY: Boolean(process.stdin.isTTY),
  readGuide: (path) => readFileSync(path, "utf-8"),
  writeStdout: (line) => console.log(line),
  writeStderr: (line) => console.error(line),
};

const defaultDeps: CliDeps = {
  loadConfig,
  inferProfile,
  resolveProfile,
  parsePlan,
  resolveLintAdapter,
  resolveTestAdapter,
  createRunnerRegistry,
  interactiveRunnerAssignment,
  createBoundary(projectRoot, profile, adapters) {
    const extensions = [...new Set(adapters.flatMap((adapter) => [...adapter.fileExtensions]))];
    const excludeDirs = [...new Set(adapters.flatMap((adapter) => [...adapter.excludeDirs]))];
    return new Boundary(projectRoot, profile.sourceLayout, extensions, excludeDirs);
  },
  createImplFlow: (boundary, registry, profile, testAdapter, lintAdapters) =>
    new ImplFlow(boundary, registry, profile, testAdapter, lintAdapters),
  createPageFlow: (boundary, registry, profile, testAdapter, lintAdapters) =>
    new PageFlow(boundary, registry, profile, testAdapter, lintAdapters),
  createComponentFlow: (boundary, registry, profile, testAdapter, lintAdapters) =>
    new ComponentFlow(boundary, registry, profile, testAdapter, lintAdapters),
  createDesignFlow: (boundary, registry, profile) => new DesignFlow(boundary, registry, profile),
  createLogger: (featureName, projectRoot) =>
    new HarnessLogger(`design_${featureName}`, { baseDir: join(projectRoot, DEFAULT_LOG_BASE_DIR) }),
  renderBenchmarkSummary,
  renderBenchmarkDiagnose,
};

export function usageLines(cliName = LOCAL_CLI_NAME): string[] {
  return [
    "Usage:",
    `  ${cliName} impl <plan-file> [--resume] [--flow full|light] [--no-interactive]`,
    `  ${cliName} component <plan-file> [--flow full|light] [--no-interactive]`,
    `  ${cliName} page <plan-file> [--flow full|light] [--no-interactive]`,
    `  ${cliName} design <feature-name> "<requirements>" [--profile <name>]`,
    `  ${cliName} benchmark-summary <log-dir> [<log-dir>]`,
    `  ${cliName} benchmark-diagnose <log-dir> [<log-dir>]`,
    `  ${cliName} init`,
  ];
}

function writeLines(runtime: CliRuntime, lines: string[], target: "stdout" | "stderr" = "stdout"): void {
  const writer = target === "stdout" ? runtime.writeStdout : runtime.writeStderr;
  for (const line of lines) {
    writer(line);
  }
}

function requireValue(value: string | undefined, message: string): string {
  if (!value) {
    throw new HarnessError(message);
  }
  return value;
}

function parseFlowArg(args: string[]): FlowMode | undefined {
  const flowFlagIndex = args.indexOf("--flow");
  return flowFlagIndex !== -1 ? args[flowFlagIndex + 1] as FlowMode | undefined : undefined;
}

async function resolveFlowResources(
  projectRoot: string,
  config: HarnessConfig,
  planPath: string,
  args: string[],
  runtime: CliRuntime,
  deps: CliDeps,
  options?: { resume?: boolean },
): Promise<FlowResources & { plan: TaskPlan }> {
  const plan = deps.parsePlan(projectRoot, planPath);
  const profileName = plan.profile ?? deps.inferProfile(config);
  const profile = deps.resolveProfile(config, profileName);
  const effectiveFlow = parseFlowArg(args) ?? profile.flow;
  const lintAdapters = profile.lint.map(deps.resolveLintAdapter);
  const testAdapter = deps.resolveTestAdapter(profile.test);
  const allAdapters: BaseAdapter[] = [...lintAdapters, testAdapter];
  const boundary = deps.createBoundary(projectRoot, profile, allAdapters);

  let overrides: Partial<Record<FlowStep, string>> | undefined;
  const noInteractive = args.includes("--no-interactive");
  if (!noInteractive && !options?.resume && runtime.isTTY) {
    overrides = await deps.interactiveRunnerAssignment(
      Object.keys(config.runners),
      profile.steps,
      effectiveFlow,
    ) ?? undefined;
  }

  const registry = deps.createRunnerRegistry(
    config,
    projectRoot,
    profile,
    overrides,
    effectiveFlow,
  );

  return { plan, boundary, registry, profile, lintAdapters, testAdapter, effectiveFlow, overrides };
}

async function runImplCommand(
  projectRoot: string,
  config: HarnessConfig,
  args: string[],
  runtime: CliRuntime,
  deps: CliDeps,
): Promise<number> {
  const planPath = requireValue(args[1], "Error: plan file path required");
  const resume = args.includes("--resume");
  const resources = await resolveFlowResources(projectRoot, config, planPath, args, runtime, deps, { resume });
  const implFlow = deps.createImplFlow(
    resources.boundary,
    resources.registry,
    resources.profile,
    resources.testAdapter,
    resources.lintAdapters,
  );
  await implFlow.run(planPath, { resume, plan: resources.plan });
  return 0;
}

async function runPageCommand(
  projectRoot: string,
  config: HarnessConfig,
  args: string[],
  runtime: CliRuntime,
  deps: CliDeps,
): Promise<number> {
  const planPath = requireValue(args[1], "Error: plan file path required");
  const resources = await resolveFlowResources(projectRoot, config, planPath, args, runtime, deps);
  const pageFlow = deps.createPageFlow(
    resources.boundary,
    resources.registry,
    resources.profile,
    resources.testAdapter,
    resources.lintAdapters,
  );
  await pageFlow.run(planPath, { plan: resources.plan });
  return 0;
}

async function runComponentCommand(
  projectRoot: string,
  config: HarnessConfig,
  args: string[],
  runtime: CliRuntime,
  deps: CliDeps,
): Promise<number> {
  const planPath = requireValue(args[1], "Error: plan file path required");
  const resources = await resolveFlowResources(projectRoot, config, planPath, args, runtime, deps);
  const componentFlow = deps.createComponentFlow(
    resources.boundary,
    resources.registry,
    resources.profile,
    resources.testAdapter,
    resources.lintAdapters,
  );
  await componentFlow.run(planPath, { plan: resources.plan });
  return 0;
}

async function runDesignCommand(
  projectRoot: string,
  config: HarnessConfig,
  args: string[],
  deps: CliDeps,
): Promise<number> {
  const featureName = requireValue(args[1], "Error: feature name and requirements required");
  const requirements = requireValue(args[2], "Error: feature name and requirements required");
  const profileFlagIndex = args.indexOf("--profile");
  const profileName = profileFlagIndex !== -1 ? args[profileFlagIndex + 1] : undefined;
  const boundary = new Boundary(projectRoot);
  const profile = deps.resolveProfile(config, profileName ?? deps.inferProfile(config));
  const registry = deps.createRunnerRegistry(config, projectRoot, profile);
  const logger = deps.createLogger(featureName, projectRoot);
  const flow = deps.createDesignFlow(boundary, registry, profile);
  await flow.run(featureName, requirements, logger);
  return 0;
}

function runBenchmarkSummaryCommand(args: string[], runtime: CliRuntime, deps: CliDeps): number {
  const logDirs = args.slice(1);
  if (logDirs.length === 0 || logDirs.length > 2) {
    throw new HarnessError("Error: benchmark-summary requires one or two log directories");
  }
  runtime.writeStdout(deps.renderBenchmarkSummary(logDirs));
  return 0;
}

function runBenchmarkDiagnoseCommand(
  projectRoot: string,
  args: string[],
  runtime: CliRuntime,
  deps: CliDeps,
): number {
  const logDirs = args.slice(1);
  if (logDirs.length === 0 || logDirs.length > 2) {
    throw new HarnessError("Error: benchmark-diagnose requires one or two log directories");
  }
  runtime.writeStdout(deps.renderBenchmarkDiagnose(logDirs, projectRoot));
  return 0;
}

function runInitCommand(runtime: CliRuntime): number {
  const guidePath = join(import.meta.dirname ?? "", "..", "..", "setup-guide.md");
  try {
    runtime.writeStdout(runtime.readGuide(guidePath));
    return 0;
  } catch {
    throw new HarnessError("setup-guide.md が見つかりません。ハーネスが正しく配置されていることを確認してください。");
  }
}

export async function runCli(
  args: string[],
  runtime: CliRuntime = defaultRuntime,
  deps: CliDeps = defaultDeps,
): Promise<number> {
  const command = args[0];
  if (!command) {
    writeLines(runtime, usageLines());
    return 1;
  }

  if (command === "init") {
    return runInitCommand(runtime);
  }

  const projectRoot = runtime.cwd();
  const config = deps.loadConfig(projectRoot);

  switch (command) {
    case "impl":
      return runImplCommand(projectRoot, config, args, runtime, deps);
    case "page":
      return runPageCommand(projectRoot, config, args, runtime, deps);
    case "component":
      return runComponentCommand(projectRoot, config, args, runtime, deps);
    case "design":
      return runDesignCommand(projectRoot, config, args, deps);
    case "benchmark-summary":
      return runBenchmarkSummaryCommand(args, runtime, deps);
    case "benchmark-diagnose":
      return runBenchmarkDiagnoseCommand(projectRoot, args, runtime, deps);
    default:
      throw new HarnessError(`Unknown command: ${command}`);
  }
}

export async function main(
  args = process.argv.slice(2),
  runtime: CliRuntime = defaultRuntime,
  deps: CliDeps = defaultDeps,
): Promise<number> {
  try {
    return await runCli(args, runtime, deps);
  } catch (error: unknown) {
    if (error instanceof HarnessError) {
      runtime.writeStderr(`[${error.name}] ${error.message}`);
    } else {
      runtime.writeStderr(`Unexpected error: ${String(error)}`);
    }
    return 1;
  }
}

const isMainModule = process.argv[1]
  ? import.meta.url === pathToFileURL(process.argv[1]).href
  : false;

if (isMainModule) {
  const exitCode = await main();
  process.exit(exitCode);
}
