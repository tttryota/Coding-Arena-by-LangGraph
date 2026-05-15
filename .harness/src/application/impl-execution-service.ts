import { existsSync, readFileSync } from "node:fs";
import { resolve } from "node:path";
import type { Boundary } from "../boundary.ts";
import type { TaskPlan } from "../types.ts";
import { GuardError, ESCALATION_LEVEL, EVENT } from "../types.ts";
import type { ImplFlowRuntime } from "./impl-flow-runtime.ts";
import type { ImplGenerationService } from "./impl-generation-service.ts";
import type { ImplReviewService } from "./impl-review-service.ts";
import type { ScopedLintService } from "./scoped-lint-service.ts";
import type { TestExecutor } from "./test-executor.ts";
import { writeImplReport } from "./impl-report-writer.ts";
import { HarnessRun } from "../domain/harness-run.ts";
import { shouldSkipStep } from "../domain/step-transition-policy.ts";
import { type ArtifactValidationFacts, validateArtifactFacts } from "../domain/artifact-validation-policy.ts";

const MAX_GREEN_RETRIES = 3;

export class ImplExecutionService {
  private boundary: Boundary;
  private testExecutor: TestExecutor;
  private generationService: ImplGenerationService;
  private lintService: ScopedLintService;
  private reviewService: ImplReviewService;

  constructor(
    boundary: Boundary,
    testExecutor: TestExecutor,
    generationService: ImplGenerationService,
    lintService: ScopedLintService,
    reviewService: ImplReviewService,
  ) {
    this.boundary = boundary;
    this.testExecutor = testExecutor;
    this.generationService = generationService;
    this.lintService = lintService;
    this.reviewService = reviewService;
  }

