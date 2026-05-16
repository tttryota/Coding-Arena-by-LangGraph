import { createHash } from "node:crypto";
import { existsSync, readFileSync } from "node:fs";
import { basename, join, resolve } from "node:path";
import { promisify } from "node:util";
import { execFile } from "node:child_process";
import { stringify as stringifyYaml } from "yaml";
import { HarnessLogger, DEFAULT_LOG_BASE_DIR } from "./logger.ts";
import { LintGuard } from "./lint-guard.ts";
import { ReviewOrchestrator } from "./review-orchestrator.ts";
import type { Boundary } from "./boundary.ts";
import type { RunnerRegistry } from "./runner-registry.ts";
import { FLOW_STEP } from "./steps.ts";
import type { ResolvedProfileConfig, StorybookConfig } from "./config.ts";
import type { LintAdapter } from "./tool-adapter.ts";
import type { ReviewIssue, ReviewResult, TaskPlan } from "./types.ts";
import { GuardError, EVENT } from "./types.ts";
import { loadTemplate, renderTemplate } from "./templates.ts";
import { parsePlan } from "./plan-parser.ts";
import { applyClaudeStepContext } from "./claude-context.ts";

const DEFAULT_TIMEOUT_MS = 10 * 60 * 1000;
const MAX_COMPONENT_FIX_RETRIES = 2;
const STORYBOOK_TIMEOUT_MS = 5 * 60 * 1000;
const execFileAsync = promisify(execFile);

type TargetOutcome = {
  target: string;
  resolved: boolean;
  fixAttempts: number;
  changedFiles: string[];
  unresolvedIssues: ReviewIssue[];
};

export class ComponentFlow {
  private boundary: Boundary;
  private registry: RunnerRegistry;
  private profile: ResolvedProfileConfig;
  private lintAdapters: LintAdapter[];

  constructor(
    boundary: Boundary,
    registry: RunnerRegistry,
    profile: ResolvedProfileConfig,
    _testAdapter: import("./tool-adapter.ts").TestAdapter,
    lintAdapters: LintAdapter[],
  ) {
    this.boundary = boundary;
    this.registry = registry;
    this.profile = profile;
    this.lintAdapters = lintAdapters;
  }

  async run(planPath: string, options?: { plan?: TaskPlan }): Promise<void> {
    const plan = options?.plan ?? parsePlan(this.boundary.getProjectRoot(), planPath);
    this.validateComponentPlan(plan);

    const root = this.boundary.getProjectRoot();
    const logger = new HarnessLogger(`component_${plan.scope.replace(/\//g, "_")}`, { baseDir: join(root, DEFAULT_LOG_BASE_DIR) });
    const lintGuard = new LintGuard(logger, this.lintAdapters, {
      toolRoot: this.profile.toolRoot,
      execOverride: this.profile.exec,
    });
    const reviewOrchestrator = new ReviewOrchestrator(logger, lintGuard, root, this.registry, this.profile);
    const criteriaPath = this.resolveComponentCriteriaPath();
    const scopeTools = this.boundary.scopeAllowedTools(plan.scope);

    const outcomes: TargetOutcome[] = [];

    for (const target of plan.targets) {
      console.log(`コンポーネントを処理中: ${target}`);
      logger.log(EVENT.REVIEW_START, { mode: "component_target", target });
      const beforeSnapshot = await this.snapshotScopeFiles(plan.scope);

      await this.generateTarget(plan, target, scopeTools);
      await this.boundary.stageFiles(plan.scope);
      await this.boundary.verifyChangedFilesWithinScope(plan.scope);

      const outcome = await this.processTarget(
        plan,
        target,
        beforeSnapshot,
        lintGuard,
        reviewOrchestrator,
        criteriaPath,
        scopeTools,
      );
      outcomes.push(outcome);
    }

    logger.saveReviewData({ plan, targets: outcomes });
    const unresolvedCount = outcomes.filter((outcome) => !outcome.resolved).length;
    console.log(`未収束 target: ${unresolvedCount}`);
  }

