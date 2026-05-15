import { readFileSync, writeFileSync, mkdirSync, existsSync } from "node:fs";
import { dirname, resolve, join } from "node:path";
import { HarnessLogger } from "./logger.ts";
import { writeImplReport } from "./application/impl-report-writer.ts";
import { TestExecutor } from "./application/test-executor.ts";
import { LintGuard } from "./lint-guard.ts";
import { DriftGuard } from "./drift-guard.ts";
import { ReviewOrchestrator } from "./review-orchestrator.ts";
import type { Boundary } from "./boundary.ts";
import type { RunnerRegistry } from "./runner-registry.ts";
import { FLOW_STEP } from "./steps.ts";
import { GuardError, HarnessError, ESCALATION_LEVEL, EVENT, STEP_ORDER } from "./types.ts";
import type { TaskPlan, LintViolation, CompletedStep } from "./types.ts";
import type { ResolvedProfileConfig } from "./config.ts";
import { ImplArtifactsPolicy } from "./domain/impl-artifacts.ts";
import { readOptionalRulesContent, resolveReviewCriteriaPaths } from "./domain/review-assets.ts";
import type { LintAdapter, TestAdapter } from "./tool-adapter.ts";
import { loadTemplate, renderTemplate } from "./templates.ts";
import { parsePlan } from "./plan-parser.ts";
import { applyStepContext, joinPromptSections } from "./step-context.ts";

const MAX_GREEN_RETRIES = 3;
const DEFAULT_TIMEOUT_MS = 10 * 60 * 1000;

