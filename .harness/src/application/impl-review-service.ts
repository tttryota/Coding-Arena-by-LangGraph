import { resolve } from "node:path";
import type { Boundary } from "../boundary.ts";
import type { ReviewOrchestrator } from "../review-orchestrator.ts";
import type { TaskPlan } from "../types.ts";
import { HarnessError } from "../types.ts";
import type { TestExecutor } from "./test-executor.ts";

export class ImplReviewService {
  private boundary: Boundary;
  private testExecutor: TestExecutor;

  constructor(boundary: Boundary, testExecutor: TestExecutor) {
    this.boundary = boundary;
    this.testExecutor = testExecutor;
  }

  async runTestReview(
    orchestrator: ReviewOrchestrator,
    plan: TaskPlan,
    testPath: string,
  ): Promise<void> {
    const testFiles = await this.boundary.findTestFiles(plan.scope);
    if (testFiles.length === 0) return;

    console.log("テストレビュー実行中...");
    await orchestrator.runReview({
      targetFiles: testFiles,
      specPath: resolve(this.boundary.getProjectRoot(), plan.specPath),
      criteriaPaths: [],
      runTests: async () => {
        const result = await this.testExecutor.run(testPath);
        if (!result.passed) {
          throw new HarnessError(`テスト失敗: ${result.output}`);
        }
      },
      rescanFiles: () => this.boundary.findTestFiles(plan.scope),
      scopeAllowedTools: this.boundary.testAllowedTools(plan.scope),
      getFileDiff: (files: string[]) => this.boundary.getFileDiff(files),
      reviewMode: "test",
      testCasesPath: resolve(this.boundary.getProjectRoot(), plan.testCasesPath),
    });
  }

  async runImplementationReview(
    orchestrator: ReviewOrchestrator,
    plan: TaskPlan,
    criteriaPaths: string[],
    testPath: string,
  ): Promise<void> {
    const implementationFiles = await this.boundary.findImplementationFiles(plan.scope);
    if (implementationFiles.length === 0) return;

    console.log("実装レビュー実行中...");
    await orchestrator.runReview({
      targetFiles: implementationFiles,
      specPath: resolve(this.boundary.getProjectRoot(), plan.specPath),
      criteriaPaths,
      runTests: async () => {
        const result = await this.testExecutor.run(testPath);
        if (!result.passed) {
          throw new HarnessError(`テスト失敗: ${result.output}`);
        }
      },
      rescanFiles: () => this.boundary.findImplementationFiles(plan.scope),
      scopeAllowedTools: this.boundary.implAllowedTools(plan.scope),
      getFileDiff: (files: string[]) => this.boundary.getFileDiff(files),
      designDecisions: plan.designDecisions,
      reviewMode: "implementation",
    });
  }
}
