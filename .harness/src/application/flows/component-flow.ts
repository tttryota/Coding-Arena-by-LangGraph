import { prepareComponentFlowRuntime } from "../runtime/component-flow-runtime.ts";
import { ComponentGenerationService } from "../services/component-generation-service.ts";
import { ComponentTargetService, type TargetOutcome } from "../services/component-target-service.ts";
import { validateComponentPlan } from "../services/task-plan-validation.ts";
import type { Boundary } from "../../infrastructure/boundary.ts";
import type { RunnerRegistry } from "../../infrastructure/runners/runner-registry.ts";
import type { ResolvedProfileConfig } from "../../infrastructure/config.ts";
import type { LintAdapter } from "../../shared/tool-adapter.ts";
import type { TaskPlan } from "../../shared/types.ts";
import { EVENT } from "../../shared/types.ts";
import { parsePlan } from "../../shared/plan-parser.ts";

export class ComponentFlow {
  private boundary: Boundary;
  private registry: RunnerRegistry;
  private profile: ResolvedProfileConfig;
  private lintAdapters: LintAdapter[];
  private generationService: ComponentGenerationService;
  private targetService: ComponentTargetService;

  constructor(
    boundary: Boundary,
    registry: RunnerRegistry,
    profile: ResolvedProfileConfig,
    _testAdapter: import("../../shared/tool-adapter.ts").TestAdapter,
    lintAdapters: LintAdapter[],
  ) {
    this.boundary = boundary;
    this.registry = registry;
    this.profile = profile;
    this.lintAdapters = lintAdapters;
    this.generationService = new ComponentGenerationService(boundary, registry, profile);
    this.targetService = new ComponentTargetService(boundary, registry, profile);
  }

  async run(planPath: string, options?: { plan?: TaskPlan }): Promise<void> {
    const plan = options?.plan ?? parsePlan(this.boundary.getProjectRoot(), planPath);
    validateComponentPlan(this.boundary, this.profile, plan);

    const runtime = prepareComponentFlowRuntime({
      boundary: this.boundary,
      registry: this.registry,
      profile: this.profile,
      lintAdapters: this.lintAdapters,
      scope: plan.scope,
    });
    const outcomes: TargetOutcome[] = [];

    for (const target of plan.targets) {
      console.log(`コンポーネントを処理中: ${target}`);
      runtime.logger.log(EVENT.REVIEW_START, { mode: "component_target", target });
      const beforeSnapshot = await this.targetService.snapshotScopeFiles(plan.scope);

      await this.generationService.generate(plan, target, runtime.scopeTools);
      await this.boundary.stageFiles(plan.scope);
      await this.boundary.verifyChangedFilesWithinScope(plan.scope);

      outcomes.push(await this.targetService.processTarget(
        plan,
        target,
        beforeSnapshot,
        runtime.lintGuard,
        runtime.reviewOrchestrator,
        runtime.criteriaPath,
        runtime.scopeTools,
      ));
    }

    runtime.logger.saveReviewData({ plan, targets: outcomes });
    const unresolvedCount = outcomes.filter((outcome) => !outcome.resolved).length;
    console.log(`未収束 target: ${unresolvedCount}`);
  }
}
