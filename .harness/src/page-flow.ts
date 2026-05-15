import { existsSync, readFileSync } from "node:fs";
import { join, resolve } from "node:path";
import { stringify as stringifyYaml } from "yaml";
import { TestExecutor } from "./application/test-executor.ts";
import { HarnessLogger } from "./logger.ts";
import { LintGuard } from "./lint-guard.ts";
import { ReviewOrchestrator } from "./review-orchestrator.ts";
import type { Boundary } from "./boundary.ts";
import type { RunnerRegistry } from "./runner-registry.ts";
import { FLOW_STEP } from "./steps.ts";
import type { TaskPlan, BrowserVerificationResult, ReviewIssue, BrowserScenarioResult } from "./types.ts";
import { DriftError, GuardError, HarnessError, ESCALATION_LEVEL } from "./types.ts";
import type { ResolvedProfileConfig } from "./config.ts";
import { assertReadyLikeStatus } from "./domain/plan-readiness.ts";
import { resolveReviewCriteriaPaths } from "./domain/review-assets.ts";
import type { LintAdapter, TestAdapter } from "./tool-adapter.ts";
import { loadTemplate, renderTemplate } from "./templates.ts";
import { parsePlan } from "./plan-parser.ts";
import { applyStepContext } from "./step-context.ts";

const DEFAULT_TIMEOUT_MS = 10 * 60 * 1000;
const MAX_BROWSER_ATTEMPTS = 2;

