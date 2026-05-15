import { join } from "node:path";
import { HarnessLogger } from "../../infrastructure/logging/logger.ts";
import { LintGuard } from "../../infrastructure/lint/lint-guard.ts";
import { ReviewOrchestrator } from "../review/review-orchestrator.ts";
import type { Boundary } from "../../infrastructure/boundary.ts";
import type { RunnerRegistry } from "../../infrastructure/runners/runner-registry.ts";
import type { ResolvedProfileConfig } from "../../infrastructure/config.ts";
import { resolveReviewCriteriaPaths } from "../../infrastructure/assets/review-assets.ts";
import type { LintAdapter } from "../../shared/tool-adapter.ts";

type RuntimeParams = {
  boundary: Boundary;
  registry: RunnerRegistry;
  profile: ResolvedProfileConfig;
  lintAdapters: LintAdapter[];
  scope: string;
};

export type PageFlowRuntime = {
  root: string;
  logger: HarnessLogger;
  lintGuard: LintGuard;
  reviewOrchestrator: ReviewOrchestrator;
  criteriaPaths: string[];
  scopeTools: string[];
};

export function preparePageFlowRuntime(params: RuntimeParams): PageFlowRuntime {
  const root = params.boundary.getProjectRoot();
  const logger = new HarnessLogger(`page_${params.scope.replace(/\//g, "_")}`, {
    baseDir: join(root, "logs"),
  });
  const lintGuard = new LintGuard(logger, params.lintAdapters, {
    toolRoot: params.profile.toolRoot,
    execOverride: params.profile.exec,
  });
  const reviewOrchestrator = new ReviewOrchestrator(
    logger,
    lintGuard,
    root,
    params.registry,
    params.profile,
  );

  return {
    root,
    logger,
    lintGuard,
    reviewOrchestrator,
    criteriaPaths: resolveReviewCriteriaPaths(root, params.profile, "frontend"),
    scopeTools: params.boundary.scopeAllowedTools(params.scope),
  };
}