  async execute(
    plan: TaskPlan,
    runtime: ImplFlowRuntime,
    runState: HarnessRun,
  ): Promise<void> {
    if (runState.getCompletedStep()) {
      console.log(`チェックポイントから再開: ${runState.getCompletedStep()} 以降を実行`);
    }

    runtime.logger.log(EVENT.TDD_START, { testCases: plan.targetTestCases });
    runtime.reviewOrchestrator.restoreRecords(runState.getReviewRecords());

    const precheck = await this.runTests(runtime.testPath, { allowCollectionError: true });
    if (precheck.passed) {
      this.logAlreadyGreen(plan, runtime, precheck.output);
    }

    if (!shouldSkipStep(runState.getCompletedStep(), "test_generated")) {
      console.log("テストコードを生成中...");
      runState.setSessionId(await this.generationService.generateTests(plan, runtime));
      await this.boundary.stageFiles(plan.scope);
      const postGenerateStatus = await this.validateGeneratedArtifacts(plan, runtime);
      let postGenerateLintPassed = false;
      try {
        await this.lintService.run(runtime.lintGuard, plan.scope, "テスト生成後", {
          scopeTools: runtime.testGenerateTools,
          root: runtime.root,
        });
        postGenerateLintPassed = true;
      } finally {
        runtime.logger.log(EVENT.BENCHMARK_ARTIFACT_STATUS, {
          step: "test_generate",
          phase: "post_generate",
          benchmarkMode: plan.benchmarkMode ?? "harness",
          targetTestFile: runtime.targetTestFile,
          targetTestFileChanged: postGenerateStatus.targetTestFileChanged,
          targetTestIntentCount: postGenerateStatus.targetTestIntentCount,
          approvedCaseCount: postGenerateStatus.approvedCaseCount,
          postGenerateLintPassed,
        });
      }
      runState.advanceTo("test_generated");
      runState.replaceReviewRecords([]);
      runtime.logger.saveCheckpoint(runState.toCheckpointPayload(new Date().toISOString()));
    }

    if (!shouldSkipStep(runState.getCompletedStep(), "test_reviewed")) {
      await this.reviewService.runTestReview(runtime.reviewOrchestrator, plan, runtime.testPath);
      runState.advanceTo("test_reviewed");
      runState.replaceReviewRecords(runtime.reviewOrchestrator.getRecords());
      runtime.logger.saveCheckpoint(runState.toCheckpointPayload(new Date().toISOString()));
    }

    let redFailureOutput = "";
    if (shouldSkipStep(runState.getCompletedStep(), "red_confirmed") && !shouldSkipStep(runState.getCompletedStep(), "green_confirmed")) {
      const rerunResult = await this.runTests(runtime.testPath, { allowCollectionError: true });
      if (rerunResult.passed) {
        await this.finishAlreadyGreen(plan, runtime, runState, rerunResult.output);
        return;
      }
      redFailureOutput = rerunResult.output;
    }

    if (!shouldSkipStep(runState.getCompletedStep(), "red_confirmed")) {
      console.log("テスト実行中（RED確認）...");
      const redResult = await this.runTests(runtime.testPath, { allowCollectionError: true });
      redFailureOutput = redResult.output;

      if (redResult.passed) {
        await this.finishAlreadyGreen(plan, runtime, runState, redResult.output);
        return;
      }

      runtime.logger.log(EVENT.TEST_RUN, { result: "RED", output: redResult.output });
      runState.advanceTo("red_confirmed");
      runState.replaceReviewRecords(runtime.reviewOrchestrator.getRecords());
      runtime.logger.saveCheckpoint(runState.toCheckpointPayload(new Date().toISOString()));
    }

    let lastFailureOutput = redFailureOutput;
    if (!shouldSkipStep(runState.getCompletedStep(), "green_confirmed")) {
      for (let attempt = 1; attempt <= MAX_GREEN_RETRIES; attempt++) {
        console.log(`実装コードを生成中... (試行 ${attempt}/${MAX_GREEN_RETRIES})`);
        runState.setSessionId(
          await this.generationService.generateImplementation(
            plan,
            runtime,
            lastFailureOutput,
            attempt,
            runState.getSessionId(),
          ),
        );

        await this.boundary.stageFiles(plan.scope);
        await this.lintService.run(runtime.lintGuard, plan.scope, `実装後 (試行 ${attempt})`, {
          scopeTools: runtime.scopeTools,
          root: runtime.root,
        });
        await this.boundary.verifyChangedFilesWithinScope(plan.scope);

        console.log("テスト実行中（GREEN確認）...");
        const greenResult = await this.runTests(runtime.testPath);
        runtime.logger.log(EVENT.TEST_RUN, {
          result: greenResult.passed ? "GREEN" : "FAILED",
          output: greenResult.output,
          attempt,
        });

        if (greenResult.passed) {
          runtime.driftGuard.checkTimeout();
          runtime.driftGuard.checkDiffScope(await this.boundary.countDiffLines());

          runState.markGreen(attempt);
          runState.replaceReviewRecords(runtime.reviewOrchestrator.getRecords());
          runtime.logger.saveCheckpoint(runState.toCheckpointPayload(new Date().toISOString()));

          await this.reviewService.runImplementationReview(
            runtime.reviewOrchestrator,
            plan,
            runtime.criteriaPaths,
            runtime.testPath,
          );
          runState.advanceTo("impl_reviewed");
          runState.replaceReviewRecords(runtime.reviewOrchestrator.getRecords());
          this.generateReport(plan, runtime, runState);
          runtime.logger.clearCheckpoint();
          console.log("完了しました。");
          return;
        }

        lastFailureOutput = greenResult.output;
        const level = runtime.driftGuard.recordTestAttempt(plan.scope, false, greenResult.output);
        if (level !== null) {
          runtime.logger.log(EVENT.DRIFT_DETECTED, { metric: "green_failure", escalation: level, attempt });
          if (level >= ESCALATION_LEVEL.LEVEL_3) {
            throw new GuardError("迷走検知: 人間のエスカレーションが必要です。");
          }
        }
      }

      throw new GuardError(`${MAX_GREEN_RETRIES} 回の試行でテストが GREEN になりませんでした。`);
    }

    if (shouldSkipStep(runState.getCompletedStep(), "green_confirmed") && !shouldSkipStep(runState.getCompletedStep(), "impl_reviewed")) {
      await this.reviewService.runImplementationReview(
        runtime.reviewOrchestrator,
        plan,
        runtime.criteriaPaths,
        runtime.testPath,
      );
      runState.advanceTo("impl_reviewed");
      runState.replaceReviewRecords(runtime.reviewOrchestrator.getRecords());
      this.generateReport(plan, runtime, runState);
      console.log("完了しました。");
    }
  }

