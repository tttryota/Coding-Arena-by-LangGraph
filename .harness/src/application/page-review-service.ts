import { resolve } from "node:path";
import { stringify as stringifyYaml } from "yaml";
import type { Boundary } from "../boundary.ts";
import type { ReviewOrchestrator } from "../review-orchestrator.ts";
import type { TaskPlan } from "../types.ts";
import { HarnessError } from "../types.ts";
import type { TestExecutor } from "./test-executor.ts";

export class PageReviewService {
  private boundary: Boundary;
  private testExecutor: TestExecutor;

  constructor(boundary: Boundary, testExecutor: TestExecutor) {
    this.boundary = boundary;
    this.testExecutor = testExecutor;
  }

  async runImplementationReview(
    orchestrator: ReviewOrchestrator,
    plan: TaskPlan,
    criteriaPaths: string[],
  ): Promise<void> {
    const implFilesRescan = () => this.boundary.findImplementationFiles(plan.scope);
    console.log("ページレビュー実行中...");
    await orchestrator.runPageReview({
      targetFiles: await implFilesRescan(),
      specPath: resolve(this.boundary.getProjectRoot(), plan.specPath),
      criteriaPaths,
      runTests: async () => {
        const result = await this.testExecutor.run(this.boundary.testPathForScope(plan.scope));
        if (!result.passed) {
          throw new HarnessError(`ページテスト失敗: ${result.output}`);
        }
      },
      rescanFiles: implFilesRescan,
      scopeAllowedTools: this.boundary.implAllowedTools(plan.scope),
      getFileDiff: (files: string[]) => this.boundary.getFileDiff(files),
      designDecisions: plan.designDecisions,
      reviewMode: "implementation",
      testCasesPath: resolve(this.boundary.getProjectRoot(), plan.testCasesPath),
      componentSpecPath: resolve(this.boundary.getProjectRoot(), plan.componentSpecPath ?? ""),
      figmaSlice: plan.figmaSlice ?? "",
      dependenciesText: stringifyYaml(
        plan.dependencies.map((dependency) => ({
          name: dependency.name,
          import: dependency.importPath,
        })),
      ),
      browserScenariosText: stringifyYaml(plan.browserScenarios),
    });
  }
}