  private validateComponentPlan(plan: TaskPlan): void {
    if (plan.type !== "component") {
      throw new GuardError(`component コマンドには type: component の plan が必要です。現在: ${plan.type ?? "未指定"}`);
    }
    if (!plan.profile) {
      throw new GuardError("component plan には profile が必要です。");
    }
    if (!plan.scope) {
      throw new GuardError("component plan には scope が必要です。");
    }
    if (!plan.specPath) {
      throw new GuardError("component plan には spec が必要です。");
    }
    if (!plan.componentSpecPath) {
      throw new GuardError("component plan には component_spec が必要です。");
    }
    if (!plan.figmaCachePath) {
      throw new GuardError("component plan には figma_cache が必要です。");
    }
    if (plan.targets.length === 0) {
      throw new GuardError("component plan には Targets セクションが必要です。");
    }
    if (plan.dependencies.length === 0) {
      throw new GuardError("component plan には Dependencies セクションが必要です。");
    }
    if (!plan.figmaSlice || plan.figmaSlice.trim() === "") {
      throw new GuardError("component plan には Figma Slice セクションが必要です。");
    }
    if (plan.completionCriteria.length === 0) {
      throw new GuardError("component plan には 完了条件 セクションが必要です。");
    }

    this.boundary.validateScope(plan.scope);

    const root = this.boundary.getProjectRoot();
    const requiredPaths = [
      resolve(root, plan.specPath),
      resolve(root, plan.componentSpecPath),
      resolve(root, plan.figmaCachePath),
    ];
    for (const fullPath of requiredPaths) {
      this.boundary.assertWithinProject(fullPath);
      if (!existsSync(fullPath)) {
        throw new GuardError(`component plan の参照ファイルが存在しません: ${fullPath}`);
      }
    }

    const specStatus = this.boundary.readFrontmatter(resolve(root, plan.specPath)).status;
    if (!this.isReadyLikeStatus(specStatus)) {
      throw new GuardError(`仕様書が ready ではありません（現在: ${specStatus ?? "なし"}）`);
    }
    const componentSpecStatus = this.boundary.readFrontmatter(resolve(root, plan.componentSpecPath)).status;
    if (!this.isReadyLikeStatus(componentSpecStatus)) {
      throw new GuardError(`コンポーネント定義書が ready ではありません（現在: ${componentSpecStatus ?? "なし"}）`);
    }

    if (!this.profile.storybook) {
      throw new GuardError("component フローには profile.storybook.renderCommand / smokeCommand の設定が必要です。");
    }
  }

  private isReadyLikeStatus(status: string | undefined): boolean {
    return status === "ready" || status === "approved";
  }

  private resolveComponentCriteriaPath(): string {
    const root = this.boundary.getProjectRoot();
    const projectPath = join(root, ".harness", "review-criteria-component.md");
    if (existsSync(projectPath)) return projectPath;

    const packagePath = join(import.meta.dirname ?? "", "..", "review-criteria-component.md");
    if (existsSync(packagePath)) return packagePath;

    throw new GuardError("review-criteria-component.md が見つかりません。");
  }

  private async generateTarget(
    plan: TaskPlan,
    target: string,
    scopeTools: string[],
  ): Promise<void> {
    const root = this.boundary.getProjectRoot();
    const spec = readFileSync(resolve(root, plan.specPath), "utf-8");
    const componentSpec = readFileSync(resolve(root, plan.componentSpecPath ?? ""), "utf-8");
    const template = loadTemplate("component-generate", root, this.registry.getConfig().templates);
    const prompt = renderTemplate(template, {
      target,
      spec,
      componentSpec,
      dependencies: stringifyYaml(
        plan.dependencies.map((dependency) => ({
          name: dependency.name,
          import: dependency.importPath,
        })),
      ),
      figmaSlice: plan.figmaSlice ?? "",
      designDecisions: plan.designDecisions.join("\n"),
    });

    const runner = this.registry.getRunner(FLOW_STEP.COMPONENT_GENERATE);
    await runner.run(
      applyClaudeStepContext(
        {
          prompt,
          allowedTools: scopeTools,
          cwd: root,
          timeoutMs: DEFAULT_TIMEOUT_MS,
        },
        this.registry.getConfig(),
        this.profile,
        FLOW_STEP.COMPONENT_GENERATE,
        root,
      ),
      undefined,
    );
  }

