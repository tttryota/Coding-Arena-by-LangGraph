import { prepareImplFlowRuntime } from "./application/impl-flow-runtime.ts";
import { ImplExecutionService } from "./application/impl-execution-service.ts";
import { ImplGenerationService } from "./application/impl-generation-service.ts";
import { ImplReviewService } from "./application/impl-review-service.ts";
import { ScopedLintService } from "./application/scoped-lint-service.ts";
import { validateImplPlan } from "./application/task-plan-validation.ts";
import { TestExecutor } from "./application/test-executor.ts";
import type { Boundary } from "./boundary.ts";
import type { RunnerRegistry } from "./runner-registry.ts";
import { EVENT } from "./types.ts";
import type { TaskPlan } from "./types.ts";
import type { ResolvedProfileConfig } from "./config.ts";
import { HarnessRun } from "./domain/harness-run.ts";
import { ImplArtifactsPolicy } from "./domain/impl-artifacts.ts";
import { readOptionalRulesContent, resolveReviewCriteriaPaths } from "./domain/review-assets.ts";
import type { LintAdapter, TestAdapter } from "./tool-adapter.ts";
import { parsePlan } from "./plan-parser.ts";
import { joinPromptSections } from "./step-context.ts";

export class ImplFlow {
  private boundary: Boundary;
  private registry: RunnerRegistry;
  private profile: ResolvedProfileConfig;
  private testAdapter: TestAdapter;
  private lintAdapters: LintAdapter[];
  private artifacts: ImplArtifactsPolicy;
  private testExecutor: TestExecutor;
  private lintService: ScopedLintService;
  private reviewService: ImplReviewService;
  private generationService: ImplGenerationService;
  private executionService: ImplExecutionService;

  constructor(
    boundary: Boundary,
    registry: RunnerRegistry,
    profile: ResolvedProfileConfig,
    testAdapter: TestAdapter,
    lintAdapters: LintAdapter[],
  ) {
    this.boundary = boundary;
    this.registry = registry;
    this.profile = profile;
    this.testAdapter = testAdapter;
    this.lintAdapters = lintAdapters;
    this.artifacts = new ImplArtifactsPolicy(testAdapter.name, {
      extractName: (scope) => this.boundary.extractName(scope),
      sourcePathForScope: (scope) => this.boundary.sourcePathForScope(scope),
      testPathForScope: (scope) => this.boundary.testPathForScope(scope),
    });
    this.testExecutor = new TestExecutor(testAdapter, {
      projectRoot: this.boundary.getProjectRoot(),
      toolRoot: this.profile.toolRoot,
      execOverride: this.profile.exec,
    });
    this.lintService = new ScopedLintService(boundary, registry, profile);
    this.reviewService = new ImplReviewService(boundary, this.testExecutor);
    this.generationService = new ImplGenerationService(registry, profile, testAdapter, this.artifacts);
    this.executionService = new ImplExecutionService(
      boundary,
      this.testExecutor,
      this.generationService,
      this.lintService,
      this.reviewService,
    );
  }

  private resolveCriteriaPaths(): string[] {
    return resolveReviewCriteriaPaths(
      this.boundary.getProjectRoot(),
      this.profile,
      "backend",
    );
  }

  private resolveRulesContent(plan: TaskPlan): string {
    return readOptionalRulesContent(
      this.boundary.getProjectRoot(),
      this.artifacts.resolveRuleName(plan),
    );
  }

  async run(planPath: string, options?: { resume?: boolean; plan?: import("./types.ts").TaskPlan }): Promise<void> {
    const plan = options?.plan ?? parsePlan(this.boundary.getProjectRoot(), planPath);
    validateImplPlan(this.boundary, plan);
    const targetTestFile = this.artifacts.suggestedTestFilePath(plan.scope);
    const targetImplementationFile = this.artifacts.suggestedImplementationPath(plan.scope);
    const criteriaPaths = this.resolveCriteriaPaths();
    const rules = this.resolveRulesContent(plan);
    const generationSystemPrompt = joinPromptSections([rules]);
    const runtime = prepareImplFlowRuntime({
      boundary: this.boundary,
      registry: this.registry,
      profile: this.profile,
      lintAdapters: this.lintAdapters,
      plan,
      resume: options?.resume,
      criteriaPaths,
      generationSystemPrompt,
      targetTestFile,
      targetImplementationFile,
    });
    runtime.logger.log(EVENT.GUARD_CHECK, { scope: plan.scope, result: "pass" });
    const runState = HarnessRun.restore(planPath, plan.scope, runtime.checkpoint);
    await this.executionService.execute(plan, runtime, runState);
  }
}