export class ImplFlow {
  private boundary: Boundary;
  private registry: RunnerRegistry;
  private profile: ResolvedProfileConfig;
  private testAdapter: TestAdapter;
  private lintAdapters: LintAdapter[];
  private artifacts: ImplArtifactsPolicy;
  private testExecutor: TestExecutor;

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
  }

  private shouldSkip(completedStep: CompletedStep | null, target: CompletedStep): boolean {
    if (!completedStep) return false;
    return STEP_ORDER.indexOf(completedStep) >= STEP_ORDER.indexOf(target);
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

  private resetGenerationBenchmarkArtifacts(scope: string, logger?: HarnessLogger): void {
    const targetTestFile = this.artifacts.suggestedTestFilePath(scope);
    const targetImplementationFile = this.artifacts.suggestedImplementationPath(scope);
    this.writeArtifactFile(targetTestFile, this.artifacts.buildTestPlaceholderContent());
    this.writeArtifactFile(targetImplementationFile, this.artifacts.buildImplementationPlaceholderContent());
    logger?.log(EVENT.BENCHMARK_ARTIFACT_RESET, {
      scope,
      targetTestFile,
      targetImplementationFile,
      benchmarkMode: "generation",
    });
  }

  private writeArtifactFile(repoRelativePath: string, content: string): void {
    const absolutePath = resolve(this.boundary.getProjectRoot(), repoRelativePath);
    mkdirSync(dirname(absolutePath), { recursive: true });
    writeFileSync(absolutePath, content, "utf-8");
  }

  private fileDiffersFromContent(repoRelativePath: string, expectedContent: string): boolean {
    const absolutePath = resolve(this.boundary.getProjectRoot(), repoRelativePath);
    if (!existsSync(absolutePath)) return false;
    return readFileSync(absolutePath, "utf-8") !== expectedContent;
  }

  private logPromptPrepared(
    logger: HarnessLogger,
    step: string,
    prompt: string,
    options?: {
      appendSystemPrompt?: string;
      allowedTools?: string[];
      primaryTargetFile?: string;
    },
  ): void {
    logger.log(EVENT.PROMPT_PREPARED, {
      step,
      promptChars: prompt.length,
      promptBytes: Buffer.byteLength(prompt, "utf-8"),
      appendSystemPromptChars: options?.appendSystemPrompt?.length ?? 0,
      appendSystemPromptBytes: Buffer.byteLength(options?.appendSystemPrompt ?? "", "utf-8"),
      allowedToolCount: options?.allowedTools?.length ?? 0,
      primaryTargetFile: options?.primaryTargetFile ?? null,
    });
  }

  private async ensureConcreteTestFilesExist(
    scope: string,
    options?: { requireTargetRewrite?: boolean; approvedCaseCount?: number },
  ): Promise<{
    concreteTestFileCount: number;
    targetTestFileMaterialized: boolean;
    targetTestFileChanged: boolean;
    targetTestIntentCount: number | null;
    approvedCaseCount: number;
  }> {
    const testFiles = await this.boundary.findTestFiles(scope);
    const concrete = testFiles.filter((file) => !file.endsWith("/__init__.py"));
    const targetTestFile = this.artifacts.suggestedTestFilePath(scope);
    const targetTestFileAbsolute = resolve(this.boundary.getProjectRoot(), targetTestFile);
    const targetTestFileMaterialized = this.fileDiffersFromContent(
      targetTestFile,
      this.artifacts.buildTestPlaceholderContent(),
    );
    const targetTestFileChanged = await this.boundary.hasWorkingTreeChange(targetTestFile);
    const approvedCaseCount = options?.approvedCaseCount ?? 0;
    const targetTestIntentCount = existsSync(targetTestFileAbsolute)
      ? this.artifacts.countTestIntents(readFileSync(targetTestFileAbsolute, "utf-8"))
      : null;
    if (concrete.length === 0) {
      throw new GuardError(
        `テスト生成後も収集対象のテストファイルが存在しません。少なくとも ${this.artifacts.suggestedTestFilePath(scope)} のようなテストファイルを生成してください。`,
      );
    }
    if (options?.requireTargetRewrite) {
      if (!testFiles.includes(targetTestFileAbsolute)) {
        throw new GuardError(
          `generation benchmark の test_generate が主対象のテストファイル ${targetTestFile} を生成していません。対象ファイルを直接更新してください。`,
        );
      }
      if (!targetTestFileMaterialized) {
        throw new GuardError(
          `generation benchmark の test_generate が ${targetTestFile} の placeholder を置換していません。既存テストの監査で終わらず、対象ファイルを具体的なテストで更新してください。`,
        );
      }
    }
    if (
      approvedCaseCount > 0 &&
      targetTestIntentCount !== null &&
      targetTestIntentCount > approvedCaseCount + 2
    ) {
      throw new GuardError(
        `生成テストの test intent 数 (${targetTestIntentCount}) が承認済みテストケース数 (${approvedCaseCount}) から大きく逸脱しています。approved cases にない独自追加や不要分割をやめてください。`,
      );
    }
    return {
      concreteTestFileCount: concrete.length,
      targetTestFileMaterialized,
      targetTestFileChanged,
      targetTestIntentCount,
      approvedCaseCount,
    };
  }

  private handleAlreadyGreen(
    plan: TaskPlan,
    logger: HarnessLogger,
    reviewOrchestrator: ReviewOrchestrator,
    output: string,
  ): never | Promise<void> {
    logger.log(EVENT.TEST_RUN, { result: "ALREADY_GREEN", output, benchmarkMode: plan.benchmarkMode });
    if (this.artifacts.isGenerationBenchmark(plan)) {
      this.generateReport(plan, logger, reviewOrchestrator.getRecords(), {
        greenAttempts: 0,
        alreadyGreen: true,
        invalidReason: "already_green",
      });
      throw new GuardError(
        "generation benchmark は ALREADY_GREEN を許容しません。既存実装ありの検証は benchmark: harness を使用してください。",
      );
    }
    console.log("警告: テストが既にパスしています。実装生成をスキップしてレビューに進みます。");
    return Promise.resolve();
  }

  async run(planPath: string, options?: { resume?: boolean; plan?: import("./types.ts").TaskPlan }): Promise<void> {
    const plan = options?.plan ?? parsePlan(this.boundary.getProjectRoot(), planPath);
    const root = this.boundary.getProjectRoot();
    const logger = new HarnessLogger(`impl_${plan.scope.replace(/\//g, "_")}`, { baseDir: join(root, "logs"), resume: options?.resume });
    const lintGuard = new LintGuard(logger, this.lintAdapters, {
      toolRoot: this.profile.toolRoot,
      execOverride: this.profile.exec,
    });
    // codexAvailable: ImplFlow の迷走対処に寄与する step で codex が使えるか
    // impl フローで実際に使う step のうち、外部レビュー系のみを判定対象とする
    const implFlowSteps: import("./steps.ts").FlowStep[] = [
      FLOW_STEP.TEST_EXTERNAL_REVIEW,
      FLOW_STEP.IMPL_EXTERNAL_REVIEW,
    ];
    const stepMapping = this.registry.getStepMapping();
    const runnerConfig = this.registry.getConfig();
    const hasCodex = implFlowSteps.some((step) => {
      if (this.registry.isStepSkipped(step)) return false;
      const runnerName = stepMapping[step];
      if (!runnerName) return false;
      const provider = runnerConfig.providers[runnerName];
      return provider?.type === "codex";
    });
    const driftGuard = new DriftGuard(logger, { codexAvailable: hasCodex });
    const reviewOrchestrator = new ReviewOrchestrator(logger, lintGuard, root, this.registry, this.profile);

    // チェックポイント復元
    const checkpoint = options?.resume ? logger.loadCheckpoint() : null;
    const resumeFrom = checkpoint?.completedStep ?? null;
    let sessionId = checkpoint?.sessionId ?? "";

    if (resumeFrom) {
      console.log(`チェックポイントから再開: ${resumeFrom} 以降を実行`);
      // 前回のレビュー記録を復元
      if (checkpoint?.records && checkpoint.records.length > 0) {
        reviewOrchestrator.restoreRecords(checkpoint.records);
      }
    }

    // ガードチェック
    this.boundary.implementationGuard(plan);
    logger.log(EVENT.GUARD_CHECK, { scope: plan.scope, result: "pass" });

    const LINES_PER_TEST_CASE = 30;
    const expectedLines = plan.targetTestCases.length * LINES_PER_TEST_CASE;
    driftGuard.startTask(plan.scope, expectedLines);
    const scopeTools = this.boundary.scopeAllowedTools(plan.scope);
    const testPath = this.boundary.testPathForScope(plan.scope);
    const targetTestFile = this.artifacts.suggestedTestFilePath(plan.scope);
    const targetImplementationFile = this.artifacts.suggestedImplementationPath(plan.scope);
    const testGenerateTools = [
      "Read",
      `Write(${targetTestFile})`,
      `Edit(${targetTestFile})`,
    ];

    const spec = readFileSync(resolve(root, plan.specPath), "utf-8");
    const criteriaPaths = this.resolveCriteriaPaths();
    const rules = this.resolveRulesContent(plan);
    const generationSystemPrompt = joinPromptSections([rules]);

    logger.log(EVENT.TDD_START, { testCases: plan.targetTestCases });

    if (this.artifacts.isGenerationBenchmark(plan)) {
      this.resetGenerationBenchmarkArtifacts(plan.scope, logger);
      const precheck = await this.runTests(testPath, { allowCollectionError: true });
      logger.log(EVENT.BENCHMARK_ARTIFACT_STATUS, {
        step: FLOW_STEP.TEST_GENERATE,
        phase: "precheck",
        benchmarkMode: "generation",
        targetTestFile,
        targetImplementationFile,
        targetTestFileMaterialized: this.fileDiffersFromContent(
          targetTestFile,
          this.artifacts.buildTestPlaceholderContent(),
        ),
        targetImplementationFileMaterialized: this.fileDiffersFromContent(
          targetImplementationFile,
          this.artifacts.buildImplementationPlaceholderContent(),
        ),
        precheckPassed: precheck.passed,
      });
      if (precheck.passed) {
        await this.handleAlreadyGreen(plan, logger, reviewOrchestrator, precheck.output);
      }
    }

    // テストコード一括生成
    if (!this.shouldSkip(resumeFrom, "test_generated")) {
      console.log("テストコードを生成中...");
      const runner = this.registry.getRunner(FLOW_STEP.TEST_GENERATE);
      const config = this.registry.getConfig();
      const testGenTemplate = loadTemplate("test-generate", root, config.templates);
      const testGenPrompt = renderTemplate(testGenTemplate, {
        testCases: plan.targetTestCases.join("\n"),
        spec,
        frameworkName: this.testAdapter.frameworkName,
        mswInstructions: this.artifacts.buildMswInstructions(plan, "test"),
        artifactInstructions: this.artifacts.buildArtifactInstructions(plan, "test"),
        targetTestFile,
        targetImplementationFile,
      });
      this.logPromptPrepared(logger, FLOW_STEP.TEST_GENERATE, testGenPrompt, {
        appendSystemPrompt: generationSystemPrompt,
        allowedTools: testGenerateTools,
        primaryTargetFile: targetTestFile,
      });
      const testGenResult = await runner.run(
        applyStepContext(
          {
            prompt: testGenPrompt,
            allowedTools: testGenerateTools,
            appendSystemPrompt: generationSystemPrompt,
            cwd: root,
            timeoutMs: DEFAULT_TIMEOUT_MS,
            observability: {
              step: FLOW_STEP.TEST_GENERATE,
              benchmarkMode: plan.benchmarkMode,
              primaryTargetFile: targetTestFile,
              relatedFiles: [targetImplementationFile],
            },
          },
          config,
          this.profile,
          FLOW_STEP.TEST_GENERATE,
          root,
          runner.name,
        ),
        logger,
      );
      sessionId = testGenResult.sessionId ?? "";
      await this.boundary.stageFiles(plan.scope);
      const postGenerateStatus = await this.ensureConcreteTestFilesExist(plan.scope, {
        requireTargetRewrite: this.artifacts.isGenerationBenchmark(plan),
        approvedCaseCount: plan.targetTestCases.length,
      });
      logger.log(EVENT.BENCHMARK_ARTIFACT_STATUS, {
        step: FLOW_STEP.TEST_GENERATE,
        phase: "post_generate_validation",
        benchmarkMode: plan.benchmarkMode ?? "harness",
        targetTestFile,
        targetTestFileChanged: postGenerateStatus.targetTestFileChanged,
        targetTestFileMaterialized: postGenerateStatus.targetTestFileMaterialized,
        concreteTestFileCount: postGenerateStatus.concreteTestFileCount,
        targetTestIntentCount: postGenerateStatus.targetTestIntentCount,
        approvedCaseCount: postGenerateStatus.approvedCaseCount,
      });
      let postGenerateLintPassed = false;
      try {
        await this.lintCheck(lintGuard, plan.scope, "テスト生成後", {
          scopeTools: testGenerateTools,
          root,
        });
        postGenerateLintPassed = true;
      } finally {
        logger.log(EVENT.BENCHMARK_ARTIFACT_STATUS, {
          step: FLOW_STEP.TEST_GENERATE,
          phase: "post_generate",
          benchmarkMode: plan.benchmarkMode ?? "harness",
          targetTestFile,
          targetTestFileChanged: postGenerateStatus.targetTestFileChanged,
          targetTestFileMaterialized: postGenerateStatus.targetTestFileMaterialized,
          concreteTestFileCount: postGenerateStatus.concreteTestFileCount,
          targetTestIntentCount: postGenerateStatus.targetTestIntentCount,
          approvedCaseCount: postGenerateStatus.approvedCaseCount,
          postGenerateLintPassed,
        });
      }
      logger.saveCheckpoint({
        planPath, completedStep: "test_generated", sessionId,
        records: [], greenAttempt: 0, timestamp: new Date().toISOString(),
      });
    }

    // テストレビュー
    if (!this.shouldSkip(resumeFrom, "test_reviewed")) {
      await this.runTestReview(reviewOrchestrator, plan, testPath);
      logger.saveCheckpoint({
        planPath, completedStep: "test_reviewed", sessionId,
        records: reviewOrchestrator.getRecords(), greenAttempt: 0,
        timestamp: new Date().toISOString(),
      });
    }

    // RED 確認
    let redFailureOutput = "";
    // resume で red_confirmed をスキップする場合、初回実装プロンプト用に RED 出力を復元
    if (this.shouldSkip(resumeFrom, "red_confirmed") && !this.shouldSkip(resumeFrom, "green_confirmed")) {
      const rerunResult = await this.runTests(testPath, { allowCollectionError: true });
      if (rerunResult.passed) {
        // resume 時にテストが既に GREEN → benchmark mode に応じて失格またはレビュー続行
        await this.handleAlreadyGreen(plan, logger, reviewOrchestrator, rerunResult.output);
        await this.runImplReview(reviewOrchestrator, plan, criteriaPaths, testPath);
        this.generateReport(plan, logger, reviewOrchestrator.getRecords(), { greenAttempts: 0, alreadyGreen: true });
        logger.clearCheckpoint();
        console.log("完了しました。");
        return;
      }
      redFailureOutput = rerunResult.output;
    }
    if (!this.shouldSkip(resumeFrom, "red_confirmed")) {
      console.log("テスト実行中（RED確認）...");
      const redResult = await this.runTests(testPath, { allowCollectionError: true });
      redFailureOutput = redResult.output;

      if (redResult.passed) {
        await this.handleAlreadyGreen(plan, logger, reviewOrchestrator, redResult.output);
        await this.runImplReview(reviewOrchestrator, plan, criteriaPaths, testPath);
        this.generateReport(plan, logger, reviewOrchestrator.getRecords(), { greenAttempts: 0, alreadyGreen: true });
        logger.clearCheckpoint();
        console.log("完了しました。");
        return;
      }

      logger.log(EVENT.TEST_RUN, { result: "RED", output: redResult.output });
      logger.saveCheckpoint({
        planPath, completedStep: "red_confirmed", sessionId,
        records: reviewOrchestrator.getRecords(), greenAttempt: 0,
        timestamp: new Date().toISOString(),
      });
    }

    // 実装 → GREEN リトライループ
    let lastFailureOutput = redFailureOutput;
    if (!this.shouldSkip(resumeFrom, "green_confirmed")) {
    for (let attempt = 1; attempt <= MAX_GREEN_RETRIES; attempt++) {
      console.log(`実装コードを生成中... (試行 ${attempt}/${MAX_GREEN_RETRIES})`);

      const config = this.registry.getConfig();
      const implTemplate = attempt === 1
        ? loadTemplate("impl-generate", root, config.templates)
        : loadTemplate("impl-retry", root, config.templates);
      const implPrompt = renderTemplate(implTemplate, {
        testOutput: lastFailureOutput,
        spec,
        mswInstructions: this.artifacts.buildMswInstructions(plan, "impl"),
        artifactInstructions: this.artifacts.buildArtifactInstructions(plan, "impl"),
        targetTestFile,
        targetImplementationFile,
      });

      const implRunner = this.registry.getRunner(FLOW_STEP.IMPL_GENERATE);
      const implResult = await implRunner.run(
        applyStepContext(
          {
            prompt: implPrompt,
            allowedTools: scopeTools,
            appendSystemPrompt: generationSystemPrompt,
            sessionId,
            cwd: root,
            timeoutMs: DEFAULT_TIMEOUT_MS,
          },
          config,
          this.profile,
          FLOW_STEP.IMPL_GENERATE,
          root,
          implRunner.name,
        ),
        logger,
      );
      sessionId = implResult.sessionId ?? sessionId;

      // 実装生成後にステージング
      await this.boundary.stageFiles(plan.scope);

      // リントチェック
      await this.lintCheck(lintGuard, plan.scope, `実装後 (試行 ${attempt})`, {
        scopeTools: scopeTools,
        root,
      });

      // スコープ外変更の検証
      await this.boundary.verifyChangedFilesWithinScope(plan.scope);

      // GREEN 確認
      console.log("テスト実行中（GREEN確認）...");
      const greenResult = await this.runTests(testPath);
      logger.log(EVENT.TEST_RUN, {
        result: greenResult.passed ? "GREEN" : "FAILED",
        output: greenResult.output,
        attempt,
      });

      if (greenResult.passed) {
        driftGuard.checkTimeout();

        const diffLines = await this.boundary.countDiffLines();
        driftGuard.checkDiffScope(diffLines);

        logger.saveCheckpoint({
          planPath, completedStep: "green_confirmed", sessionId,
          records: reviewOrchestrator.getRecords(), greenAttempt: attempt,
          timestamp: new Date().toISOString(),
        });

        // 実装レビュー（3ステップ: self_criteria + self_quality + codex）
        await this.runImplReview(reviewOrchestrator, plan, criteriaPaths, testPath);
        this.generateReport(plan, logger, reviewOrchestrator.getRecords(), { greenAttempts: attempt, alreadyGreen: false });
        logger.clearCheckpoint();
        console.log("完了しました。");
        return;
      }

      // 次の試行のために最新の失敗出力を保持
      lastFailureOutput = greenResult.output;

      // DriftGuard に失敗を記録
      const level = driftGuard.recordTestAttempt(plan.scope, false, greenResult.output);
      if (level !== null) {
        logger.log(EVENT.DRIFT_DETECTED, { metric: "green_failure", escalation: level, attempt });
        if (level >= ESCALATION_LEVEL.LEVEL_3) {
          throw new GuardError("迷走検知: 人間のエスカレーションが必要です。");
        }
      }
    }

    throw new GuardError(
      `${MAX_GREEN_RETRIES} 回の試行でテストが GREEN になりませんでした。`,
    );
    } // end if !shouldSkip green_confirmed

    // GREEN確認済みからの再開: 実装レビューのみ実行
    if (this.shouldSkip(resumeFrom, "green_confirmed") && !this.shouldSkip(resumeFrom, "impl_reviewed")) {
      await this.runImplReview(reviewOrchestrator, plan, criteriaPaths, testPath);
      const greenAttempt = checkpoint?.greenAttempt ?? 1;
      this.generateReport(plan, logger, reviewOrchestrator.getRecords(), { greenAttempts: greenAttempt, alreadyGreen: false });
      console.log("完了しました。");
    }
  }

  private async lintCheck(
    lintGuard: LintGuard, scope: string, phase: string,
    options?: { scopeTools?: string[]; root?: string },
  ): Promise<void> {
    console.log(`リントチェック中（${phase}）...`);
    const sourceFiles = await this.boundary.findSourceFiles(scope);
    if (sourceFiles.length === 0) return;

    const claudeFix = options?.scopeTools
      ? async (violations: LintViolation[]) => {
          const issueList = violations
            .map((v) => `${v.tool}: ${v.file}:${v.line} - ${v.message}`)
            .join("\n");
          const runner = this.registry.getRunner(FLOW_STEP.LINT_FIX);
          await runner.run(
            applyStepContext(
              {
                prompt: `以下のリンター違反を修正してください。自動修正できなかった違反です。

## 違反一覧
${issueList}

## 制約
- 指摘された違反のみ修正する
- 既存のロジックや振る舞いを変更しない`,
                allowedTools: options.scopeTools,
                cwd: options.root,
              },
              this.registry.getConfig(),
              this.profile,
              FLOW_STEP.LINT_FIX,
              this.boundary.getProjectRoot(),
              runner.name,
            ),
            undefined,
          );
        }
      : undefined;

    await lintGuard.check(sourceFiles, {
      claudeFix,
    });
  }

  private async runTestReview(
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
        const result = await this.runTests(testPath);
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

  private async runImplReview(
    orchestrator: ReviewOrchestrator,
    plan: TaskPlan,
    criteriaPaths: string[],
    testPath: string,
  ): Promise<void> {
    const implFiles = await this.boundary.findImplementationFiles(plan.scope);
    if (implFiles.length === 0) return;

    console.log("実装レビュー実行中...");
    await orchestrator.runReview({
      targetFiles: implFiles,
      specPath: resolve(this.boundary.getProjectRoot(), plan.specPath),
      criteriaPaths,
      runTests: async () => {
        const result = await this.runTests(testPath);
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

  private async runTests(
    testPath: string,
    options?: { allowCollectionError?: boolean },
  ): Promise<{ passed: boolean; output: string }> {
    return this.testExecutor.run(testPath, options);
  }

  private generateReport(
    plan: TaskPlan,
    logger: HarnessLogger,
    records: import("./types.ts").ReviewRecord[],
    tdd: { greenAttempts: number; alreadyGreen: boolean; invalidReason?: string },
  ): void {
    writeImplReport(this.boundary.getProjectRoot(), logger, plan, records, tdd);
  }
}