  private async processTarget(
    plan: TaskPlan,
    target: string,
    beforeSnapshot: Map<string, string>,
    lintGuard: LintGuard,
    reviewOrchestrator: ReviewOrchestrator,
    criteriaPath: string,
    scopeTools: string[],
  ): Promise<TargetOutcome> {
    let fixAttempts = 0;
    let changedFiles = await this.collectChangedFilesSince(plan.scope, beforeSnapshot);
    let lastIssues: ReviewIssue[] = [];

    for (;;) {
      changedFiles = await this.collectChangedFilesSince(plan.scope, beforeSnapshot);
      lastIssues = await this.runTargetChecks(
        target,
        changedFiles,
        lintGuard,
        reviewOrchestrator,
        criteriaPath,
      );

      if (lastIssues.length === 0) {
        return {
          target,
          resolved: true,
          fixAttempts,
          changedFiles,
          unresolvedIssues: [],
        };
      }

      if (fixAttempts >= MAX_COMPONENT_FIX_RETRIES) {
        return {
          target,
          resolved: false,
          fixAttempts,
          changedFiles,
          unresolvedIssues: lastIssues,
        };
      }

      fixAttempts++;
      console.log(`指摘を修正中... (${target} ${fixAttempts}/${MAX_COMPONENT_FIX_RETRIES})`);
      await this.applyFixes(target, lastIssues, scopeTools);
      await this.boundary.stageFiles(plan.scope);
      await this.boundary.verifyChangedFilesWithinScope(plan.scope);
    }
  }

  private async runTargetChecks(
    target: string,
    changedFiles: string[],
    lintGuard: LintGuard,
    reviewOrchestrator: ReviewOrchestrator,
    criteriaPath: string,
  ): Promise<ReviewIssue[]> {
    if (changedFiles.length === 0) {
      return [{
        file: "",
        severity: "critical",
        description: `target "${target}" の生成後に変更ファイルが検出されませんでした。`,
      }];
    }

    const issues: ReviewIssue[] = [];

    try {
      await lintGuard.check(changedFiles);
    } catch (error: unknown) {
      issues.push(this.errorToIssue(error, changedFiles[0], `target "${target}" の静的チェックに失敗しました`));
    }

    const storyIssues = await this.runStoryGates(target, changedFiles);
    issues.push(...storyIssues);

    const reviewResult = await reviewOrchestrator.runComponentReview(changedFiles, [criteriaPath]);
    issues.push(...this.scopeReviewIssues(reviewResult, changedFiles));

    return issues;
  }

  private scopeReviewIssues(result: ReviewResult, changedFiles: string[]): ReviewIssue[] {
    const allowed = new Set(changedFiles.map((file) => resolve(file)));
    return result.issues.filter((issue) => {
      if (!issue.file) return true;
      return allowed.has(resolve(issue.file));
    });
  }

  private async runStoryGates(target: string, changedFiles: string[]): Promise<ReviewIssue[]> {
    const storyFiles = this.findStoryFilesForTarget(target, changedFiles);
    if (storyFiles.length === 0) {
      return [{
        file: changedFiles[0] ?? "",
        severity: "major",
        description: `target "${target}" の Story ファイルが見つかりません。${target}.stories.tsx を生成してください。`,
      }];
    }

    const storyFile = storyFiles[0];
    const issues: ReviewIssue[] = [];
    const renderIssues = await this.runStorybookCommand("render", target, storyFile, this.profile.storybook!);
    issues.push(...renderIssues);
    if (renderIssues.length === 0) {
      const smokeIssues = await this.runStorybookCommand("smoke", target, storyFile, this.profile.storybook!);
      issues.push(...smokeIssues);
    }
    return issues;
  }

