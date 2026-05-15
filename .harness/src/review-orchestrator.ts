import type { HarnessLogger } from "./logger.ts";
import type { LintGuard } from "./lint-guard.ts";
import type { RunnerRegistry } from "./runner-registry.ts";
import type { ResolvedProfileConfig } from "./config.ts";
import type { FlowStep } from "./steps.ts";
import { FLOW_STEP } from "./steps.ts";
import { DriftError, RunnerRateLimitError, ESCALATION_LEVEL, EVENT } from "./types.ts";
import type { ReviewIssue, ReviewResult, ReviewRecord } from "./types.ts";
import { ReviewCycleService } from "./application/review-cycle-service.ts";
import type { PageReviewCycleParams, ReviewCycleParams, ReviewStepDefinition } from "./application/review-cycle-service.ts";
import { ReviewStepExecutor } from "./application/review-step-executor.ts";
import { ReviewPromptFactory } from "./application/review-prompt-factory.ts";
import { parseReviewResult } from "./domain/review-output.ts";

export class ReviewOrchestrator {
  private logger: HarnessLogger;
  private lintGuard: LintGuard;
  private projectRoot: string;
  private registry: RunnerRegistry;
  private stepExecutor: ReviewStepExecutor;
  private prompts: ReviewPromptFactory;
  private cycleService: ReviewCycleService;
  private records: ReviewRecord[] = [];

  constructor(
    logger: HarnessLogger,
    lintGuard: LintGuard,
    projectRoot: string,
    registry: RunnerRegistry,
    profile?: ResolvedProfileConfig,
  ) {
    this.logger = logger;
    this.lintGuard = lintGuard;
    this.projectRoot = projectRoot;
    this.registry = registry;
    this.stepExecutor = new ReviewStepExecutor(logger, projectRoot, registry, profile);
    this.prompts = new ReviewPromptFactory(projectRoot, registry);
    this.cycleService = new ReviewCycleService(
      lintGuard,
      this.prompts,
      (step, prompt, options) => this.executeRun(step, prompt, options),
      projectRoot,
    );
  }

  getRecords(): ReviewRecord[] {
    return [...this.records];
  }

  restoreRecords(records: ReviewRecord[]): void {
    this.records = [...records];
  }

  async runReview(params: ReviewCycleParams): Promise<ReviewResult[]> {
    // テストレビューは records をリセット、実装レビューは追記
    if (params.reviewMode === "test") {
      this.records = [];
    }
    const steps = params.reviewMode === "test"
      ? this.testReviewSteps(params)
      : this.implementationReviewSteps(params);
    const results = await this.cycleService.runSequentialReview(steps, params, this.records);

    if (params.reviewMode === "implementation" && params.designDecisions) {
      for (const decision of params.designDecisions) {
        this.records.push({
          step: "design_decision",
          cycle: 0,
          reviewer: "plan",
          findings: [],
          decision: "accepted",
          diffBefore: "",
          diffAfter: "",
          judgmentSummary: decision,
        });
      }
    }

    return results;
  }

  async runPageReview(params: PageReviewCycleParams): Promise<ReviewResult[]> {
    this.logger.log(EVENT.REVIEW_START, { mode: "page-3-step" });
    return this.cycleService.runCompositeReview(
      "page_review",
      this.pageReviewSteps(params),
      params,
      this.records,
    );
  }

  async runComponentReview(
    targetFiles: string[],
    criteriaPaths: string[],
  ): Promise<ReviewResult> {
    const promptPackage = this.prompts.buildComponentCriteriaReview(targetFiles, criteriaPaths);
    return this.executeReview(
      FLOW_STEP.COMPONENT_SELF_REVIEW,
      promptPackage.prompt,
      "component_self_review",
      { appendSystemPrompt: promptPackage.appendSystemPrompt },
    );
  }

