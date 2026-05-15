import { Boundary } from "../../infrastructure/boundary.ts";
import {
  inferProfile,
  loadConfig,
  resolveProfile,
  type HarnessConfig,
  type ResolvedProfileConfig,
} from "../../infrastructure/config.ts";
import { interactiveRunnerAssignment } from "../../cli/interactive.ts";
import { parsePlan } from "../../shared/plan-parser.ts";
import { createRunnerRegistry, type RunnerRegistry } from "../../infrastructure/runners/runner-registry.ts";
import type { FlowMode, FlowStep } from "../../shared/steps.ts";
import {
  resolveLintAdapter,
  resolveTestAdapter,
  type BaseAdapter,
  type LintAdapter,
  type TestAdapter,
} from "../../shared/tool-adapter.ts";
import type { TaskPlan } from "../../shared/types.ts";

export type PlanFlowEnvironment = {
  projectRoot: string;
  planPath: string;
  config: HarnessConfig;
  plan: TaskPlan;
  profileName: string;
  profile: ResolvedProfileConfig;
  boundary: Boundary;
  registry: RunnerRegistry;
  lintAdapters: LintAdapter[];
  testAdapter: TestAdapter;
};

type PreparePlanFlowEnvironmentParams = {
  projectRoot: string;
  planPath: string;
  flow?: FlowMode;
  profileOverride?: string;
  noInteractive?: boolean;
  resume?: boolean;
};

export async function preparePlanFlowEnvironment(
  params: PreparePlanFlowEnvironmentParams,
): Promise<PlanFlowEnvironment> {
  const config = loadConfig(params.projectRoot);
  if (params.flow) {
    config.flow = params.flow;
  }

  const plan = parsePlan(params.projectRoot, params.planPath);
  const profileName = params.profileOverride ?? plan.profile ?? inferProfile(config);
  const profile = resolveProfile(config, profileName);
  plan.profile = profileName;

  const lintAdapters = profile.lint.map(resolveLintAdapter);
  const testAdapter = resolveTestAdapter(profile.test);
  const boundary = buildBoundary(params.projectRoot, profile, [...lintAdapters, testAdapter]);

  let overrides: Partial<Record<FlowStep, string>> | undefined;
  const interactiveEnabled = !params.noInteractive && !(params.resume ?? false) && process.stdin.isTTY;
  if (interactiveEnabled) {
    overrides = await interactiveRunnerAssignment(config, config.flow, profile) ?? undefined;
  }

  const registry = createRunnerRegistry(config, params.projectRoot, profile, overrides);

  return {
    projectRoot: params.projectRoot,
    planPath: params.planPath,
    config,
    plan,
    profileName,
    profile,
    boundary,
    registry,
    lintAdapters,
    testAdapter,
  };
}

type PrepareDesignFlowEnvironmentParams = {
  projectRoot: string;
  profileName?: string;
};

export function prepareDesignFlowEnvironment(
  params: PrepareDesignFlowEnvironmentParams,
): {
  config: HarnessConfig;
  profile: ResolvedProfileConfig | undefined;
  boundary: Boundary;
  registry: RunnerRegistry;
} {
  const config = loadConfig(params.projectRoot);
  const profile = params.profileName
    ? resolveProfile(config, params.profileName)
    : Object.keys(config.profiles).length === 1
      ? resolveProfile(config, inferProfile(config))
      : undefined;
  const boundary = new Boundary(params.projectRoot);
  const registry = createRunnerRegistry(config, params.projectRoot, profile);
  return { config, profile, boundary, registry };
}

function buildBoundary(
  projectRoot: string,
  profile: ResolvedProfileConfig,
  adapters: BaseAdapter[],
): Boundary {
  const extensions = [...new Set(adapters.flatMap((adapter) => [...adapter.fileExtensions]))];
  const excludeDirs = [...new Set(adapters.flatMap((adapter) => [...adapter.excludeDirs]))];
  return new Boundary(
    projectRoot,
    profile.sourceLayout,
    profile.allowedSideEffectFiles,
    extensions,
    excludeDirs,
  );
}
