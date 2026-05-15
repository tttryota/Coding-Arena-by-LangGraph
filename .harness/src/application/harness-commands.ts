import { join } from "node:path";
import { renderBenchmarkSummary } from "../benchmark-summary.ts";
import { ComponentFlow } from "../component-flow.ts";
import { DesignFlow } from "../design-flow.ts";
import { HarnessLogger } from "../logger.ts";
import { ImplFlow } from "../impl-flow.ts";
import { PageFlow } from "../page-flow.ts";
import type { FlowMode } from "../steps.ts";
import { prepareDesignFlowEnvironment, preparePlanFlowEnvironment } from "./plan-flow-environment.ts";

export async function runImplCommand(params: {
  projectRoot: string;
  planPath: string;
  flow?: FlowMode;
  profileOverride?: string;
  noInteractive?: boolean;
  resume?: boolean;
}): Promise<void> {
  const environment = await preparePlanFlowEnvironment(params);
  const flow = new ImplFlow(
    environment.boundary,
    environment.registry,
    environment.profile,
    environment.testAdapter,
    environment.lintAdapters,
  );
  await flow.run(environment.planPath, {
    resume: params.resume,
    plan: environment.plan,
  });
}

export async function runPageCommand(params: {
  projectRoot: string;
  planPath: string;
  flow?: FlowMode;
  profileOverride?: string;
  noInteractive?: boolean;
}): Promise<void> {
  const environment = await preparePlanFlowEnvironment(params);
  const flow = new PageFlow(
    environment.boundary,
    environment.registry,
    environment.profile,
    environment.testAdapter,
    environment.lintAdapters,
  );
  await flow.run(environment.planPath, { plan: environment.plan });
}

export async function runComponentCommand(params: {
  projectRoot: string;
  planPath: string;
  flow?: FlowMode;
  profileOverride?: string;
  noInteractive?: boolean;
}): Promise<void> {
  const environment = await preparePlanFlowEnvironment(params);
  const flow = new ComponentFlow(
    environment.boundary,
    environment.registry,
    environment.profile,
    environment.testAdapter,
    environment.lintAdapters,
  );
  await flow.run(environment.planPath, { plan: environment.plan });
}

export async function runDesignCommand(params: {
  projectRoot: string;
  featureName: string;
  requirements: string;
  profileName?: string;
}): Promise<void> {
  const environment = prepareDesignFlowEnvironment({
    projectRoot: params.projectRoot,
    profileName: params.profileName,
  });
  const logger = new HarnessLogger(`design_${params.featureName}`, {
    baseDir: join(params.projectRoot, "logs"),
  });
  const flow = new DesignFlow(environment.boundary, environment.registry, environment.profile);
  await flow.run(params.featureName, params.requirements, logger);
}

export function runBenchmarkSummaryCommand(logDirs: string[]): string {
  return renderBenchmarkSummary(logDirs);
}