  private async runStorybookCommand(
    mode: "render" | "smoke",
    target: string,
    storyFile: string,
    storybook: StorybookConfig,
  ): Promise<ReviewIssue[]> {
    const commandTemplate = mode === "render" ? storybook.renderCommand : storybook.smokeCommand;
    const command = commandTemplate.map((part) => this.expandStorybookArg(part, target, storyFile));
    const [tool, ...args] = command;

    try {
      const { stdout, stderr } = await execFileAsync(tool, args, {
        cwd: this.profile.toolRoot,
        timeout: STORYBOOK_TIMEOUT_MS,
      });
      const output = `${stdout}${stderr}`.trim();
      if (output) {
        // no-op; command output remains in process logs only
      }
      return [];
    } catch (error: unknown) {
      const execError = error as { stdout?: string; stderr?: string; code?: string | number; message?: string };
      const output = `${execError.stdout ?? ""}${execError.stderr ?? ""}`.trim();
      return [{
        file: storyFile,
        severity: "major",
        description: `Storybook ${mode} command が失敗しました。command=${command.join(" ")}. output=${(output || execError.message || "").slice(0, 1200)}`,
      }];
    }
  }

  private expandStorybookArg(arg: string, target: string, storyFile: string): string {
    return arg
      .replaceAll("{{target}}", target)
      .replaceAll("{{storyFile}}", storyFile)
      .replaceAll("{{toolRoot}}", this.profile.toolRoot);
  }

  private async applyFixes(target: string, issues: ReviewIssue[], scopeTools: string[]): Promise<void> {
    const issueList = issues
      .map((issue, index) => `${index + 1}. [${issue.severity}] ${issue.file}:${issue.line ?? "?"} - ${issue.description}`)
      .join("\n");
    const prompt = `target "${target}" の component と Story を修正してください。

## 指摘一覧
${issueList}

## 制約
- プレゼンテーション責務のみを扱う
- API、server state、atom/global state、ビジネスロジックを追加しない
- Story は props ベースで状態再現する
- Story は CSF3 形式を維持する
- 指摘の解消に必要な範囲だけ修正する`;

    const runner = this.registry.getRunner(FLOW_STEP.APPLY_FIXES);
    await runner.run(
      applyClaudeStepContext(
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
      ),
      undefined,
    );
  }

  private async snapshotScopeFiles(scope: string): Promise<Map<string, string>> {
    const files = await this.boundary.findImplementationFiles(scope);
    const snapshot = new Map<string, string>();
    for (const file of files) {
      snapshot.set(file, this.fileHash(file));
    }
    return snapshot;
  }

  private async collectChangedFilesSince(
    scope: string,
    beforeSnapshot: Map<string, string>,
  ): Promise<string[]> {
    const files = await this.boundary.findImplementationFiles(scope);
    const changed: string[] = [];
    for (const file of files) {
      const hash = this.fileHash(file);
      const previous = beforeSnapshot.get(file);
      if (!previous || previous !== hash) {
        changed.push(file);
      }
    }
    return changed;
  }

  private fileHash(file: string): string {
    return createHash("sha1").update(readFileSync(file)).digest("hex");
  }

  private findStoryFilesForTarget(target: string, changedFiles: string[]): string[] {
    return changedFiles.filter((file) => {
      const name = basename(file);
      return name === `${target}.stories.tsx`
        || name === `${target}.stories.ts`
        || name === `${target}.stories.jsx`
        || name === `${target}.stories.js`;
    });
  }

  private errorToIssue(error: unknown, file: string, prefix: string): ReviewIssue {
    const message = error instanceof Error ? error.message : String(error);
    return {
      file,
      severity: "critical",
      description: `${prefix}: ${message}`,
    };
  }
}
