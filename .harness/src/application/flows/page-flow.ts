import { PageBrowserService } from "../services/page-browser-service.ts";
import { preparePageFlowRuntime } from "../runtime/page-flow-runtime.ts";
import { PageGenerationService } from "../services/page-generation-service.ts";
import { PageReviewService } from "../review/page-review-service.ts";
import { ScopedLintService } from "../services/scoped-lint-service.ts";
import { validatePagePlan } from "../services/task-plan-validation.ts";
import { TestExecutor } from "../services/test-executor.ts";
import type { Boundary } from "../../infrastructure/boundary.ts";
import type { RunnerRegistry } from "../../infrastructure/runners/runner-registry.ts";
import type { TaskPlan } from "../../shared/types.ts";
import { DriftError, HarnessError, ESCALATION_LEVEL } from "../../shared/types.ts";
import type { ResolvedProfileConfig } from "../../infrastructure/config.ts";
import type { LintGuard } from "../../infrastructure/lint/lint-guard.ts";
import type { LintAdapter, TestAdapter } from "../../shared/tool-adapter.ts";
import { parsePlan } from "../../shared/plan-parser.ts";

const MAX_BROWSER_ATTEMPTS = 2;

export class PageFlow {
  private boundary: Boundary;
  private registry: RunnerRegistry;
  private profile: ResolvedProfileConfig;
  private testAdapter: TestAdapter;
  private lintAdapters: LintAdapter[];
  private testExecutor: TestExecutor;
  private lintService: ScopedLintService;
  private generationService: PageGenerationService;
  private browserService: PageBrowserService;
  private reviewService: PageReviewService;

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
    this.testExecutor = new TestExecutor(testAdapter, {
      projectRoot: this.boundary.getProjectRoot(),
      toolRoot: this.profile.toolRoot,
      execOverride: this.profile.exec,
      genericFailureMessage: `${testAdapter.frameworkName} がページフロー中に失敗しました。`,
    });
    this.lintService = new ScopedLintService(boundary, registry, profile);
    this.generationService = new PageGenerationService(boundary, registry, profile);
    this.browserService = new PageBrowserService(boundary, registry, profile);
    this.reviewService = new PageReviewService(boundary, this.testExecutor);
  }

  async run(planPath: string, options?: { plan?: TaskPlan }): Promise<void> {
    const plan = options?.plan ?? parsePlan(this.boundary.getProjectRoot(), planPath);
    validatePagePlan(this.boundary, plan);

    const runtime = preparePageFlowRuntime({
      boundary: this.boundary,
      registry: this.registry,
      profile: this.profile,
      lintAdapters: this.lintAdapters,
      scope: plan.scope,
    });

    console.log("ページ実装を生成中...");
    await this.generationService.generate(plan, runtime.scopeTools);
    await this.boundary.stageFiles(plan.scope);
    await this.runStaticChecks(runtime.lintGuard, plan, runtime.scopeTools);
    await this.boundary.verifyChangedFilesWithinScope(plan.scope);

    await this.reviewService.runImplementationReview(
      runtime.reviewOrchestrator,
      plan,
      runtime.criteriaPaths,
    );
    await this.boundary.verifyChangedFilesWithinScope(plan.scope);

    for (let attempt = 1; attempt <= MAX_BROWSER_ATTEMPTS; attempt++) {
      console.log(`ブラウザ検証中... (試行 ${attempt}/${MAX_BROWSER_ATTEMPTS})`);
      const pageFiles = await this.boundary.findImplementationFiles(plan.scope);
      const browserResult = await this.browserService.runVerification(plan, pageFiles);
      if (browserResult.overall === "pass") {
        console.log("ブラウザ検証に通過しました。人間確認に進めます。");
        return;
      }

      if (attempt >= MAX_BROWSER_ATTEMPTS) {
        throw new DriftError(
          ESCALATION_LEVEL.LEVEL_1,
          "page_browser_verification",
          `Browser Verification が ${MAX_BROWSER_ATTEMPTS} 回の試行でも通過しませんでした。`,
        );
      }

      const browserIssues = this.browserService.issuesFromResult(browserResult);
      console.log("ブラウザ検証で指摘が出たため修正し、レビューに戻ります...");
      await this.browserService.applyFixes(browserIssues, runtime.scopeTools);
      await this.runStaticChecks(runtime.lintGuard, plan, runtime.scopeTools);
      await this.boundary.verifyChangedFilesWithinScope(plan.scope);
      await this.reviewService.runImplementationReview(
        runtime.reviewOrchestrator,
        plan,
        runtime.criteriaPaths,
      );
      await this.boundary.verifyChangedFilesWithinScope(plan.scope);
    }
  }

  private async runStaticChecks(
    lintGuard: LintGuard,
    plan: TaskPlan,
    scopeTools: string[],
  ): Promise<void> {
    console.log("静的チェック実行中...");
    await this.lintService.run(lintGuard, plan.scope, "ページ静的チェック", {
      scopeTools,
      root: this.boundary.getProjectRoot(),
    });

    const testResult = await this.runTests(this.boundary.testPathForScope(plan.scope));
    if (!testResult.passed) {
      throw new HarnessError(`ページテスト失敗: ${testResult.output}`);
    }
  }

  private async runTests(
    testPath: string,
  ): Promise<{ passed: boolean; output: string }> {
    return this.testExecutor.run(testPath, {
      collectionErrorMessage: `${this.testAdapter.frameworkName} がページフロー中に失敗しました (kind: collection-error)。`,
      noTestsMessage: `${this.testAdapter.frameworkName} がページフロー中に失敗しました (kind: no-tests)。`,
      genericFailureMessage: `${this.testAdapter.frameworkName} がページフロー中に失敗しました。`,
    });
  }
}