export class PageFlow {
  private boundary: Boundary;
  private registry: RunnerRegistry;
  private profile: ResolvedProfileConfig;
  private testAdapter: TestAdapter;
  private lintAdapters: LintAdapter[];
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
    this.testExecutor = new TestExecutor(testAdapter, {
      projectRoot: this.boundary.getProjectRoot(),
      toolRoot: this.profile.toolRoot,
      execOverride: this.profile.exec,
      genericFailureMessage: `${testAdapter.frameworkName} がページフロー中に失敗しました。`,
    });
  }

  async run(planPath: string, options?: { plan?: TaskPlan }): Promise<void> {
    const plan = options?.plan ?? parsePlan(this.boundary.getProjectRoot(), planPath);
    this.validatePagePlan(plan);

    const root = this.boundary.getProjectRoot();
    const logger = new HarnessLogger(`page_${plan.scope.replace(/\//g, "_")}`, { baseDir: join(root, "logs") });
    const lintGuard = new LintGuard(logger, this.lintAdapters, {
      toolRoot: this.profile.toolRoot,
      execOverride: this.profile.exec,
    });
    const reviewOrchestrator = new ReviewOrchestrator(logger, lintGuard, root, this.registry, this.profile);
    const criteriaPaths = this.resolveCriteriaPaths();
    const scopeTools = this.boundary.scopeAllowedTools(plan.scope);
    const implFilesRescan = () => this.boundary.findImplementationFiles(plan.scope);

    console.log("ページ実装を生成中...");
    await this.generatePage(plan, scopeTools);
    await this.boundary.stageFiles(plan.scope);
    await this.runStaticChecks(lintGuard, plan, scopeTools);
    await this.boundary.verifyChangedFilesWithinScope(plan.scope);

    console.log("ページレビュー実行中...");
    await reviewOrchestrator.runPageReview({
      targetFiles: await implFilesRescan(),
      specPath: resolve(root, plan.specPath),
      criteriaPaths,
      runTests: async () => {
        const result = await this.runTests(this.boundary.testPathForScope(plan.scope));
        if (!result.passed) {
          throw new HarnessError(`ページテスト失敗: ${result.output}`);
        }
      },
      rescanFiles: implFilesRescan,
      scopeAllowedTools: this.boundary.implAllowedTools(plan.scope),
      getFileDiff: (files: string[]) => this.boundary.getFileDiff(files),
      designDecisions: plan.designDecisions,
      reviewMode: "implementation",
      testCasesPath: resolve(root, plan.testCasesPath),
      componentSpecPath: resolve(root, plan.componentSpecPath ?? ""),
      figmaSlice: plan.figmaSlice ?? "",
      dependenciesText: stringifyYaml(
        plan.dependencies.map((dependency) => ({
          name: dependency.name,
          import: dependency.importPath,
        })),
      ),
      browserScenariosText: stringifyYaml(plan.browserScenarios),
    });
    await this.boundary.verifyChangedFilesWithinScope(plan.scope);

    for (let attempt = 1; attempt <= MAX_BROWSER_ATTEMPTS; attempt++) {
      console.log(`ブラウザ検証中... (試行 ${attempt}/${MAX_BROWSER_ATTEMPTS})`);
      const pageFiles = await implFilesRescan();
      const browserResult = await this.runBrowserVerification(plan, pageFiles);
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

      const browserIssues = this.browserIssuesFromResult(browserResult);
      console.log("ブラウザ検証で指摘が出たため修正し、レビューに戻ります...");
      await this.applyBrowserFixes(browserIssues, scopeTools);
      await this.runStaticChecks(lintGuard, plan, scopeTools);
      await this.boundary.verifyChangedFilesWithinScope(plan.scope);
      await reviewOrchestrator.runPageReview({
        targetFiles: await implFilesRescan(),
        specPath: resolve(root, plan.specPath),
        criteriaPaths,
        runTests: async () => {
          const result = await this.runTests(this.boundary.testPathForScope(plan.scope));
          if (!result.passed) {
            throw new HarnessError(`ページテスト失敗: ${result.output}`);
          }
        },
        rescanFiles: implFilesRescan,
        scopeAllowedTools: this.boundary.implAllowedTools(plan.scope),
        getFileDiff: (files: string[]) => this.boundary.getFileDiff(files),
        designDecisions: plan.designDecisions,
        reviewMode: "implementation",
        testCasesPath: resolve(root, plan.testCasesPath),
        componentSpecPath: resolve(root, plan.componentSpecPath ?? ""),
        figmaSlice: plan.figmaSlice ?? "",
        dependenciesText: stringifyYaml(
          plan.dependencies.map((dependency) => ({
            name: dependency.name,
            import: dependency.importPath,
          })),
        ),
        browserScenariosText: stringifyYaml(plan.browserScenarios),
      });
      await this.boundary.verifyChangedFilesWithinScope(plan.scope);
    }
  }

  private validatePagePlan(plan: TaskPlan): void {
    if (plan.type !== "page") {
      throw new GuardError(`page コマンドには type: page の plan が必要です。現在: ${plan.type ?? "未指定"}`);
    }
    if (!plan.profile) {
      throw new GuardError("page plan には profile が必要です。");
    }
    if (!plan.scope) {
      throw new GuardError("page plan には scope が必要です。");
    }
    if (!plan.specPath) {
      throw new GuardError("page plan には spec が必要です。");
    }
    if (!plan.testCasesPath) {
      throw new GuardError("page plan には test_cases が必要です。");
    }
    if (!plan.componentSpecPath) {
      throw new GuardError("page plan には component_spec が必要です。");
    }
    if (!plan.figmaCachePath) {
      throw new GuardError("page plan には figma_cache が必要です。");
    }
    if (plan.msw === undefined) {
      throw new GuardError("page plan には msw が必要です。");
    }
    if (plan.dependencies.length === 0) {
      throw new GuardError("page plan には Dependencies セクションが必要です。");
    }
    if (!plan.figmaSlice || plan.figmaSlice.trim() === "") {
      throw new GuardError("page plan には Figma Slice セクションが必要です。");
    }
    if (plan.browserScenarios.length === 0) {
      throw new GuardError("page plan には Browser Scenarios セクションが必要です。");
    }
    if (plan.targetTestCases.length === 0) {
      throw new GuardError("page plan には 対象テストケース セクションが必要です。");
    }
    if (plan.completionCriteria.length === 0) {
      throw new GuardError("page plan には 完了条件 セクションが必要です。");
    }

    this.boundary.validateScope(plan.scope);

    const root = this.boundary.getProjectRoot();
    const requiredPaths = [
      resolve(root, plan.specPath),
      resolve(root, plan.testCasesPath),
      resolve(root, plan.componentSpecPath),
      resolve(root, plan.figmaCachePath),
    ];
    for (const fullPath of requiredPaths) {
      this.boundary.assertWithinProject(fullPath);
      if (!existsSync(fullPath)) {
        throw new GuardError(`page plan の参照ファイルが存在しません: ${fullPath}`);
      }
    }

    assertReadyLikeStatus(this.boundary.readFrontmatter(resolve(root, plan.specPath)).status, "仕様書");
    assertReadyLikeStatus(
      this.boundary.readFrontmatter(resolve(root, plan.testCasesPath)).status,
      "テストケース",
    );
    assertReadyLikeStatus(
      this.boundary.readFrontmatter(resolve(root, plan.componentSpecPath)).status,
      "コンポーネント定義書",
    );
  }

  private resolveCriteriaPaths(): string[] {
    return resolveReviewCriteriaPaths(
      this.boundary.getProjectRoot(),
      this.profile,
      "frontend",
    );
  }

  private async generatePage(plan: TaskPlan, scopeTools: string[]): Promise<void> {
    const root = this.boundary.getProjectRoot();
    const spec = readFileSync(resolve(root, plan.specPath), "utf-8");
    const componentSpec = readFileSync(resolve(root, plan.componentSpecPath ?? ""), "utf-8");
    const figmaSlice = plan.figmaSlice ?? "";
    const dependencies = stringifyYaml(
      plan.dependencies.map((dependency) => ({
        name: dependency.name,
        import: dependency.importPath,
      })),
    );
    const browserScenarios = stringifyYaml(plan.browserScenarios);

    const config = this.registry.getConfig();
    const template = loadTemplate("page-generate", root, config.templates);
    const prompt = renderTemplate(template, {
      spec,
      componentSpec,
      dependencies,
      figmaSlice,
      browserScenarios,
      targetTestCases: plan.targetTestCases.join("\n"),
    });

    const runner = this.registry.getRunner(FLOW_STEP.PAGE_GENERATE);
    await runner.run(
      applyStepContext(
        {
          prompt,
          allowedTools: scopeTools,
          cwd: root,
          timeoutMs: DEFAULT_TIMEOUT_MS,
        },
        this.registry.getConfig(),
        this.profile,
        FLOW_STEP.PAGE_GENERATE,
        root,
        runner.name,
      ),
      undefined,
    );
  }

  private async runStaticChecks(
    lintGuard: LintGuard,
    plan: TaskPlan,
    scopeTools: string[],
  ): Promise<void> {
    console.log("静的チェック実行中...");
    const sourceFiles = await this.boundary.findSourceFiles(plan.scope);
    if (sourceFiles.length > 0) {
      await lintGuard.check(sourceFiles, {
        claudeFix: async (violations) => {
          const issueList = violations
            .map((violation) => `${violation.tool}: ${violation.file}:${violation.line} - ${violation.message}`)
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
                allowedTools: scopeTools,
                cwd: this.boundary.getProjectRoot(),
              },
              this.registry.getConfig(),
              this.profile,
              FLOW_STEP.LINT_FIX,
              this.boundary.getProjectRoot(),
              runner.name,
            ),
            undefined,
          );
        },
      });
    }

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

  private async runBrowserVerification(
    plan: TaskPlan,
    targetFiles: string[],
  ): Promise<BrowserVerificationResult> {
    const root = this.boundary.getProjectRoot();
    const spec = readFileSync(resolve(root, plan.specPath), "utf-8");
    const config = this.registry.getConfig();
    const template = loadTemplate("review-page-browser", root, config.templates);
    const prompt = renderTemplate(template, {
      spec,
      browserScenarios: stringifyYaml(plan.browserScenarios),
      fileContents: this.readFiles(targetFiles),
    });

    const runner = this.registry.getRunner(FLOW_STEP.PAGE_BROWSER_VERIFY);
    const response = await runner.run(
      applyStepContext(
        {
          prompt,
          cwd: root,
          timeoutMs: DEFAULT_TIMEOUT_MS,
        },
        this.registry.getConfig(),
        this.profile,
        FLOW_STEP.PAGE_BROWSER_VERIFY,
        root,
        runner.name,
      ),
      undefined,
    );

    return this.parseBrowserVerificationResult(response.text);
  }

  private parseBrowserVerificationResult(output: string): BrowserVerificationResult {
    const cleaned = output.replace(/```(?:json)?\s*\n([\s\S]*?)```/g, "$1");
    const jsonMatch = /\{[\s\S]*"overall"\s*:\s*"[^"]+"[\s\S]*"scenarios"\s*:\s*\[[\s\S]*\][\s\S]*\}/.exec(cleaned);
    const raw = jsonMatch?.[0] ?? cleaned;

    let parsed: unknown;
    try {
      parsed = JSON.parse(raw);
    } catch {
      throw new HarnessError("Browser Verification の出力が不正な JSON です。");
    }

    if (typeof parsed !== "object" || parsed === null || Array.isArray(parsed)) {
      throw new HarnessError("Browser Verification の出力形式が不正です。");
    }
    const record = parsed as Record<string, unknown>;
    if (record.overall !== "pass" && record.overall !== "fail" && record.overall !== "blocked") {
      throw new HarnessError("Browser Verification の overall は pass/fail/blocked のいずれかである必要があります。");
    }
    if (!Array.isArray(record.scenarios)) {
      throw new HarnessError("Browser Verification の scenarios は配列である必要があります。");
    }

    const scenarios = record.scenarios.map((item, index) => this.parseBrowserScenarioResult(item, index));
    return {
      overall: record.overall,
      scenarios,
    } satisfies BrowserVerificationResult;
  }

  private parseBrowserScenarioResult(item: unknown, index: number): BrowserScenarioResult {
    if (typeof item !== "object" || item === null || Array.isArray(item)) {
      throw new HarnessError(`Browser Verification scenarios[${index}] の形式が不正です。`);
    }
    const record = item as Record<string, unknown>;
    const status = record.status;
    if (status !== "pass" && status !== "fail" && status !== "blocked") {
      throw new HarnessError(`Browser Verification scenarios[${index}].status は pass/fail/blocked のいずれかである必要があります。`);
    }

    return {
      name: this.requiredString(record.name, `scenarios[${index}].name`),
      status,
      completedSteps: this.optionalStringList(record.completed_steps),
      failedStep: this.optionalString(record.failed_step),
      expected: this.optionalStringList(record.expected),
      observed: this.optionalStringList(record.observed),
      notes: this.optionalString(record.notes),
    };
  }

  private browserIssuesFromResult(result: BrowserVerificationResult): ReviewIssue[] {
    const issues = result.scenarios
      .filter((scenario) => scenario.status !== "pass")
      .map((scenario) => {
        const expected = scenario.expected?.join(" / ") ?? "期待結果不明";
        const observed = scenario.observed?.join(" / ") ?? "観測結果不明";
        const failureDetail = scenario.failedStep ? `失敗ステップ: ${scenario.failedStep}` : "失敗ステップ不明";
        return {
          description: `Browser Verification 失敗: ${scenario.name}. ${failureDetail}. expected=${expected}. observed=${observed}. ${scenario.notes ?? ""}`.trim(),
          severity: scenario.status === "blocked" ? "critical" : "major",
          file: "",
        } satisfies ReviewIssue;
      });
    if (issues.length === 0 && result.overall !== "pass") {
      issues.push({
        description: `Browser Verification 全体が ${result.overall} で終了しました。scenario 単位の詳細が返っていません。`,
        severity: "critical",
        file: "",
      });
    }
    return issues;
  }

  private async applyBrowserFixes(
    issues: ReviewIssue[],
    scopeTools: string[],
  ): Promise<void> {
    const issueList = issues
      .map((issue, index) => `${index + 1}. [${issue.severity}] ${issue.description}`)
      .join("\n");
    const prompt = `以下の Browser Verification 指摘を修正してください。

## 指摘一覧
${issueList}

## 制約
- 仕様書の UX 要件に合致するよう修正する
- ページの配線、状態遷移、レンダリング不整合の修正を優先する
- 不要なリファクタリングは行わない`;

    const runner = this.registry.getRunner(FLOW_STEP.APPLY_FIXES);
    await runner.run(
      applyStepContext(
        {
          prompt,
          allowedTools: scopeTools,
          cwd: this.boundary.getProjectRoot(),
          timeoutMs: DEFAULT_TIMEOUT_MS,
        },
        this.registry.getConfig(),
        this.profile,
        FLOW_STEP.APPLY_FIXES,
        this.boundary.getProjectRoot(),
        runner.name,
      ),
      undefined,
    );
  }

  private readFiles(files: string[]): string {
    return files
      .map((file) => {
        const content = readFileSync(file, "utf-8");
        return `### ${file}\n\`\`\`\n${content}\n\`\`\``;
      })
      .join("\n\n");
  }

  private requiredString(value: unknown, field: string): string {
    if (typeof value !== "string" || value.trim() === "") {
      throw new HarnessError(`Browser Verification の ${field} は空でない文字列である必要があります。`);
    }
    return value;
  }

  private optionalString(value: unknown): string | undefined {
    return typeof value === "string" && value.trim() !== "" ? value : undefined;
  }

  private optionalStringList(value: unknown): string[] {
    if (!Array.isArray(value)) return [];
    return value.filter((item): item is string => typeof item === "string");
  }
}
