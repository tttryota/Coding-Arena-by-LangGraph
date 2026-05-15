import { execFile } from "node:child_process";
import { createHash } from "node:crypto";
import { basename, resolve } from "node:path";
import { readFileSync } from "node:fs";
import { promisify } from "node:util";
import type { Boundary } from "../boundary.ts";
import type { RunnerRegistry } from "../runner-registry.ts";
import type { ResolvedProfileConfig, StorybookConfig } from "../config.ts";
import { applyStepContext } from "../step-context.ts";
import { FLOW_STEP } from "../steps.ts";
import { type ReviewIssue, type ReviewResult, type TaskPlan } from "../types.ts";
import type { LintGuard } from "../lint-guard.ts";
import type { ReviewOrchestrator } from "../review-orchestrator.ts";

const DEFAULT_TIMEOUT_MS = 10 * 60 * 1000;
const MAX_COMPONENT_FIX_RETRIES = 2;
const STORYBOOK_TIMEOUT_MS = 5 * 60 * 1000;
const execFileAsync = promisify(execFile);

export type TargetOutcome = {
  target: string;
  resolved: boolean;
  fixAttempts: number;
  changedFiles: string[];
  unresolvedIssues: ReviewIssue[];
};

export class ComponentTargetService {
  private boundary: Boundary;
  private registry: RunnerRegistry;
  private profile: ResolvedProfileConfig;

  constructor(
    boundary: Boundary,
    registry: RunnerRegistry,
    profile: ResolvedProfileConfig,
  ) {
    this.boundary = boundary;
    this.registry = registry;
    this.profile = profile;
  }

  async processTarget(
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

  async snapshotScopeFiles(scope: string): Promise<Map<string, string>> {
    const files = await this.boundary.findImplementationFiles(scope);
    const snapshot = new Map<string, string>();
    for (const file of files) {
      snapshot.set(file, this.fileHash(file));
    }
    return snapshot;
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

    issues.push(...await this.runStoryGates(target, changedFiles));
    const reviewResult = await reviewOrchestrator.runComponentReview(changedFiles, [criteriaPath]);
    issues.push(...this.scopeReviewIssues(reviewResult, changedFiles));
    return issues;
  }

  private scopeReviewIssues(result: ReviewResult, changedFiles: string[]): ReviewIssue[] {
    const allowed = new Set(changedFiles.map((file) => resolve(file)));
    return result.issues.filter((issue) => !issue.file || allowed.has(resolve(issue.file)));
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
      issues.push(...await this.runStorybookCommand("smoke", target, storyFile, this.profile.storybook!));
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
      await execFileAsync(tool, args, {
        cwd: this.profile.toolRoot,
        timeout: STORYBOOK_TIMEOUT_MS,
      });
      return [];
    } catch (error: unknown) {
      const execError = error as { stdout?: string; stderr?: string; message?: string };
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