  private testReviewSteps(params: ReviewCycleParams): ReviewStepDefinition[] {
    this.logger.log(EVENT.REVIEW_START, { mode: "test-2-step" });
    const steps: ReviewStepDefinition[] = [
      {
        step: FLOW_STEP.TEST_SELF_QUALITY,
        reviewer: "test_self_quality",
        mode: "test",
        run: () => this.selfReviewTestQuality(params.targetFiles, params.specPath, params.testCasesPath ?? ""),
      },
    ];

    if (!this.registry.isStepSkipped(FLOW_STEP.TEST_EXTERNAL_REVIEW)) {
      steps.push({
        step: FLOW_STEP.TEST_EXTERNAL_REVIEW,
        reviewer: "test_external",
        mode: "test",
        run: async () => {
          try {
            return await this.codexTestReview(params.targetFiles, params.specPath, params.testCasesPath ?? "");
          } catch (error: unknown) {
            if (error instanceof RunnerRateLimitError) {
              this.logger.log(EVENT.RUNNER_RATE_LIMITED, {
                fallback: "none",
                runner: error.runnerName,
                step: FLOW_STEP.TEST_EXTERNAL_REVIEW,
              });
            }
            throw error;
          }
        },
      });
    }

    return steps;
  }

  private implementationReviewSteps(params: ReviewCycleParams): ReviewStepDefinition[] {
    this.logger.log(EVENT.REVIEW_START, {
      mode: this.registry.isStepSkipped(FLOW_STEP.IMPL_EXTERNAL_REVIEW) ? "impl-2-step" : "impl-3-step",
    });
    const steps: ReviewStepDefinition[] = [
      {
        step: FLOW_STEP.IMPL_SELF_CRITERIA,
        reviewer: "self_criteria",
        mode: "implementation",
        run: () => this.selfReviewCriteria(params.targetFiles, params.criteriaPaths),
      },
      {
        step: FLOW_STEP.IMPL_SELF_QUALITY,
        reviewer: "self_quality",
        mode: "implementation",
        run: () => this.selfReviewQuality(params.targetFiles, params.specPath),
      },
    ];

    if (!this.registry.isStepSkipped(FLOW_STEP.IMPL_EXTERNAL_REVIEW)) {
      steps.push({
        step: FLOW_STEP.IMPL_EXTERNAL_REVIEW,
        reviewer: "impl_external",
        mode: "implementation",
        run: async () => {
          try {
            return await this.codexReview(params.targetFiles, params.specPath);
          } catch (error: unknown) {
            if (error instanceof RunnerRateLimitError) {
              this.logger.log(EVENT.RUNNER_RATE_LIMITED, {
                fallback: "none",
                runner: error.runnerName,
                step: FLOW_STEP.IMPL_EXTERNAL_REVIEW,
              });
            }
            throw error;
          }
        },
      });
    }

    return steps;
  }

  private pageReviewSteps(params: PageReviewCycleParams): ReviewStepDefinition[] {
    return [
      {
        step: FLOW_STEP.PAGE_REVIEW_DESIGN,
        reviewer: "page_design",
        mode: "page",
        run: () => this.pageDesignReview(
          params.targetFiles,
          params.specPath,
          params.componentSpecPath,
          params.dependenciesText,
          params.figmaSlice,
        ),
      },
      {
        step: FLOW_STEP.PAGE_REVIEW_BEHAVIOR,
        reviewer: "page_behavior",
        mode: "page",
        run: () => this.pageBehaviorReview(params.targetFiles, params.specPath, params.browserScenariosText),
      },
      {
        step: FLOW_STEP.PAGE_REVIEW_CODE,
        reviewer: "page_code",
        mode: "page",
        run: () => this.pageCodeReview(params.targetFiles, params.criteriaPaths),
      },
    ];
  }

  private async selfReviewTestQuality(
    targetFiles: string[],
    specPath: string,
    testCasesPath: string,
  ): Promise<ReviewResult> {
    const promptPackage = this.prompts.buildTestQualityReview(targetFiles, specPath, testCasesPath);

    this.logger.log(EVENT.SELF_REVIEW, { step: "test_quality" });
    return this.executeReview(FLOW_STEP.TEST_SELF_QUALITY, promptPackage.prompt, "test_self_quality");
  }