  private async validateGeneratedArtifacts(
    plan: TaskPlan,
    runtime: ImplFlowRuntime,
  ): Promise<{ targetTestFileChanged: boolean; targetTestIntentCount: number | null; approvedCaseCount: number }> {
    const targetTestFileAbsolute = resolve(this.boundary.getProjectRoot(), runtime.targetTestFile);
    const testFiles = await this.boundary.findTestFiles(plan.scope);
    const facts: ArtifactValidationFacts = {
      concreteTestFileCount: testFiles.filter((file) => !file.endsWith("/__init__.py")).length,
      targetTestFile: runtime.targetTestFile,
      targetTestFilePresent: testFiles.includes(targetTestFileAbsolute),
      targetTestFileChanged: await this.boundary.hasWorkingTreeChange(runtime.targetTestFile),
      targetTestIntentCount: existsSync(targetTestFileAbsolute)
        ? this.generationService.countTestIntents(readFileSync(targetTestFileAbsolute, "utf-8"))
        : null,
      approvedCaseCount: plan.targetTestCases.length,
    };
    const status = validateArtifactFacts(facts);
    runtime.logger.log(EVENT.BENCHMARK_ARTIFACT_STATUS, {
      step: "test_generate",
      phase: "post_generate_validation",
      benchmarkMode: plan.benchmarkMode ?? "harness",
      targetTestFile: runtime.targetTestFile,
      targetTestFileChanged: status.targetTestFileChanged,
      targetTestIntentCount: status.targetTestIntentCount,
      approvedCaseCount: status.approvedCaseCount,
    });
    return status;
  }

  private async finishAlreadyGreen(
    plan: TaskPlan,
    runtime: ImplFlowRuntime,
    runState: HarnessRun,
    output: string,
  ): Promise<void> {
    this.logAlreadyGreen(plan, runtime, output);
    runState.markAlreadyGreen();
    await this.reviewService.runImplementationReview(
      runtime.reviewOrchestrator,
      plan,
      runtime.criteriaPaths,
      runtime.testPath,
    );
    runState.replaceReviewRecords(runtime.reviewOrchestrator.getRecords());
    this.generateReport(plan, runtime, runState);
    runtime.logger.clearCheckpoint();
    console.log("完了しました。");
  }

  private logAlreadyGreen(
    plan: TaskPlan,
    runtime: ImplFlowRuntime,
    output: string,
  ): void {
    runtime.logger.log(EVENT.TEST_RUN, {
      result: "ALREADY_GREEN",
      output,
      benchmarkMode: plan.benchmarkMode,
    });
    console.log("警告: テストが既にパスしています。実装生成をスキップしてレビューに進みます。");
  }

  private async runTests(
    testPath: string,
    options?: { allowCollectionError?: boolean },
  ): Promise<{ passed: boolean; output: string }> {
    return this.testExecutor.run(testPath, options);
  }

  private generateReport(
    plan: TaskPlan,
    runtime: ImplFlowRuntime,
    runState: HarnessRun,
  ): void {
    writeImplReport(
      this.boundary.getProjectRoot(),
      runtime.logger,
      plan,
      runState.getReviewRecords(),
      {
        greenAttempts: runState.getGreenAttempt(),
        alreadyGreen: runState.isAlreadyGreen(),
      },
    );
  }
}
