import { readFileSync } from "node:fs";
import { join, resolve } from "node:path";
import { DriftGuard } from "../drift-guard.ts";
import { HarnessLogger } from "../logger.ts";
import { LintGuard } from "../lint-guard.ts";
import { ReviewOrchestrator } from "../review-orchestrator.ts";
import type { Boundary } from "../boundary.ts";
import type { RunnerRegistry } from "../runner-registry.ts";
import { FLOW_STEP } from "../steps.ts";
import { EVENT } from "../types.ts";
import type { CheckpointData, TaskPlan } from "../types.ts";
import type { ResolvedProfileConfig } from "../config.ts";
import type { LintAdapter } from "../tool-adapter.ts";

type RuntimeParams = {
  boundary: Boundary;
  registry: RunnerRegistry;
  profile: ResolvedProfileConfig;
  lintAdapters: LintAdapter[];
  plan: TaskPlan;
  resume?: boolean;
  criteriaPaths: string[];
  generationSystemPrompt: string | undefined;
  targetTestFile: string;
  targetImplementationFile: string;
};

export type ImplFlowRuntime = {
  root: string;
  logger: HarnessLogger;
  lintGuard: LintGuard;
  driftGuard: DriftGuard;
  reviewOrchestrator: ReviewOrchestrator;
  checkpoint: CheckpointData | null;
  sessionId: string;
  scopeTools: string[];
  testPath: string;
  testGenerateTools: string[];
  spec: string;
  criteriaPaths: string[];
  generationSystemPrompt: string | undefined;
  targetTestFile: string;
  targetImplementationFile: string;
};

export function prepareImplFlowRuntime(params: RuntimeParams): ImplFlowRuntime {
  const root = params.boundary.getProjectRoot();
  const logger = new HarnessLogger(`impl_${params.plan.scope.replace(/\//g, "_")}`, {
    baseDir: join(root, "logs"),
    resume: params.resume,
  });
  const lintGuard = new LintGuard(logger, params.lintAdapters, {
    toolRoot: params.profile.toolRoot,
    execOverride: params.profile.exec,
  });
  const driftGuard = new DriftGuard(logger, {
    codexAvailable: hasCodexReviewProvider(params.registry),
  });
  const reviewOrchestrator = new ReviewOrchestrator(
    logger,
    lintGuard,
    root,
    params.registry,
    params.profile,
  );

  const checkpoint = params.resume ? logger.loadCheckpoint() : null;

  const linesPerTestCase = 30;
  const expectedLines = params.plan.targetTestCases.length * linesPerTestCase;
  driftGuard.startTask(params.plan.scope, expectedLines);

  const scopeTools = params.boundary.scopeAllowedTools(params.plan.scope);
  const testPath = params.boundary.testPathForScope(params.plan.scope);
  const testGenerateTools = [
    "Read",
    `Write(${params.targetTestFile})`,
    `Edit(${params.targetTestFile})`,
  ];
  const spec = readFileSync(resolve(root, params.plan.specPath), "utf-8");

  return {
    root,
    logger,
    lintGuard,
    driftGuard,
    reviewOrchestrator,
    checkpoint,
    sessionId: checkpoint?.sessionId ?? "",
    scopeTools,
    testPath,
    testGenerateTools,
    spec,
    criteriaPaths: params.criteriaPaths,
    generationSystemPrompt: params.generationSystemPrompt,
    targetTestFile: params.targetTestFile,
    targetImplementationFile: params.targetImplementationFile,
  };
}

function hasCodexReviewProvider(registry: RunnerRegistry): boolean {
  const reviewSteps: import("../steps.ts").FlowStep[] = [
    FLOW_STEP.TEST_EXTERNAL_REVIEW,
    FLOW_STEP.IMPL_EXTERNAL_REVIEW,
  ];
  const stepMapping = registry.getStepMapping();
  const runnerConfig = registry.getConfig();
  return reviewSteps.some((step) => {
    if (registry.isStepSkipped(step)) return false;
    const runnerName = stepMapping[step];
    if (!runnerName) return false;
    const provider = runnerConfig.providers[runnerName];
    return provider?.type === "codex";
  });
}
