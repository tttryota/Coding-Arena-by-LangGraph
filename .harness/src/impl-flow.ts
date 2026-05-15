import { readFileSync, writeFileSync, mkdirSync, existsSync } from "node:fs";
import { dirname, resolve, join } from "node:path";
import { HarnessLogger, redact } from "./logger.ts";
import { LintGuard } from "./lint-guard.ts";
import { DriftGuard } from "./drift-guard.ts";
import { ReviewOrchestrator } from "./review-orchestrator.ts";
import type { Boundary } from "./boundary.ts";
import type { RunnerRegistry } from "./runner-registry.ts";
import { FLOW_STEP } from "./steps.ts";
import { GuardError, HarnessError, ESCALATION_LEVEL, EVENT, STEP_ORDER } from "./types.ts";
import type { TaskPlan, ReviewRecord, LintViolation, CompletedStep } from "./types.ts";
import type { ResolvedProfileConfig } from "./config.ts";
import { readOptionalRulesContent, resolveReviewCriteriaPaths } from "./domain/review-assets.ts";
import type { LintAdapter, TestAdapter } from "./tool-adapter.ts";
import { loadTemplate, renderTemplate } from "./templates.ts";
import { runTool } from "./launcher.ts";
import type { LauncherOptions } from "./launcher.ts";
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
      this.resolveRuleName(plan),
    );
  }

  private resolveRuleName(plan: TaskPlan): string | undefined {
    if (plan.type === "impl" && plan.profile === "frontend") {
      return "logic";
    }
    return plan.type;
  }

  private buildMswInstructions(plan: TaskPlan, mode: "test" | "impl"): string {
    if (!plan.msw) return "";

    if (mode === "test") {
      return `## MSW セットアップ
- テストファイルに MSW server のセットアップ (beforeAll/afterEach/afterAll) を含める
- API モック用の handler import を含める（handler ファイルは実装フェーズで生成される）
- handler の配置先: frontend/src/mocks/handlers/
- server.use(...handlers) でモックを適用する`;
    }

    return `## MSW ハンドラ生成
- frontend/src/mocks/handlers/ に共有ハンドラファイルを生成する
- ハンドラのレスポンス形状はバックエンド API の契約と一致させる
- テストファイルから import されるパスと一致させる`;
  }

  private isGenerationBenchmark(plan: TaskPlan): boolean {
    return plan.benchmarkMode === "generation";
  }

  private scopeModuleName(scope: string): string {
    return this.boundary.extractName(scope).replace(/-/g, "_");
  }

  private suggestedTestFilePath(scope: string): string {
    const testDir = this.boundary.testPathForScope(scope);
    const moduleName = this.scopeModuleName(scope);
    if (this.testAdapter.name === "pytest") {
      return `${testDir}/test_${moduleName}.py`;
    }
    if (this.testAdapter.name === "vitest") {
      return `${testDir}/${this.boundary.extractName(scope)}.test.ts`;
    }
    return `${testDir}/`;
  }

  private suggestedImplementationPath(scope: string): string {
    const sourceDir = this.boundary.sourcePathForScope(scope);
    const moduleName = this.scopeModuleName(scope);
    if (this.testAdapter.name === "pytest") {
      return `${sourceDir}/${moduleName}.py`;
    }
    if (this.testAdapter.name === "vitest") {
      return `${sourceDir}/${this.boundary.extractName(scope)}.ts`;
    }
    return `${sourceDir}/`;
  }

  private buildArtifactInstructions(plan: TaskPlan, mode: "test" | "impl"): string {
    const generationBenchmarkDiscipline = this.isGenerationBenchmark(plan)
      ? [
          "## Generation Benchmark Discipline",
          "- 既に置かれている placeholder ファイルをそのまま置換すること",
          "- 参照してよい一次情報は spec、approved test cases、対象の placeholder ファイル、および言語設定ファイルまでに限定すること",
          "- docs/reviews や過去の benchmark レポートは参照しないこと",
          "- 最低限の確認が済んだらすぐに対象ファイルへ書き込みを開始すること",
        ].join("\n")
      : "";
    const generationTestDiscipline = this.isGenerationBenchmark(plan) && mode === "test"
      ? [
          "- 最初に主対象のテストファイルを placeholder から置換すること",
          "- この step で書き込む先は主対象のテストファイルに限定すること",
          "- repo 全体の充足確認や既存 concrete test の監査だけで終わらないこと",
          "- 実装内容の探索は import や公開インターフェース確認に必要な最小限に留めること",
        ].join("\n")
      : "";

    if (mode === "test") {
      return [
        "## 生成物の配置",
        `- この step では workspace 上のテストファイルを直接作成または更新すること`,
        `- 主対象のテストファイル候補: ${this.suggestedTestFilePath(plan.scope)}`,
        `- 少なくとも 1 件は pytest/vitest が収集できる実テストケースを含めること`,
        "- 回答本文だけでコードを返さず、ファイルへ反映すること",
        generationBenchmarkDiscipline,
        generationTestDiscipline,
      ].join("\n");
    }

    return [
      "## 生成物の配置",
      `- この step では workspace 上の実装ファイルを直接作成または更新すること`,
      `- 主対象の実装ファイル候補: ${this.suggestedImplementationPath(plan.scope)}`,
      `- テストが import できる配置・モジュール名に合わせること`,
      "- 回答本文だけでコードを返さず、ファイルへ反映すること",
      generationBenchmarkDiscipline,
    ].join("\n");
  }

  private buildTestPlaceholderContent(): string {
    if (this.testAdapter.name === "pytest") {
      return [
        '"""Harness placeholder: replace with concrete pytest cases for this scope."""',
        "",
        "def test_harness_placeholder() -> None:",
        '    raise AssertionError("Replace this placeholder with concrete benchmark tests.")',
        "",
      ].join("\n");
    }
    if (this.testAdapter.name === "vitest") {
      return [
        'import { describe, it, expect } from "vitest";',
        "",
        'describe("harness placeholder", () => {',
        '  it("must be replaced with concrete benchmark tests", () => {',
        '    expect(false, "replace placeholder tests").toBe(true);',
        "  });",
        "});",
        "",
      ].join("\n");
    }
    return [
      "# Harness placeholder: replace with concrete tests for this scope.",
      "",
    ].join("\n");
  }

  private buildImplementationPlaceholderContent(): string {
    if (this.testAdapter.name === "pytest") {
      return [
        '"""Harness placeholder: replace with the concrete implementation for this scope."""',
        "",
      ].join("\n");
    }
    return "// Harness placeholder: replace with the concrete implementation for this scope.\n";
  }

  private resetGenerationBenchmarkArtifacts(scope: string, logger?: HarnessLogger): void {
    const targetTestFile = this.suggestedTestFilePath(scope);
    const targetImplementationFile = this.suggestedImplementationPath(scope);
    this.writeArtifactFile(targetTestFile, this.buildTestPlaceholderContent());
    this.writeArtifactFile(targetImplementationFile, this.buildImplementationPlaceholderContent());
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
    const targetTestFile = this.suggestedTestFilePath(scope);
    const targetTestFileAbsolute = resolve(this.boundary.getProjectRoot(), targetTestFile);
    const targetTestFileMaterialized = this.fileDiffersFromContent(
      targetTestFile,
      this.buildTestPlaceholderContent(),
    );
    const targetTestFileChanged = await this.boundary.hasWorkingTreeChange(targetTestFile);
    const approvedCaseCount = options?.approvedCaseCount ?? 0;
    const targetTestIntentCount = existsSync(targetTestFileAbsolute)
      ? this.countTestIntents(readFileSync(targetTestFileAbsolute, "utf-8"))
      : null;
    if (concrete.length === 0) {
      throw new GuardError(
        `テスト生成後も収集対象のテストファイルが存在しません。少なくとも ${this.suggestedTestFilePath(scope)} のようなテストファイルを生成してください。`,
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

  private countTestIntents(fileContents: string): number {
    if (this.testAdapter.name === "pytest") {
      const matches = fileContents.match(/^\s*def\s+test_[A-Za-z0-9_]+\s*\(/gm);
      return matches?.length ?? 0;
    }
    if (this.testAdapter.name === "vitest") {
      const matches = fileContents.match(/\b(?:it|test)\s*\(/g);
      return matches?.length ?? 0;
    }
    return 0;
  }

  private handleAlreadyGreen(
    plan: TaskPlan,
    logger: HarnessLogger,
    reviewOrchestrator: ReviewOrchestrator,
    output: string,
  ): never | Promise<void> {
    logger.log(EVENT.TEST_RUN, { result: "ALREADY_GREEN", output, benchmarkMode: plan.benchmarkMode });
    if (this.isGenerationBenchmark(plan)) {
      this.generateReport(
        plan,
        logger,
        reviewOrchestrator.getRecords(),
        {
          greenAttempts: 0,
          alreadyGreen: true,
          invalidReason: "already_green",
        },
      );
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
    const targetTestFile = this.suggestedTestFilePath(plan.scope);
    const targetImplementationFile = this.suggestedImplementationPath(plan.scope);
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

    if (this.isGenerationBenchmark(plan)) {
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
          this.buildTestPlaceholderContent(),
        ),
        targetImplementationFileMaterialized: this.fileDiffersFromContent(
          targetImplementationFile,
          this.buildImplementationPlaceholderContent(),
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
        mswInstructions: this.buildMswInstructions(plan, "test"),
        artifactInstructions: this.buildArtifactInstructions(plan, "test"),
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
        requireTargetRewrite: this.isGenerationBenchmark(plan),
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
        mswInstructions: this.buildMswInstructions(plan, "impl"),
        artifactInstructions: this.buildArtifactInstructions(plan, "impl"),
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
    // testPath は repo-relative。toolRoot が root 以外の場合に備え絶対パスに変換
    const absTestPath = resolve(this.boundary.getProjectRoot(), testPath);
    const args = this.testAdapter.buildArgs(absTestPath);
    const launcherOptions: LauncherOptions = {
      toolRoot: this.profile.toolRoot,
      execOverride: this.profile.exec,
    };
    const result = await runTool(this.testAdapter.name, args, launcherOptions);
    const testResult = this.testAdapter.parseResult(
      result.stdout,
      result.stderr,
      result.exitCode,
    );

    switch (testResult.kind) {
      case "passed":
        return { passed: true, output: testResult.output };
      case "failed":
        return { passed: false, output: testResult.output };
      case "collection-error":
        if (options?.allowCollectionError) {
          return { passed: false, output: testResult.output };
        }
        throw new GuardError(
          `${this.testAdapter.frameworkName} がコレクションエラーで終了しました。環境を確認してください。\n${testResult.output}`,
        );
      case "no-tests":
        throw new GuardError(
          `${this.testAdapter.frameworkName} がテスト未検出で終了しました。テストパスを確認してください。`,
        );
      case "internal-error":
      case "interrupted":
        throw new GuardError(
          `${this.testAdapter.frameworkName} が内部エラーで終了しました (exit ${testResult.exitCode})。\n${testResult.output}`,
        );
    }
  }

  private generateReport(
    plan: TaskPlan,
    logger: HarnessLogger,
    records: ReviewRecord[],
    tdd: { greenAttempts: number; alreadyGreen: boolean; invalidReason?: string },
  ): void {
    const root = this.boundary.getProjectRoot();
    const timestamp = new Date().toISOString().replace(/[:.]/g, "-").slice(0, 19);
    const scopeSlug = plan.scope.replace(/\//g, "_");
    const usageSummary = logger.summarizeRunnerUsage();

    // review-data.json を保存
    logger.saveReviewData({
      plan,
      benchmark: {
        mode: plan.benchmarkMode ?? null,
        invalidReason: tdd.invalidReason ?? null,
      },
      records,
      tdd,
      usageSummary,
    });

    // MD レポート生成
    // 集計対象: accepted を除いたレビュー実行レコードのみ
    const activeRecords = records.filter(
      (r) => r.step !== "design_decision" && r.decision !== "accepted",
    );
    const fixedRecords = activeRecords.filter((r) => r.decision === "fixed");
    const lgtmRecords = activeRecords.filter((r) => r.decision === "lgtm");
    const acceptedRecords = records.filter((r) => r.decision === "accepted");
    // レビューステップ数（ユニークな step で数える）
    const reviewSteps = [...new Set(activeRecords.map((r) => r.step))].length;
    // レビューサイクル総数（修正による再実行を含む）
    const totalCycles = activeRecords.length;
    // 修正した指摘の総件数（record 数ではなく issue 数）
    const fixCount = fixedRecords.reduce((sum, r) => sum + r.findings.length, 0);

    let md = `# タスクレポート: ${plan.scope}

**実行日**: ${timestamp}
**スコープ**: ${plan.scope}
**結果**: 完了
**ベンチマーク種別**: ${plan.benchmarkMode ?? "none"}
**レビューサイクル数**: ${totalCycles}回
**修正件数**: ${fixCount}件
**LLM実行回数**: ${usageSummary.total.runs}回

## 対象テストケース
${plan.targetTestCases.map((tc, i) => `${i + 1}. ${tc}`).join("\n")}

## TDD サイクル
`;

    if (tdd.alreadyGreen) {
      md += `- テスト生成後、既に GREEN（実装生成スキップ）\n`;
    } else {
      md += `- 実装生成: ${tdd.greenAttempts}回目で GREEN（最大3回）\n`;
    }
    if (tdd.invalidReason) {
      md += `- benchmark 判定: 無効（${tdd.invalidReason}）\n`;
    }

    md += `\n---\n\n## レビュー詳細\n\n`;

    // ステップごとにグループ化（design_decision と accepted は別セクションで出力）
    const displayRecords = records.filter(
      (r) => r.step !== "design_decision" && r.decision !== "accepted",
    );
    const steps = [...new Set(displayRecords.map((r) => r.step))];
    for (const step of steps) {
      const stepRecords = displayRecords.filter((r) => r.step === step);
      md += `### ${step}\n\n`;

      for (const record of stepRecords) {
        if (record.decision === "lgtm") {
          md += `指摘なし（${record.cycle}回目で通過）\n\n`;
        } else if (record.decision === "fixed") {
          // 指摘一覧
          for (const issue of record.findings) {
            md += `- [${issue.severity}] ${issue.file}${issue.line ? `:${issue.line}` : ""} — ${redact(issue.description)}\n`;
          }
          // 判断理由（サイクルあたり1回）
          md += `\n**判断**: ${redact(record.judgmentSummary)}\n`;
          // diff（サイクルあたり1回）
          if (record.diffAfter) {
            const snippet = redact(record.diffAfter.split("\n").slice(0, 30).join("\n"));
            if (snippet.trim()) {
              md += `\n<details><summary>修正 diff</summary>\n\n\`\`\`diff\n${snippet}\n\`\`\`\n</details>\n`;
            }
          }
          md += `\n`;
        } else if (record.decision === "escalated") {
          md += `**エスカレーション**: ${record.judgmentSummary}\n\n`;
        }
      }
    }

    // 設計判断セクション（事前定義 vs レビュー中の許容を分離）
    const designDecisionRecords = acceptedRecords.filter((r) => r.step === "design_decision");
    const reviewAcceptedRecords = acceptedRecords.filter((r) => r.step !== "design_decision");

    if (designDecisionRecords.length > 0) {
      md += `---\n\n## 事前定義の設計判断\n\n`;
      for (const record of designDecisionRecords) {
        md += `- ${redact(record.judgmentSummary)}\n`;
      }
      md += `\n`;
    }

    if (reviewAcceptedRecords.length > 0) {
      md += `---\n\n## レビュー中に許容した指摘\n\n`;
      for (const record of reviewAcceptedRecords) {
        for (const issue of record.findings) {
          md += `#### ${redact(issue.description)}（${issue.severity}）\n`;
          md += `- **ファイル**: ${issue.file}${issue.line ? `:${issue.line}` : ""}\n`;
          md += `- **判断**: 許容\n`;
          md += `- **理由**: ${redact(record.judgmentSummary)}\n\n`;
        }
      }
    }

    // サマリー
    md += `---\n\n## サマリー\n\n`;
    md += `| 指標 | 値 |\n|---|---|\n`;
    md += `| レビューステップ数 | ${reviewSteps} |\n`;
    md += `| レビューサイクル総数 | ${totalCycles}回（修正による再実行を含む） |\n`;
    md += `| 修正した指摘数 | ${fixCount}件 |\n`;
    md += `| 通過ステップ数 | ${lgtmRecords.length}件 |\n`;
    md += `| 事前定義の設計判断 | ${designDecisionRecords.length}件 |\n`;
    md += `| レビュー中に許容 | ${reviewAcceptedRecords.length}件 |\n`;
    md += `| LLM実行回数 | ${usageSummary.total.runs}件 |\n`;
    md += `| Input Tokens | ${usageSummary.total.inputTokens} |\n`;
    md += `| Output Tokens | ${usageSummary.total.outputTokens} |\n`;
    md += `| Cost USD | ${usageSummary.total.costUsd.toFixed(4)} |\n`;

    const usageSteps = Object.entries(usageSummary.byStep);
    if (usageSteps.length > 0) {
      md += `\n### LLM Usage By Step\n\n`;
      md += `| Step | Runs | Input | Output | Cost USD |\n|---|---:|---:|---:|---:|\n`;
      for (const [step, totals] of usageSteps) {
        md += `| ${step} | ${totals.runs} | ${totals.inputTokens} | ${totals.outputTokens} | ${totals.costUsd.toFixed(4)} |\n`;
      }
    }

    // 書き出し
    const reportsDir = join(root, "docs/reviews");
    mkdirSync(reportsDir, { recursive: true });
    const reportPath = join(reportsDir, `${timestamp}_${scopeSlug}.md`);
    writeFileSync(reportPath, md, "utf-8");
    console.log(`レポート生成: ${reportPath}`);
  }
}