  private async selfReviewCriteria(
    targetFiles: string[],
    criteriaPaths: string[],
  ): Promise<ReviewResult> {
    const promptPackage = this.prompts.buildImplementationCriteriaReview(targetFiles, criteriaPaths);

    this.logger.log(EVENT.SELF_REVIEW, { step: "criteria" });
    return this.executeReview(FLOW_STEP.IMPL_SELF_CRITERIA, promptPackage.prompt, "self_criteria", {
      appendSystemPrompt: promptPackage.appendSystemPrompt,
    });
  }

  private async selfReviewQuality(
    targetFiles: string[],
    specPath: string,
  ): Promise<ReviewResult> {
    const promptPackage = this.prompts.buildImplementationQualityReview(targetFiles, specPath);

    this.logger.log(EVENT.SELF_REVIEW, { step: "quality" });
    return this.executeReview(FLOW_STEP.IMPL_SELF_QUALITY, promptPackage.prompt, "self_quality");
  }

  private async codexTestReview(
    targetFiles: string[],
    specPath: string,
    testCasesPath: string,
  ): Promise<ReviewResult> {
    const promptPackage = this.prompts.buildCodexTestReview(targetFiles, specPath, testCasesPath);

    return this.executeReview(FLOW_STEP.TEST_EXTERNAL_REVIEW, promptPackage.prompt, "test_external");
  }

  private async codexReview(
    targetFiles: string[],
    specPath: string,
  ): Promise<ReviewResult> {
    const promptPackage = this.prompts.buildCodexImplementationReview(targetFiles, specPath);

    return this.executeReview(FLOW_STEP.IMPL_EXTERNAL_REVIEW, promptPackage.prompt, "impl_external");
  }

  private async pageDesignReview(
    targetFiles: string[],
    specPath: string,
    componentSpecPath: string,
    dependenciesText: string,
    figmaSlice: string,
  ): Promise<ReviewResult> {
    const promptPackage = this.prompts.buildPageDesignReview(
      targetFiles,
      specPath,
      componentSpecPath,
      dependenciesText,
      figmaSlice,
    );

    return this.executeReview(FLOW_STEP.PAGE_REVIEW_DESIGN, promptPackage.prompt, "page_design");
  }

  private async pageBehaviorReview(
    targetFiles: string[],
    specPath: string,
    browserScenariosText: string,
  ): Promise<ReviewResult> {
    const promptPackage = this.prompts.buildPageBehaviorReview(targetFiles, specPath, browserScenariosText);

    return this.executeReview(FLOW_STEP.PAGE_REVIEW_BEHAVIOR, promptPackage.prompt, "page_behavior");
  }

  private async pageCodeReview(
    targetFiles: string[],
    criteriaPaths: string[],
  ): Promise<ReviewResult> {
    const promptPackage = this.prompts.buildPageCodeReview(targetFiles, criteriaPaths);

    return this.executeReview(
      FLOW_STEP.PAGE_REVIEW_CODE,
      promptPackage.prompt,
      "page_code",
      { appendSystemPrompt: promptPackage.appendSystemPrompt },
    );
  }

  private parseReviewResult(reviewer: string, output: string): ReviewResult {
    return parseReviewResult(reviewer, output);
  }

  private async executeReview(
    step: FlowStep,
    prompt: string,
    reviewer: string,
    options?: {
      allowedTools?: string[];
      appendSystemPrompt?: string;
      timeoutMs?: number;
    },
  ): Promise<ReviewResult> {
    const response = await this.stepExecutor.execute(step, {
      prompt,
      allowedTools: options?.allowedTools ?? ["Read"],
      appendSystemPrompt: options?.appendSystemPrompt,
      timeoutMs: options?.timeoutMs,
    });
    return this.parseReviewResult(reviewer, response.text);
  }

  private async executeRun(
    step: FlowStep,
    prompt: string,
    options?: {
      allowedTools?: string[];
      appendSystemPrompt?: string;
      cwd?: string;
      timeoutMs?: number;
    },
  ): Promise<string> {
    const response = await this.stepExecutor.execute(step, {
      prompt,
      allowedTools: options?.allowedTools,
      appendSystemPrompt: options?.appendSystemPrompt,
      cwd: options?.cwd,
      timeoutMs: options?.timeoutMs,
    });
    return response.text;
  }
}
